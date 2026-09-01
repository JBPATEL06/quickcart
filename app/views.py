from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
from .models import (
    User, Address, Category, Product, ProductImage, 
    Review, Wishlist, Cart, CartItem, Order, OrderItem, 
    OrderTrackingEvent, SupportMessage, FAQItem, Coupon, ReviewFlag, Notification
)
from .ai_services import execute_smart_catalog_search, parse_natural_language_search_query

# Helper: Cart session/user management
def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.save()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


# ==========================================
# 1. STORE VIEWS (HOME, SEARCH, CATEGORY, DETAIL, COMPARE)
# ==========================================

def home_view(request):
    categories = Category.objects.all()
    trending_products = Product.objects.filter(is_trending=True)[:8]
    limited_offers = Product.objects.filter(is_limited_offer=True)[:4]
    all_products = Product.objects.all()[:12]

    return render(request, 'store/home.html', {
        'categories': categories,
        'trending_products': trending_products,
        'limited_offers': limited_offers,
        'all_products': all_products,
    })


def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    
    sort = request.GET.get('sort', 'featured')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'rating':
        products = products.order_by('-rating')
    elif sort == 'trust':
        products = products.order_by('-trust_score')

    paginator = Paginator(products, 16)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'store/category.html', {
        'category': category,
        'products': page_obj,
        'page_obj': page_obj,
        'total_count': paginator.count,
        'current_sort': sort,
    })


def search_view(request):
    raw_query = request.GET.get('q', '').strip()
    min_p = request.GET.get('min_price')
    max_p = request.GET.get('max_price')
    products = Product.objects.filter(is_published=True)
    parsed_info = {}

    if raw_query:
        products, parsed_info = execute_smart_catalog_search(raw_query, products)

    if min_p and min_p.replace('.', '', 1).isdigit():
        products = products.filter(price__gte=float(min_p))
    if max_p and max_p.replace('.', '', 1).isdigit():
        products = products.filter(price__lte=float(max_p))

    cat_filter = request.GET.getlist('category')
    if cat_filter:
        products = products.filter(category__slug__in=cat_filter)

    min_rating = request.GET.get('rating')
    if min_rating:
        products = products.filter(rating__gte=min_rating)

    sort = request.GET.get('sort', 'relevance')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'rating':
        products = products.order_by('-rating')
    elif sort == 'trust':
        products = products.order_by('-trust_score')

    paginator = Paginator(products, 16)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'store/search.html', {
        'query': raw_query,
        'parsed_info': parsed_info,
        'products': page_obj,
        'page_obj': page_obj,
        'total_count': paginator.count,
        'current_sort': sort,
        'selected_categories': cat_filter,
        'current_min_price': min_p,
        'current_max_price': max_p,
    })


def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    reviews = product.reviews.all()
    images = product.images.all()

    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'images': images,
    })


def compare_view(request):
    ids_param = request.GET.get('ids', '')
    product_ids = [int(i) for i in ids_param.split(',') if i.isdigit()]
    products = Product.objects.filter(id__in=product_ids)

    return render(request, 'store/compare.html', {
        'products': products,
    })


# ==========================================
# 2. CART & CHECKOUT VIEWS
# ==========================================

def cart_detail_view(request):
    cart = get_or_create_cart(request)
    return render(request, 'cart/cart.html', {'cart': cart})


def api_add_to_cart(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity
    item.save()

    return JsonResponse({
        'success': True,
        'message': f"Added {product.name} to cart.",
        'total_items': cart.total_items,
        'subtotal': str(cart.subtotal),
    })


def api_update_cart(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    item_id = request.POST.get('item_id')
    action = request.POST.get('action')
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)

    if action == 'increase':
        item.quantity += 1
        item.save()
    elif action == 'decrease':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
            item = None

    if cart.promo_code:
        cart.discount_amount = cart.calculate_discount(cart.promo_code)
        cart.save()

    return JsonResponse({
        'success': True,
        'item_quantity': item.quantity if item else 0,
        'item_total': str(item.total_price) if item else "0.00",
        'cart_total_items': cart.total_items,
        'cart_subtotal': str(cart.subtotal),
        'cart_discount': str(cart.discount_amount),
        'cart_shipping': str(cart.estimated_shipping),
        'cart_tax': str(cart.estimated_tax),
        'cart_grand_total': f"{cart.grand_total:.2f}",
    })


def api_remove_from_cart(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    item_id = request.POST.get('item_id')
    cart = get_or_create_cart(request)
    CartItem.objects.filter(id=item_id, cart=cart).delete()

    if cart.promo_code:
        cart.discount_amount = cart.calculate_discount(cart.promo_code)
        cart.save()

    return JsonResponse({
        'success': True,
        'cart_total_items': cart.total_items,
        'cart_subtotal': str(cart.subtotal),
        'cart_discount': str(cart.discount_amount),
        'cart_shipping': str(cart.estimated_shipping),
        'cart_tax': str(cart.estimated_tax),
        'cart_grand_total': f"{cart.grand_total:.2f}",
    })


def api_apply_promo(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    code = request.POST.get('promo_code', '').strip().upper()
    cart = get_or_create_cart(request)

    if not code:
        return JsonResponse({'success': False, 'message': 'Please enter a valid promo code.'}, status=400)

    valid_promos = {
        'QUICK20': '20% discount applied!',
        'WELCOME10': '10% welcome discount applied!',
        'FLAT50': '₹50 flat discount applied!',
        'FREESHIP': 'Free delivery unlocked!',
    }

    if code not in valid_promos:
        return JsonResponse({'success': False, 'message': 'Invalid promo code. Try QUICK20 or WELCOME10.'}, status=400)

    discount = cart.calculate_discount(code)
    cart.promo_code = code
    cart.discount_amount = discount
    cart.save()

    return JsonResponse({
        'success': True,
        'message': f"Success! {valid_promos[code]}",
        'promo_code': code,
        'discount_amount': str(discount),
        'subtotal': str(cart.subtotal),
        'shipping': str(cart.estimated_shipping),
        'tax': str(cart.estimated_tax),
        'grand_total': f"{cart.grand_total:.2f}",
    })


def api_remove_promo(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    cart = get_or_create_cart(request)
    cart.promo_code = None
    cart.discount_amount = 0
    cart.save()

    return JsonResponse({
        'success': True,
        'message': "Promo code removed.",
        'subtotal': str(cart.subtotal),
        'discount_amount': "0.00",
        'shipping': str(cart.estimated_shipping),
        'tax': str(cart.estimated_tax),
        'grand_total': f"{cart.grand_total:.2f}",
    })


def payment_gateway_view(request):
    cart = get_or_create_cart(request)
    if cart.total_items == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect('store:home')

    if request.method == 'POST':
        recipient_name = request.POST.get('recipient_name', 'Maya Thompson')
        phone = request.POST.get('phone', '+91 98765 43210')
        shipping_address = request.POST.get('shipping_address', '42 Silver Oak Avenue, Bengaluru')
        payment_method = request.POST.get('payment_method', 'Credit / Debit Card')

        user = request.user if request.user.is_authenticated else None
        if not user:
            user = User.objects.filter(username='maya@example.com').first()

        order = Order.objects.create(
            order_number=Order.generate_order_number(),
            user=user,
            status='placed',
            recipient_name=recipient_name,
            shipping_address=shipping_address,
            phone=phone,
            subtotal=cart.subtotal,
            shipping_fee=cart.estimated_shipping,
            tax=cart.estimated_tax,
            discount_amount=cart.discount_amount,
            promo_code=cart.promo_code,
            total_amount=cart.grand_total,
            payment_method=payment_method,
            tracking_number=f"TRK-{timezone.now().strftime('%Y%m%d%H%M%S')[-8:]}",
            carrier="QuickCart Express Delivery",
            estimated_delivery="Estimated Delivery in 2-3 Business Days"
        )

        for ci in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=ci.product,
                product_name=ci.product.name,
                price=ci.product.price,
                quantity=ci.quantity,
                image_url=ci.product.main_image
            )

        OrderTrackingEvent.objects.create(
            order=order,
            stage='placed',
            title='Order Placed & Payment Authorized',
            description=f'Payment verified via {payment_method}. Seller preparing fulfillment.',
            location='Bengaluru Central Hub',
            timestamp=timezone.now(),
            is_completed=True,
            order_step=1
        )

        # Clear cart
        cart.items.all().delete()
        cart.promo_code = None
        cart.discount_amount = 0
        cart.save()

        messages.success(request, f"Order #{order.order_number} confirmed! Payment processed successfully.")
        return redirect('customer:order_detail', order.order_number)

    return render(request, 'cart/payment.html', {'cart': cart})


def about_view(request):
    return render(request, 'pages/about.html')


def terms_view(request):
    return render(request, 'pages/terms.html')


def help_faq_view(request):
    return render(request, 'pages/help.html')


@login_required
def checkout_view(request):
    cart = get_or_create_cart(request)
    if cart.total_items == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect('store:home')

    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first() or addresses.first()

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method', 'Credit Card ending in 4242')
        
        if address_id:
            addr = get_object_or_404(Address, id=address_id, user=request.user)
            shipping_str = f"{addr.recipient_name}, {addr.street_address}, {addr.city}, {addr.state} - {addr.postal_code}"
            recipient_name = addr.recipient_name
            phone = addr.phone
        else:
            recipient_name = request.POST.get('recipient_name', request.user.display_name)
            shipping_str = f"{request.POST.get('street_address')}, {request.POST.get('city')}, {request.POST.get('state')} - {request.POST.get('postal_code')}"
            phone = request.POST.get('phone', request.user.phone or '+91 98765 43210')

        order = Order.objects.create(
            order_number=Order.generate_order_number(),
            user=request.user,
            status='placed',
            recipient_name=recipient_name,
            shipping_address=shipping_str,
            phone=phone,
            subtotal=cart.subtotal,
            discount_amount=cart.discount_amount,
            promo_code=cart.promo_code,
            shipping_fee=cart.estimated_shipping,
            tax=cart.estimated_tax,
            total_amount=cart.grand_total,
            payment_method=payment_method,
            carrier='QuickCart Express',
            estimated_delivery='Within 3-4 business days'
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

        OrderTrackingEvent.objects.create(
            order=order,
            stage='placed',
            title='Order Placed & Confirmed',
            description='We received your order and are preparing it for shipment.',
            location='Bengaluru Central Hub',
            timestamp=timezone.now(),
            is_completed=True,
            order_step=1
        )

        cart.items.all().delete()
        messages.success(request, f"Order #{order.order_number} placed successfully!")
        return redirect('customer:order_detail', order_number=order.order_number)

    return render(request, 'cart/checkout.html', {
        'cart': cart,
        'addresses': addresses,
        'default_address': default_address,
    })


# ==========================================
# 3. AUTHENTICATION & CUSTOMER PORTAL VIEWS
# ==========================================

def login_view(request):
    next_url = request.GET.get('next', '').strip()
    
    if request.user.is_authenticated:
        if request.user.is_staff or getattr(request.user, 'role', '') == 'admin':
            return redirect('admin_dashboard')
        if next_url and next_url.startswith('/') and not next_url.startswith('/admin-panel/'):
            return redirect(next_url)
        return redirect('customer:orders')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            if user.is_staff or getattr(user, 'role', '') == 'admin':
                return redirect('admin_dashboard')
            if next_url and next_url.startswith('/') and not next_url.startswith('/admin-panel/'):
                return redirect(next_url)
            return redirect('customer:orders')
        else:
            messages.error(request, "Invalid email or password. Please try again.")

    return render(request, 'accounts/login.html', {'next': next_url})


def signup_view(request):
    next_url = request.GET.get('next', '').strip()
    if request.user.is_authenticated:
        if request.user.is_staff or getattr(request.user, 'role', '') == 'admin':
            return redirect('admin_dashboard')
        return redirect('customer:orders')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not email or not password:
            messages.error(request, "Please fill in all required fields.")
        elif password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=email).exists():
            messages.error(request, "An account with this email already exists.")
        else:
            names = full_name.split(' ', 1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ''
            
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='customer'
            )
            login(request, user)
            messages.success(request, f"Welcome to QuickCart, {user.first_name}!")
            if next_url and next_url.startswith('/') and not next_url.startswith('/admin-panel/'):
                return redirect(next_url)
            return redirect('customer:orders')

    return render(request, 'accounts/signup.html', {'next': next_url})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('store:home')


def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        user = User.objects.filter(email=email).first()
        if user:
            # Send password reset email via Django mail
            from django.core.mail import send_mail
            try:
                send_mail(
                    subject="QuickCart Password Reset Request",
                    message=f"Hi {user.first_name or 'there'},\n\nWe received a request to reset your QuickCart password. Click below to set a new password:\n\nhttp://127.0.0.1:8000/accounts/reset-password/\n\nIf you did not request this, please ignore this email.\n\nBest regards,\nQuickCart Security Team",
                    from_email="support@quickcart.com",
                    recipient_list=[email],
                    fail_silently=True
                )
            except Exception:
                pass
        request.session['reset_email'] = email
        return redirect('accounts:forgot_password_done')

    return render(request, 'accounts/forgot_password.html')


def forgot_password_done_view(request):
    email = request.session.get('reset_email', '')
    return render(request, 'accounts/forgot_password_done.html', {'email': email})


def reset_password_view(request):
    if request.method == 'POST':
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        email = request.session.get('reset_email', '')

        if not password or password != confirm:
            return render(request, 'accounts/reset_password.html', {'error': 'Passwords do not match.'})

        user = User.objects.filter(email=email).first() or User.objects.filter(username='maya@example.com').first()
        if user:
            user.set_password(password)
            user.save()
            messages.success(request, "Password updated successfully! Please log in.")
            return redirect('accounts:login')
        else:
            return render(request, 'accounts/reset_password.html', {'error': 'User account not found.'})

    return render(request, 'accounts/reset_password.html')


@login_required
def orders_view(request):
    status_filter = request.GET.get('status', 'all')
    orders = Order.objects.filter(user=request.user)
    
    if status_filter == 'delivered':
        orders = orders.filter(status='delivered')
    elif status_filter == 'in_transit':
        orders = orders.filter(status__in=['in_transit', 'shipped', 'out_for_delivery'])
    elif status_filter == 'cancelled':
        orders = orders.filter(status='cancelled')

    return render(request, 'customer/orders.html', {
        'orders': orders,
        'current_status': status_filter,
        'active_tab': 'orders'
    })


@login_required
def order_detail_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    tracking_events = order.tracking_events.all()
    return render(request, 'customer/order_detail.html', {
        'order': order,
        'tracking_events': tracking_events,
        'active_tab': 'orders'
    })


@login_required
def wishlist_view(request):
    category_slug = request.GET.get('category', 'all')
    user_wishlist = Wishlist.objects.filter(user=request.user).select_related('product', 'product__category')
    
    # Extract only categories present in the user's saved items
    saved_category_ids = user_wishlist.values_list('product__category_id', flat=True).distinct()
    saved_categories = Category.objects.filter(id__in=saved_category_ids).order_by('name')

    wishlist_items = user_wishlist
    if category_slug and category_slug != 'all':
        wishlist_items = wishlist_items.filter(product__category__slug=category_slug)

    return render(request, 'customer/wishlist.html', {
        'wishlist_items': wishlist_items,
        'saved_categories': saved_categories,
        'total_saved_count': user_wishlist.count(),
        'current_category': category_slug,
        'active_tab': 'wishlist'
    })


@login_required
def addresses_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            Address.objects.create(
                user=request.user,
                recipient_name=request.POST.get('recipient_name'),
                street_address=request.POST.get('street_address'),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                postal_code=request.POST.get('postal_code'),
                phone=request.POST.get('phone'),
                label=request.POST.get('label', 'home'),
                is_default=(request.POST.get('is_default') == 'on')
            )
            messages.success(request, "New address added successfully!")
            return redirect('customer:addresses')

        elif action == 'delete':
            Address.objects.filter(id=request.POST.get('address_id'), user=request.user).delete()
            messages.success(request, "Address deleted.")
            return redirect('customer:addresses')

        elif action == 'set_default':
            addr = get_object_or_404(Address, id=request.POST.get('address_id'), user=request.user)
            addr.is_default = True
            addr.save()
            messages.success(request, "Default address updated.")
            return redirect('customer:addresses')

    addresses = Address.objects.filter(user=request.user)
    return render(request, 'customer/addresses.html', {
        'addresses': addresses,
        'active_tab': 'addresses'
    })


@login_required
def settings_view(request):
    if request.method == 'POST':
        section = request.POST.get('section')
        if section == 'personal':
            request.user.first_name = request.POST.get('first_name', '').strip()
            request.user.last_name = request.POST.get('last_name', '').strip()
            request.user.phone = request.POST.get('phone', '').strip()
            request.user.save()
            messages.success(request, "Personal information updated.")
        
        elif section == 'password':
            old_pass = request.POST.get('old_password')
            new_pass = request.POST.get('new_password')
            confirm_pass = request.POST.get('confirm_password')
            
            if not request.user.check_password(old_pass):
                messages.error(request, "Current password is incorrect.")
            elif new_pass != confirm_pass:
                messages.error(request, "New passwords do not match.")
            else:
                request.user.set_password(new_pass)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Password updated successfully.")
        
        elif section == 'preferences':
            request.user.email_notifications = request.POST.get('email_notifications') == 'on'
            request.user.order_updates = request.POST.get('order_updates') == 'on'
            request.user.marketing_emails = request.POST.get('marketing_emails') == 'on'
            request.user.save()
            messages.success(request, "Notification preferences saved.")

        return redirect('customer:settings')

    return render(request, 'customer/settings.html', {'active_tab': 'settings'})


@login_required
def help_view(request):
    faqs = FAQItem.objects.all()
    return render(request, 'customer/help.html', {
        'faqs': faqs,
        'active_tab': 'help'
    })


# ==========================================
# 4. SUPPORT VIEWS & AJAX ENDPOINTS
# ==========================================

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        order_number = request.POST.get('order_number', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and message:
            SupportMessage.objects.create(name=name, email=email, order_number=order_number, message=message)
            return redirect('support:contact_success')
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, 'support/contact.html')


def contact_success_view(request):
    return render(request, 'support/contact_success.html')


def api_toggle_wishlist(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Login required to save items.'}, status=401)
    
    product = get_object_or_404(Product, id=request.POST.get('product_id'))
    item = Wishlist.objects.filter(user=request.user, product=product).first()
    if item:
        item.delete()
        saved = False
        msg = f"Removed {product.name} from saved items."
    else:
        Wishlist.objects.create(user=request.user, product=product)
        saved = True
        msg = f"Added {product.name} to saved items."

    return JsonResponse({'success': True, 'saved': saved, 'message': msg})


def api_search_autocomplete(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    products, _ = execute_smart_catalog_search(query)
    results = [{
        'id': p.id,
        'name': p.name,
        'price': str(p.price),
        'image': p.main_image,
        'url': f"/product/{p.slug}/"
    } for p in products[:6]]

    return JsonResponse({'results': results})


# ==========================================
# 5. ADMIN PANEL CONTROLLERS (SCREENS 21-26)
# ==========================================

def admin_dashboard_view(request):
    total_orders = Order.objects.count()
    total_users = User.objects.count()
    rev_agg = Order.objects.exclude(status='cancelled').aggregate(total=Sum('total_amount'))
    total_rev = rev_agg['total'] or 0
    
    # Status Counts for Donut Chart
    placed_cnt = Order.objects.filter(status='placed').count()
    confirmed_cnt = Order.objects.filter(status='confirmed').count()
    shipped_cnt = Order.objects.filter(status__in=['shipped', 'in_transit', 'out_for_delivery']).count()
    delivered_cnt = Order.objects.filter(status='delivered').count()
    cancelled_cnt = Order.objects.filter(status='cancelled').count()

    # Alerts Count
    flagged_reviews = ReviewFlag.objects.select_related('review', 'review__product').filter(is_moderated=False)[:4]
    low_stock_products = Product.objects.filter(stock__lt=20)[:4]
    alerts_count = flagged_reviews.count() + low_stock_products.count()

    recent_orders = Order.objects.all().order_by('-created_at')[:6]

    return render(request, 'admin/dashboard.html', {
        'active_admin_tab': 'dashboard',
        'total_orders_count': total_orders,
        'total_revenue': f"{total_rev:,.2f}",
        'total_revenue_num': float(total_rev),
        'total_users_count': total_users,
        'alerts_count': alerts_count,
        'recent_orders': recent_orders,
        'flagged_reviews': flagged_reviews,
        'low_stock_products': low_stock_products,
        'placed_cnt': placed_cnt,
        'confirmed_cnt': confirmed_cnt,
        'shipped_cnt': shipped_cnt,
        'delivered_cnt': delivered_cnt,
        'cancelled_cnt': cancelled_cnt,
    })


def admin_orders_view(request):
    status_filter = request.GET.get('status', 'all')
    search_q = request.GET.get('q', '').strip()
    orders = Order.objects.all().order_by('-created_at')

    if status_filter != 'all' and status_filter:
        orders = orders.filter(status=status_filter)

    if search_q:
        orders = orders.filter(
            Q(order_number__icontains=search_q) |
            Q(recipient_name__icontains=search_q) |
            Q(user__email__icontains=search_q) |
            Q(phone__icontains=search_q)
        )

    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/orders.html', {
        'active_admin_tab': 'orders',
        'orders': page_obj,
        'page_obj': page_obj,
        'total_count': paginator.count,
        'current_status': status_filter,
        'search_query': search_q,
    })


def admin_order_detail_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'admin/order_detail.html', {
        'active_admin_tab': 'orders',
        'order': order,
    })


def admin_update_order_status(request, order_number):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        order = get_object_or_404(Order, order_number=order_number)
        
        status_titles = {
            'confirmed': ('Order Confirmed', 'Your order has been verified and processed by the seller.', 2),
            'shipped': ('Order Shipped', 'Your package has left the fulfillment hub.', 3),
            'in_transit': ('In Transit', 'Package is on the way to your local distribution center.', 4),
            'out_for_delivery': ('Out for Delivery', 'Courier executive is delivering your package today.', 5),
            'delivered': ('Delivered', 'Package safely handed over at delivery address.', 6),
            'cancelled': ('Order Cancelled', 'Order has been cancelled.', 0),
        }

        if new_status in status_titles:
            order.status = new_status
            order.save()

            title, desc, step = status_titles[new_status]
            OrderTrackingEvent.objects.create(
                order=order,
                stage=new_status,
                title=title,
                description=desc,
                location='Bengaluru Central Hub',
                timestamp=timezone.now(),
                is_completed=True,
                order_step=step
            )

            if order.user:
                Notification.objects.create(
                    user=order.user,
                    title=f"Order #{order.order_number}: {title}",
                    body=desc,
                    notification_type='order',
                    related_link=f"/customer/orders/{order.order_number}/"
                )

                from django.core.mail import send_mail
                try:
                    send_mail(
                        subject=f"QuickCart Update: Order #{order.order_number} is {new_status.replace('_', ' ').title()}",
                        message=f"Hi {order.recipient_name},\n\nYour order #{order.order_number} has been updated to: {new_status.replace('_', ' ').title()}.\n\n{desc}\n\nTrack your order in real-time:\nhttp://127.0.0.1:8000/customer/orders/{order.order_number}/\n\nThank you for shopping with QuickCart!",
                        from_email="orders@quickcart.com",
                        recipient_list=[order.user.email],
                        fail_silently=True
                    )
                except Exception:
                    pass

            messages.success(request, f"Order #{order_number} status updated to '{new_status.replace('_', ' ').title()}' successfully!")

    referer = request.META.get('HTTP_REFERER')
    if referer and '/admin-panel/orders/' in referer:
        return redirect(referer)
    return redirect('admin_orders')


def admin_products_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        brand = request.POST.get('brand')
        category_id = request.POST.get('category_id')
        price = request.POST.get('price')
        stock = request.POST.get('stock', 50)
        main_image = request.POST.get('main_image', '').strip()
        description = request.POST.get('description')

        category = get_object_or_404(Category, id=category_id)
        from django.utils.text import slugify
        slug = slugify(f"{name}-{Product.objects.count() + 1}")

        # Handle multiple uploaded image files
        from django.core.files.storage import default_storage
        uploaded_files = request.FILES.getlist('product_images')
        
        if uploaded_files:
            first_file = uploaded_files[0]
            saved_path = default_storage.save(f"products/{first_file.name}", first_file)
            main_image = default_storage.url(saved_path)
        elif not main_image:
            main_image = "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80"

        prod = Product.objects.create(
            name=name,
            slug=slug,
            brand=brand,
            category=category,
            price=price,
            stock=stock,
            main_image=main_image,
            description=description,
            trust_score=95,
            is_published=True
        )

        # Create ProductImage gallery records for all uploaded files
        for i, f in enumerate(uploaded_files):
            if i > 0:
                f_path = default_storage.save(f"products/{f.name}", f)
                img_url = default_storage.url(f_path)
            else:
                img_url = main_image
            ProductImage.objects.create(product=prod, image_url=img_url, order=i)

        messages.success(request, f"Product '{name}' added to catalog successfully with {len(uploaded_files)} images!")
        return redirect('admin_products')

    category_slug = request.GET.get('category', 'all')
    search_q = request.GET.get('q', '').strip()
    products = Product.objects.all().select_related('category').order_by('-id')

    if category_slug != 'all' and category_slug:
        products = products.filter(category__slug=category_slug)

    if search_q:
        products = products.filter(
            Q(name__icontains=search_q) |
            Q(brand__icontains=search_q) |
            Q(description__icontains=search_q)
        )

    all_categories = Category.objects.all()
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/products.html', {
        'active_admin_tab': 'products',
        'products': page_obj,
        'page_obj': page_obj,
        'total_count': paginator.count,
        'all_categories': all_categories,
        'current_category': category_slug,
        'search_query': search_q,
    })


def admin_edit_product(request, product_id):
    if request.method == 'POST':
        prod = get_object_or_404(Product, id=product_id)
        prod.name = request.POST.get('name', prod.name)
        prod.brand = request.POST.get('brand', prod.brand)
        category_id = request.POST.get('category_id')
        if category_id:
            prod.category = get_object_or_404(Category, id=category_id)
        prod.price = request.POST.get('price', prod.price)
        prod.stock = request.POST.get('stock', prod.stock)
        
        # Handle multiple uploaded image files
        from django.core.files.storage import default_storage
        uploaded_files = request.FILES.getlist('product_images')
        
        if uploaded_files:
            first_file = uploaded_files[0]
            saved_path = default_storage.save(f"products/{first_file.name}", first_file)
            prod.main_image = default_storage.url(saved_path)
            
            for i, f in enumerate(uploaded_files):
                if i > 0:
                    f_path = default_storage.save(f"products/{f.name}", f)
                    img_url = default_storage.url(f_path)
                else:
                    img_url = prod.main_image
                ProductImage.objects.create(product=prod, image_url=img_url, order=i)
        elif request.POST.get('main_image'):
            prod.main_image = request.POST.get('main_image')

        prod.description = request.POST.get('description', prod.description)
        prod.save()
        messages.success(request, f"Product '{prod.name}' updated successfully!")
    return redirect('admin_products')


def admin_delete_product(request, product_id):
    if request.method == 'POST':
        prod = get_object_or_404(Product, id=product_id)
        name = prod.name
        prod.delete()
        messages.success(request, f"Product '{name}' has been deleted from the catalog.")
    return redirect('admin_products')


def admin_create_category(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        icon_name = request.POST.get('icon_name', 'bi-tag').strip()
        from django.utils.text import slugify
        slug = request.POST.get('slug') or slugify(name)
        
        if name:
            cat, created = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'icon_name': icon_name, 'order': Category.objects.count() + 1}
            )
            if created:
                messages.success(request, f"Custom category '{name}' created successfully!")
            else:
                messages.info(request, f"Category '{name}' already exists.")
    return redirect('admin_products')


def admin_customers_view(request):
    search_q = request.GET.get('q', '').strip()
    customers = User.objects.all().prefetch_related('orders').order_by('-date_joined')

    if search_q:
        customers = customers.filter(
            Q(username__icontains=search_q) |
            Q(email__icontains=search_q) |
            Q(first_name__icontains=search_q) |
            Q(last_name__icontains=search_q) |
            Q(phone__icontains=search_q)
        )

    # Compute spend per customer
    cust_data = []
    for c in customers:
        total_spent = c.orders.exclude(status='cancelled').aggregate(total=Sum('total_amount'))['total'] or 0
        cust_data.append({
            'user': c,
            'orders_count': c.orders.count(),
            'total_spent': f"{total_spent:,.2f}",
            'default_address': c.addresses.filter(is_default=True).first() or c.addresses.first(),
            'recent_orders': c.orders.all().order_by('-created_at')[:3]
        })

    paginator = Paginator(cust_data, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/customers.html', {
        'active_admin_tab': 'customers',
        'customers': page_obj,
        'page_obj': page_obj,
        'total_count': paginator.count,
        'search_query': search_q,
    })


def admin_promotions_view(request):
    coupons = Coupon.objects.all().order_by('-created_at')
    return render(request, 'admin/promotions.html', {
        'active_admin_tab': 'promotions',
        'coupons': coupons,
    })


def admin_create_promotion(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        title = request.POST.get('title', '').strip()
        discount_type = request.POST.get('discount_type', 'percentage')
        discount_value = request.POST.get('discount_value', 10)
        min_order = request.POST.get('min_order_amount', 0)
        
        if code and discount_value:
            Coupon.objects.create(
                code=code,
                title=title or f"{code} Special Discount",
                discount_type=discount_type,
                discount_value=discount_value,
                min_order_amount=min_order or 0,
                valid_from=timezone.now(),
                valid_until=timezone.now() + timezone.timedelta(days=90),
                is_active=True
            )
            messages.success(request, f"Promotion code '{code}' created successfully!")
    return redirect('admin_promotions')


def admin_edit_promotion(request, coupon_id):
    if request.method == 'POST':
        coupon = get_object_or_404(Coupon, id=coupon_id)
        coupon.code = request.POST.get('code', coupon.code).strip().upper()
        coupon.title = request.POST.get('title', coupon.title).strip()
        coupon.discount_type = request.POST.get('discount_type', coupon.discount_type)
        coupon.discount_value = request.POST.get('discount_value', coupon.discount_value)
        coupon.min_order_amount = request.POST.get('min_order_amount', coupon.min_order_amount)
        coupon.is_active = (request.POST.get('is_active') == 'on')
        coupon.save()
        messages.success(request, f"Promotion '{coupon.code}' updated successfully!")
    return redirect('admin_promotions')


def admin_delete_promotion(request, coupon_id):
    if request.method == 'POST':
        coupon = get_object_or_404(Coupon, id=coupon_id)
        code = coupon.code
        coupon.delete()
        messages.success(request, f"Promotion code '{code}' deleted.")
    return redirect('admin_promotions')


def admin_reports_view(request):
    products = Product.objects.all()
    return render(request, 'admin/reports.html', {
        'active_admin_tab': 'reports',
        'products': products,
    })


def admin_settings_view(request):
    if request.method == 'POST':
        store_name = request.POST.get('store_name')
        support_email = request.POST.get('support_email')
        free_shipping = request.POST.get('free_shipping_threshold')
        tax_rate = request.POST.get('tax_rate')
        
        request.session['store_settings'] = {
            'store_name': store_name,
            'support_email': support_email,
            'free_shipping_threshold': free_shipping,
            'tax_rate': tax_rate
        }
        messages.success(request, "Store settings and security policies updated successfully!")
        return redirect('admin_settings')

    settings_data = request.session.get('store_settings', {
        'store_name': 'QuickCart E-Commerce',
        'support_email': 'support@quickcart.com',
        'free_shipping_threshold': '999',
        'tax_rate': '5'
    })

    return render(request, 'admin/settings.html', {
        'active_admin_tab': 'settings',
        'settings_data': settings_data,
    })


def admin_support_view(request):
    status_filter = request.GET.get('status', 'all')
    msgs = SupportMessage.objects.all().order_by('-created_at')

    # Seed demo support inquiries if empty
    if not msgs.exists():
        SupportMessage.objects.create(
            name="Maya Thompson",
            email="maya@example.com",
            order_number="QC-78495",
            message="Hello, could you please confirm if my order will be delivered before Friday evening? I need it for a weekend trip.",
            is_resolved=False
        )
        SupportMessage.objects.create(
            name="Aarav Sharma",
            email="aarav.sharma@example.com",
            order_number="QC-90124",
            message="I would like to update my delivery address to Office address in Bengaluru. Please assist.",
            is_resolved=True
        )
        msgs = SupportMessage.objects.all().order_by('-created_at')

    if status_filter == 'pending':
        msgs = msgs.filter(is_resolved=False)
    elif status_filter == 'resolved':
        msgs = msgs.filter(is_resolved=True)

    paginator = Paginator(msgs, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/support.html', {
        'active_admin_tab': 'support',
        'messages_list': page_obj,
        'page_obj': page_obj,
        'total_count': paginator.count,
        'current_status': status_filter,
    })


def admin_resolve_support(request, message_id):
    if request.method == 'POST':
        msg = get_object_or_404(SupportMessage, id=message_id)
        msg.is_resolved = True
        msg.save()
        messages.success(request, f"Inquiry from {msg.name} marked as resolved!")
    return redirect('admin_support')


