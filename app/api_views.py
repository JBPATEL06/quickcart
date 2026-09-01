import json
import csv
from decimal import Decimal
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from django.core.paginator import Paginator

from .models import (
    User, Address, Category, Product, ProductImage, ProductSpecification,
    ComparisonAttribute, Seller, SellerDocument, SellerInventory,
    Review, ReviewFlag, PriceHistory, PricePrediction, PriceDropAlert,
    Coupon, Cart, CartItem, Order, OrderItem, OrderTrackingEvent,
    AssistantConversation, AssistantMessage, UserActivityLog,
    RecommendationSettings, RecommendationExclusion, VoiceSearchLog,
    QRShare, Notification, NotificationTemplate, HomepageBanner,
    AdminRole, AdminAuditLog
)
from .ai_services import (
    classify_review_content, predict_product_price_trend,
    parse_shopping_intent_and_rank, get_nearby_sellers_for_product,
    send_notification, log_user_activity, get_personalized_recommendations
)

# Helper: JSON Response Envelope
def api_response(data=None, error=None, status=200, **kwargs):
    payload = {
        'success': error is None,
        'data': data,
        'error': error,
    }
    payload.update(kwargs)
    return JsonResponse(payload, status=status, safe=False)


def get_or_set_session_id(request):
    session_id = request.headers.get('X-Session-ID') or request.COOKIES.get('qc_session_id')
    if not session_id:
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
    return session_id


# =======================================================
# MODULE 1: AUTH & SESSIONS
# =======================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_signup(request):
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        phone = data.get('phone', '')

        if not email or not password:
            return api_response(error={'code': 'VALIDATION_ERROR', 'message': 'Email and password are required.'}, status=400)

        if User.objects.filter(email=email).exists():
            return api_response(error={'code': 'USER_EXISTS', 'message': 'Account with this email already exists.'}, status=400)

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )
        login(request, user)

        # Merge Guest Session
        session_id = get_or_set_session_id(request)
        Cart.objects.filter(session_key=session_id).update(user=user)
        UserActivityLog.objects.filter(session_id=session_id).update(user=user)

        return api_response(data={
            'user_id': user.id,
            'email': user.email,
            'name': user.display_name,
            'role': user.role
        }, status=201)
    except Exception as e:
        return api_response(error={'code': 'SERVER_ERROR', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        user = authenticate(request, username=email, password=password)
        if not user:
            return api_response(error={'code': 'INVALID_CREDENTIALS', 'message': 'Invalid email or password.'}, status=401)

        login(request, user)

        # Merge Guest Cart
        session_id = get_or_set_session_id(request)
        guest_cart = Cart.objects.filter(session_key=session_id).first()
        if guest_cart:
            user_cart, _ = Cart.objects.get_or_create(user=user)
            for item in guest_cart.items.all():
                citem, created = CartItem.objects.get_or_create(cart=user_cart, product=item.product)
                if not created:
                    citem.quantity += item.quantity
                    citem.save()
            guest_cart.delete()

        return api_response(data={
            'user_id': user.id,
            'email': user.email,
            'name': user.display_name,
            'role': user.role,
            'is_two_factor_enabled': user.is_two_factor_enabled
        })
    except Exception as e:
        return api_response(error={'code': 'SERVER_ERROR', 'message': str(e)}, status=500)


@require_http_methods(["GET"])
def api_guest_session(request):
    session_id = get_or_set_session_id(request)
    cart, _ = Cart.objects.get_or_create(session_key=session_id)
    return api_response(data={
        'session_id': session_id,
        'cart_item_count': cart.total_items,
        'authenticated': request.user.is_authenticated
    })


@require_http_methods(["GET"])
def api_current_user(request):
    if not request.user.is_authenticated:
        return api_response(error={'code': 'UNAUTHORIZED', 'message': 'Authentication required.'}, status=401)

    u = request.user
    return api_response(data={
        'id': u.id,
        'email': u.email,
        'name': u.display_name,
        'initials': u.initials,
        'phone': u.phone,
        'role': u.role,
        'theme_mode': u.theme_mode,
        'is_two_factor_enabled': u.is_two_factor_enabled
    })


# =======================================================
# MODULE 2: CATALOG & COMPARISON
# =======================================================

@require_http_methods(["GET"])
def api_list_products(request):
    q = request.GET.get('q', '').strip()
    cat_slug = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'trending')
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 12))

    queryset = Product.objects.filter(is_published=True).select_related('category')

    if q:
        queryset = queryset.filter(Q(name__icontains=q) | Q(brand__icontains=q) | Q(description__icontains=q))
        log_user_activity(get_or_set_session_id(request), request.user, 'search', search_query=q)

    if cat_slug and cat_slug != 'all':
        queryset = queryset.filter(category__slug=cat_slug)

    if min_price:
        queryset = queryset.filter(price__gte=float(min_price))
    if max_price:
        queryset = queryset.filter(price__lte=float(max_price))

    if sort_by == 'price_low':
        queryset = queryset.order_by('price')
    elif sort_by == 'price_high':
        queryset = queryset.order_by('-price')
    elif sort_by == 'rating':
        queryset = queryset.order_by('-rating')
    elif sort_by == 'trust':
        queryset = queryset.order_by('-trust_score')
    else:
        queryset = queryset.order_by('-is_trending', '-created_at')

    paginator = Paginator(queryset, limit)
    current_page = paginator.get_page(page)

    data = [{
        'id': p.id,
        'name': p.name,
        'slug': p.slug,
        'brand': p.brand,
        'category': p.category.name,
        'category_slug': p.category.slug,
        'price': str(p.price),
        'original_price': str(p.original_price) if p.original_price else None,
        'discount_percent': p.discount_percent,
        'trust_score': p.trust_score,
        'trust_badge_label': p.trust_badge_label,
        'rating': str(p.rating),
        'review_count': p.review_count,
        'stock': p.stock,
        'main_image': p.main_image
    } for p in current_page]

    return api_response(data=data, total=paginator.count, page=page, limit=limit, total_pages=paginator.num_pages)


@require_http_methods(["GET"])
def api_product_detail(request, slug_or_id):
    if slug_or_id.isdigit():
        product = get_object_or_404(Product, id=int(slug_or_id))
    else:
        product = get_object_or_404(Product, slug=slug_or_id)

    log_user_activity(get_or_set_session_id(request), request.user, 'view', product=product)

    # Get or compute price prediction
    prediction = getattr(product, 'price_prediction', None)
    if not prediction:
        prediction = predict_product_price_trend(product)

    specs = list(product.specs.values('spec_key', 'spec_value'))
    images = list(product.images.values('image_url', 'alt_text'))

    return api_response(data={
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'brand': product.brand,
        'tagline': product.tagline,
        'description': product.description,
        'price': str(product.price),
        'original_price': str(product.original_price) if product.original_price else None,
        'discount_percent': product.discount_percent,
        'trust_score': product.trust_score,
        'trust_badge_label': product.trust_badge_label,
        'stock': product.stock,
        'rating': str(product.rating),
        'review_count': product.review_count,
        'main_image': product.main_image,
        'additional_images': images,
        'specifications': specs,
        'price_prediction': {
            'predicted_trend': prediction.predicted_trend,
            'confidence_score': prediction.confidence_score,
            'suggestion_text': prediction.suggestion_text
        }
    })


@require_http_methods(["GET"])
def api_list_categories(request):
    cats = Category.objects.filter(is_active=True).annotate(product_count=Count('products'))
    data = [{
        'id': c.id,
        'name': c.name,
        'slug': c.slug,
        'icon_name': c.icon_name,
        'description': c.description,
        'image_url': c.image_url,
        'product_count': c.product_count
    } for c in cats]
    return api_response(data=data)


# =======================================================
# MODULE 3: SELLERS & NEARBY FINDER
# =======================================================

@require_http_methods(["GET"])
def api_nearby_sellers(request):
    product_id = request.GET.get('product_id')
    lat = float(request.GET.get('lat', 28.6139))
    lng = float(request.GET.get('lng', 77.2090))
    radius = float(request.GET.get('radius_km', 100))

    if not product_id:
        return api_response(error={'code': 'MISSING_PARAM', 'message': 'product_id is required.'}, status=400)

    sellers = get_nearby_sellers_for_product(int(product_id), lat, lng, radius)
    return api_response(data=sellers, count=len(sellers))


@csrf_exempt
@require_http_methods(["POST"])
def api_seller_onboard(request):
    try:
        data = json.loads(request.body)
        seller = Seller.objects.create(
            business_name=data.get('business_name'),
            owner_name=data.get('owner_name'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            city=data.get('city'),
            postal_code=data.get('postal_code'),
            latitude=Decimal(str(data.get('latitude', 28.6139))),
            longitude=Decimal(str(data.get('longitude', 77.2090))),
            status='pending'
        )
        return api_response(data={'seller_id': seller.id, 'status': seller.status}, status=201)
    except Exception as e:
        return api_response(error={'code': 'SERVER_ERROR', 'message': str(e)}, status=500)


# =======================================================
# MODULE 4: CART, WISHLIST, CHECKOUT & ORDERS
# =======================================================

def _get_cart(request):
    session_id = get_or_set_session_id(request)
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        cart, _ = Cart.objects.get_or_create(session_key=session_id)
    return cart


@require_http_methods(["GET"])
def api_get_cart(request):
    cart = _get_cart(request)
    items = [{
        'id': i.id,
        'product_id': i.product.id,
        'name': i.product.name,
        'price': str(i.product.price),
        'quantity': i.quantity,
        'total_price': str(i.total_price),
        'image': i.product.main_image
    } for i in cart.items.all().select_related('product')]

    return api_response(data={
        'items': items,
        'total_items': cart.total_items,
        'subtotal': str(cart.subtotal),
        'promo_code': cart.promo_code,
        'discount_amount': str(cart.discount_amount),
        'shipping_fee': cart.estimated_shipping,
        'tax': str(cart.estimated_tax),
        'grand_total': str(cart.grand_total)
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_add_cart_item(request):
    try:
        data = json.loads(request.body)
        prod_id = data.get('product_id')
        qty = int(data.get('quantity', 1))

        product = get_object_or_404(Product, id=prod_id)
        cart = _get_cart(request)

        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            item.quantity += qty
        else:
            item.quantity = qty
        item.save()

        # Recalculate promo discount
        if cart.promo_code:
            cart.discount_amount = Decimal(str(cart.calculate_discount(cart.promo_code)))
            cart.save()

        log_user_activity(get_or_set_session_id(request), request.user, 'cart_add', product=product)

        return api_response(data={
            'message': f"Added {product.name} to cart",
            'total_items': cart.total_items,
            'grand_total': str(cart.grand_total)
        })
    except Exception as e:
        return api_response(error={'code': 'CART_ERROR', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_checkout(request):
    if not request.user.is_authenticated:
        return api_response(error={'code': 'AUTH_REQUIRED', 'message': 'Login is required to place an order.'}, status=401)

    try:
        data = json.loads(request.body)
        cart = _get_cart(request)
        if cart.items.count() == 0:
            return api_response(error={'code': 'EMPTY_CART', 'message': 'Cart is empty.'}, status=400)

        order_num = Order.generate_order_number()
        order = Order.objects.create(
            order_number=order_num,
            user=request.user,
            recipient_name=data.get('recipient_name', request.user.display_name),
            shipping_address=data.get('shipping_address', 'Default Delivery Address'),
            phone=data.get('phone', request.user.phone or '+91 98765 43210'),
            subtotal=cart.subtotal,
            discount_amount=cart.discount_amount,
            promo_code=cart.promo_code,
            shipping_fee=cart.estimated_shipping,
            tax=cart.estimated_tax,
            total_amount=cart.grand_total,
            payment_method=data.get('payment_method', 'Card ending in 4242'),
            status='placed'
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                price=item.product.price,
                quantity=item.quantity,
                image_url=item.product.main_image
            )
            # Log purchase
            log_user_activity(get_or_set_session_id(request), request.user, 'purchase', product=item.product)

        # Initial Tracking Event
        OrderTrackingEvent.objects.create(
            order=order,
            stage='placed',
            title='Order Placed & Confirmed',
            description='Your payment was verified and order details sent to warehouse.',
            location='Central Fulfillment Center',
            timestamp=timezone.now(),
            order_step=1,
            is_completed=True
        )

        # Clear Cart
        cart.items.all().delete()
        cart.promo_code = None
        cart.discount_amount = 0
        cart.save()

        # Send Notification
        send_notification(
            user=request.user,
            notification_type='order_status',
            title=f"Order Confirmed: #{order.order_number}",
            body=f"We've received your order of ₹{order.total_amount}. Tracking is now active.",
            related_link=f"/customer/orders/{order.order_number}/"
        )

        return api_response(data={
            'order_number': order.order_number,
            'total_amount': str(order.total_amount),
            'status': order.status
        }, status=201)
    except Exception as e:
        return api_response(error={'code': 'CHECKOUT_ERROR', 'message': str(e)}, status=500)


@require_http_methods(["GET"])
def api_order_tracking(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    events = [{
        'stage': ev.stage,
        'title': ev.title,
        'description': ev.description,
        'location': ev.location,
        'timestamp': ev.timestamp.isoformat(),
        'is_completed': ev.is_completed,
        'order_step': ev.order_step
    } for ev in order.tracking_events.all()]

    return api_response(data={
        'order_number': order.order_number,
        'status': order.status,
        'recipient_name': order.recipient_name,
        'total_amount': str(order.total_amount),
        'tracking_events': events
    })


# =======================================================
# MODULE 5: REVIEWS & AI FAKE CLASSIFIER
# =======================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_create_review(request):
    try:
        data = json.loads(request.body)
        prod_id = data.get('product_id')
        title = data.get('title')
        content = data.get('content')
        rating = int(data.get('rating', 5))
        author_name = data.get('author_name', request.user.display_name if request.user.is_authenticated else 'Customer')

        product = get_object_or_404(Product, id=prod_id)
        is_verified = request.user.is_authenticated and OrderItem.objects.filter(order__user=request.user, product=product).exists()

        review = Review.objects.create(
            product=product,
            user=request.user if request.user.is_authenticated else None,
            author_name=author_name,
            title=title,
            content=content,
            rating=rating,
            is_verified_purchase=is_verified
        )

        # Run AI Fake Classifier
        clf = classify_review_content(author_name, title, content, rating, is_verified)
        ReviewFlag.objects.create(
            review=review,
            suspicion_score=clf['suspicion_score'],
            flag_reason=clf['flag_reason'],
            ai_classification_details=clf['ai_classification_details'],
            status=clf['status']
        )

        # Recalculate Trust Score
        product.recalculate_trust_score()

        return api_response(data={
            'review_id': review.id,
            'suspicion_score': clf['suspicion_score'],
            'moderation_status': clf['status'],
            'new_product_trust_score': product.trust_score
        }, status=201)
    except Exception as e:
        return api_response(error={'code': 'REVIEW_ERROR', 'message': str(e)}, status=500)


# =======================================================
# MODULE 6: PRICING & AI PRICE PREDICTIONS
# =======================================================

@require_http_methods(["GET"])
def api_price_history(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    history = [{
        'old_price': str(h.old_price),
        'new_price': str(h.new_price),
        'changed_at': h.changed_at.isoformat()
    } for h in product.price_history.all()]

    prediction = getattr(product, 'price_prediction', None)
    if not prediction:
        prediction = predict_product_price_trend(product)

    return api_response(data={
        'product_id': product.id,
        'current_price': str(product.price),
        'history': history,
        'prediction': {
            'predicted_trend': prediction.predicted_trend,
            'confidence_score': prediction.confidence_score,
            'suggestion_text': prediction.suggestion_text
        }
    })


# =======================================================
# MODULE 7: AI SHOPPING ASSISTANT
# =======================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_assistant_message(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        conv_id = data.get('conversation_id')
        session_id = get_or_set_session_id(request)

        if not user_message:
            return api_response(error={'code': 'EMPTY_MESSAGE', 'message': 'Message cannot be empty.'}, status=400)

        if conv_id:
            conv = get_object_or_404(AssistantConversation, id=conv_id)
        else:
            conv = AssistantConversation.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=session_id
            )

        # Log User Message
        AssistantMessage.objects.create(
            conversation=conv,
            sender='user',
            message_text=user_message
        )

        # AI Intent & Ranking Pipeline
        result = parse_shopping_intent_and_rank(user_message, request.user, session_id)

        # Log AI Assistant Response
        AssistantMessage.objects.create(
            conversation=conv,
            sender='assistant',
            message_text=result['response_text'],
            parsed_intent=result['parsed_intent'],
            suggested_products=result['suggested_products']
        )

        return api_response(data={
            'conversation_id': conv.id,
            'response': result['response_text'],
            'parsed_intent': result['parsed_intent'],
            'suggested_products': result['suggested_products']
        })
    except Exception as e:
        return api_response(error={'code': 'ASSISTANT_ERROR', 'message': str(e)}, status=500)


# =======================================================
# MODULE 8: RECOMMENDATIONS & PERSONALIZATION
# =======================================================

@require_http_methods(["GET"])
def api_recommendations_home(request):
    session_id = get_or_set_session_id(request)
    products = get_personalized_recommendations(request.user, session_id, limit=8)

    data = [{
        'id': p.id,
        'name': p.name,
        'slug': p.slug,
        'brand': p.brand,
        'category': p.category.name,
        'price': str(p.price),
        'trust_score': p.trust_score,
        'rating': str(p.rating),
        'main_image': p.main_image
    } for p in products]

    return api_response(data=data)


# =======================================================
# MODULE 9: VOICE SEARCH & QR MARKETING
# =======================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_voice_search(request):
    try:
        data = json.loads(request.body)
        transcript = data.get('transcript', '').strip()
        session_id = get_or_set_session_id(request)

        products = Product.objects.filter(
            Q(name__icontains=transcript) | Q(brand__icontains=transcript) | Q(category__name__icontains=transcript),
            is_published=True
        )[:8]

        VoiceSearchLog.objects.create(
            session_id=session_id,
            user=request.user if request.user.is_authenticated else None,
            transcript=transcript,
            matched_products_count=products.count()
        )

        results = [{
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'price': str(p.price),
            'main_image': p.main_image
        } for p in products]

        return api_response(data={'transcript': transcript, 'results': results})
    except Exception as e:
        return api_response(error={'code': 'VOICE_ERROR', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_qr_generate(request):
    try:
        data = json.loads(request.body)
        prod_id = data.get('product_id')
        campaign = data.get('campaign', 'Product Share')

        product = get_object_or_404(Product, id=prod_id)
        qr = QRShare.objects.create(
            product=product,
            campaign_name=campaign,
            deep_link_url=f"/product/{product.slug}/?src=qr_{campaign}"
        )
        return api_response(data={
            'qr_token': str(qr.qr_code_token),
            'deep_link_url': qr.deep_link_url,
            'product_name': product.name
        }, status=201)
    except Exception as e:
        return api_response(error={'code': 'QR_ERROR', 'message': str(e)}, status=500)


# =======================================================
# MODULE 10: CENTRAL NOTIFICATIONS
# =======================================================

@require_http_methods(["GET"])
def api_list_notifications(request):
    if not request.user.is_authenticated:
        return api_response(error={'code': 'AUTH_REQUIRED', 'message': 'Login required.'}, status=401)

    notifs = request.user.notifications.all()[:20]
    data = [{
        'id': n.id,
        'type': n.notification_type,
        'title': n.title,
        'body': n.body,
        'related_link': n.related_link,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat()
    } for n in notifs]

    return api_response(data=data, unread_count=request.user.notifications.filter(is_read=False).count())


# =======================================================
# MODULE 11: COUPONS, AUDIT & CSV ANALYTICS EXPORT
# =======================================================

@require_http_methods(["GET"])
def api_list_coupons(request):
    coupons = Coupon.objects.filter(is_active=True)
    data = [{
        'code': c.code,
        'title': c.title,
        'discount_type': c.discount_type,
        'discount_value': str(c.discount_value),
        'min_order_amount': str(c.min_order_amount),
        'valid_until': c.valid_until.isoformat() if c.valid_until else None
    } for c in coupons]
    return api_response(data=data)


@require_http_methods(["GET"])
def api_export_sales_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="quickcart_sales_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Date', 'Customer', 'Items', 'Subtotal', 'Discount', 'Total Amount', 'Status'])

    for order in Order.objects.all().order_by('-created_at'):
        writer.writerow([
            order.order_number,
            order.created_at.strftime('%Y-%m-%d %H:%M'),
            order.recipient_name,
            order.total_items,
            order.subtotal,
            order.discount_amount,
            order.total_amount,
            order.status
        ])

    return response


# =======================================================
# PLUGGABLE INTERNAL AI MOCK INTERFACES
# =======================================================

@csrf_exempt
@require_http_methods(["POST"])
def internal_ai_classify_review(request):
    try:
        data = json.loads(request.body)
        res = classify_review_content(
            author_name=data.get('author_name', ''),
            title=data.get('title', ''),
            content=data.get('content', ''),
            rating=int(data.get('rating', 5)),
            is_verified_purchase=data.get('is_verified_purchase', True)
        )
        return api_response(data=res)
    except Exception as e:
        return api_response(error={'code': 'CLASSIFIER_ERROR', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def internal_ai_predict_price(request):
    try:
        data = json.loads(request.body)
        prod_id = data.get('product_id')
        product = get_object_or_404(Product, id=prod_id)
        pred = predict_product_price_trend(product)
        return api_response(data={
            'product_id': product.id,
            'predicted_trend': pred.predicted_trend,
            'confidence_score': pred.confidence_score,
            'suggestion_text': pred.suggestion_text,
            'predicted_next_price': str(pred.predicted_next_price) if pred.predicted_next_price else None
        })
    except Exception as e:
        return api_response(error={'code': 'PREDICTOR_ERROR', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def internal_ai_parse_intent(request):
    try:
        data = json.loads(request.body)
        msg = data.get('message', '')
        res = parse_shopping_intent_and_rank(msg)
        return api_response(data=res)
    except Exception as e:
        return api_response(error={'code': 'INTENT_ERROR', 'message': str(e)}, status=500)
