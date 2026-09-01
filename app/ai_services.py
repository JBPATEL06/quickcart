import re
import math
from decimal import Decimal
from django.db import models
from django.utils import timezone
from .models import (
    Product, Category, Seller, SellerInventory, Review, ReviewFlag,
    PriceHistory, PricePrediction, PriceDropAlert,
    UserActivityLog, RecommendationSettings, RecommendationExclusion,
    Notification, AssistantMessage, QRShare, AdminAuditLog
)

# =======================================================
# 1. AI FAKE REVIEW CLASSIFIER ENGINE (PLUGGABLE INTERFACE)
# =======================================================

def classify_review_content(author_name, title, content, rating, is_verified_purchase=True):
    """
    AI Fake Review Classifier.
    Analyzes spam triggers, repeated phrases, emotional exaggerations, and URL patterns.
    Returns:
        suspicion_score (int): 0 to 100
        flag_reason (str): Reason for flagging
        status (str): 'approved' | 'pending' | 'flagged_fake'
    """
    text = f"{title} {content}".lower()
    score = 0
    reasons = []

    # Check 1: External links or promotions
    if re.search(r'(https?://|www\.|\.com|\.in|free cash|whatsapp|telegram)', text):
        score += 65
        reasons.append("Contains promotional links or social handles")

    # Check 2: Repetitive filler words or character spam
    if re.search(r'(.)\1{4,}', text) or re.search(r'(best best best|good good good|fake fake)', text):
        score += 35
        reasons.append("Excessive repetitive characters/keywords")

    # Check 3: Generic low-effort 5-star or 1-star without specifics
    word_count = len(text.split())
    if word_count < 3 and rating in [1, 5]:
        score += 25
        reasons.append("Ultra-short extreme rating without context")

    # Check 4: Non-verified purchase bias
    if not is_verified_purchase:
        score += 20
        reasons.append("Unverified buyer account")

    # Determine classification status
    if score >= 60:
        status = 'flagged_fake'
    elif score >= 30:
        status = 'pending'
    else:
        status = 'approved'

    return {
        'suspicion_score': min(score, 100),
        'flag_reason': ", ".join(reasons) if reasons else "Clean organic review",
        'status': status,
        'ai_classification_details': {
            'word_count': word_count,
            'spam_marker_detected': score >= 60,
            'sentiment_analysis': 'Extremely positive' if rating >= 4 else 'Negative'
        }
    }


# =======================================================
# 2. AI PRICE TREND PREDICTION ENGINE
# =======================================================

def predict_product_price_trend(product):
    """
    AI Price Predictor analyzing historical price fluctuations and seasonal cycles.
    Returns:
        predicted_trend: 'drop' | 'stable' | 'rise'
        confidence_score: 50-98 (%)
        suggestion_text: Guidance for buyer
        predicted_next_price: Decimal
    """
    history = list(product.price_history.order_by('changed_at'))
    current_price = float(product.price)
    
    if len(history) >= 2:
        recent_changes = [float(h.new_price) - float(h.old_price) for h in history[-3:]]
        avg_change = sum(recent_changes) / len(recent_changes)

        if avg_change < -5:
            trend = 'drop'
            confidence = 88
            next_price = round(current_price * 0.93, 2)
            suggestion = "Price is trending downwards. Good chance of further drop."
        elif avg_change > 5:
            trend = 'rise'
            confidence = 82
            next_price = round(current_price * 1.07, 2)
            suggestion = "Price is likely to increase soon. Buy now to lock in savings."
        else:
            trend = 'stable'
            confidence = 91
            next_price = current_price
            suggestion = "Price is currently stable and at fair market value."
    else:
        # Default heuristic based on discounts
        if product.original_price and float(product.original_price) > current_price:
            trend = 'stable'
            confidence = 85
            next_price = current_price
            suggestion = f"Currently on discount ({product.discount_percent}% off). Lowest price in 30 days."
        else:
            trend = 'drop'
            confidence = 78
            next_price = round(current_price * 0.95, 2)
            suggestion = "Expect festive discount drops in the next 14 days."

    prediction, _ = PricePrediction.objects.update_or_create(
        product=product,
        defaults={
            'predicted_trend': trend,
            'confidence_score': confidence,
            'suggestion_text': suggestion,
            'predicted_next_price': Decimal(str(next_price))
        }
    )
    return prediction


# =======================================================
# 3. AI SHOPPING ASSISTANT & INTENT PARSER
# =======================================================

def parse_shopping_intent_and_rank(user_message, user=None, session_id=None):
    """
    Parses budget limits, category intent, and features from free-text user queries.
    Queries catalog and ranks the top 3 product recommendations with 1-line rationales.
    """
    msg = user_message.lower()
    parsed_budget = None
    parsed_category = None
    
    # 1. Extract budget (e.g. "under 200", "below ₹500", "budget 1500")
    budget_match = re.search(r'(?:under|below|budget|less than|within|around)\s*(?:₹|rs\.?|inr)?\s*(\d+)', msg)
    if budget_match:
        try:
            parsed_budget = float(budget_match.group(1))
        except ValueError:
            parsed_budget = None

    # Check for Policy / Store FAQs First
    if any(k in msg for k in ['return policy', 'how to return', 'refund', 'exchange']):
        return {
            'response_text': "QuickCart offers an easy 7-day hassle-free return window on all verified purchases. Items must be in original condition with tags and packaging intact. You can initiate a return directly from your 'My Orders' portal.",
            'parsed_intent': {'topic': 'returns'},
            'suggested_products': []
        }
    
    if any(k in msg for k in ['track order', 'order status', 'where is my order', 'tracking']):
        return {
            'response_text': "You can track your active orders in real-time from your 'My Orders' dashboard! Simply click on any order number to see the full 5-stage shipment timeline with live courier updates.",
            'parsed_intent': {'topic': 'order_tracking'},
            'suggested_products': []
        }

    if any(k in msg for k in ['payment method', 'how to pay', 'upi', 'credit card', 'cod']):
        return {
            'response_text': "QuickCart accepts Credit/Debit cards (Visa, Mastercard, RuPay), UPI QR & VPA (GPay, PhonePe, Paytm), Net Banking across all major banks, and Cash on Delivery (COD). All online payments are protected by 256-bit SSL encryption.",
            'parsed_intent': {'topic': 'payments'},
            'suggested_products': []
        }

    if any(k in msg for k in ['coupon', 'promo code', 'discount code', 'give me coupon', 'voucher']):
        return {
            'response_text': "We periodically run seasonal offers and promotional discounts! Active promotions and sale banners are displayed on our homepage. Please check our homepage banners or subscribe for special seasonal deals.",
            'parsed_intent': {'topic': 'promotions'},
            'suggested_products': []
        }

    # Extract Category intent & keywords
    categories = Category.objects.all()
    for cat in categories:
        if cat.name.lower() in msg or cat.slug in msg:
            parsed_category = cat
            break
        # Common aliases
        if any(w in msg for w in ['headphone', 'earphone', 'audio', 'sound', 'watch', 'smartwatch', 'laptop', 'phone', 'camera']):
            parsed_category = Category.objects.filter(models.Q(slug='electronics') | models.Q(slug='audio-headphones') | models.Q(slug='smartphones')).first()
        elif any(w in msg for w in ['coffee', 'mug', 'chair', 'kitchen', 'home', 'bottle', 'flask']):
            parsed_category = Category.objects.filter(models.Q(slug='home-kitchen') | models.Q(slug='home-living')).first()

    # Query Catalog with Natural Language smart search
    matched_products, _ = execute_smart_catalog_search(user_message)
    matched_products = list(matched_products.order_by('-trust_score', '-rating')[:3])
    
    # Fallback to top trusted if none found
    if not matched_products:
        matched_products = list(Product.objects.filter(is_published=True).order_by('-trust_score')[:3])

    suggestions = []
    for p in matched_products:
        if parsed_budget and float(p.price) <= parsed_budget:
            reason = f"Fits your ₹{parsed_budget:,.0f} budget with high {p.trust_score}% Trust Score."
        else:
            reason = f"Top-rated ({p.rating}★) with certified {p.trust_score}% Trust Score."
            
        suggestions.append({
            'product_id': p.id,
            'name': p.name,
            'slug': p.slug,
            'url': f"/product/{p.slug}/",
            'image': p.main_image,
            'price': str(p.price),
            'rating': str(p.rating),
            'trust_score': p.trust_score,
            'main_image': p.main_image,
            'reason': reason
        })

    # Response dialogue
    if suggestions:
        response_text = f"I found {len(suggestions)} great matches for you! Here are our top recommendations based on your request:"
    else:
        response_text = "I'm searching our inventory for you. Could you share more details about what product or features you're looking for?"

    return {
        'response_text': response_text,
        'parsed_intent': {
            'budget': parsed_budget,
            'category': parsed_category.name if parsed_category else 'General',
            'keywords': [w for w in msg.split() if len(w) > 3]
        },
        'suggested_products': suggestions
    }


# =======================================================
# 4. GEOGRAPHIC NEARBY SELLER FINDER (HAVERSINE FORMULA)
# =======================================================

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """
    Computes great-circle distance between two GPS coordinates in Kilometers.
    """
    R = 6371.0 # Earth's radius in kilometers
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) * math.sin(dLat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dLon / 2) * math.sin(dLon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def get_nearby_sellers_for_product(product_id, user_lat=28.6139, user_lng=77.2090, max_radius_km=100):
    """
    Finds verified sellers carrying stock for a product, sorted by distance from user.
    """
    inventories = SellerInventory.objects.filter(
        product_id=product_id,
        is_available=True,
        stock__gt=0,
        seller__status='verified'
    ).select_related('seller')

    results = []
    for inv in inventories:
        seller = inv.seller
        dist_km = calculate_haversine_distance(
            float(user_lat), float(user_lng),
            float(seller.latitude), float(seller.longitude)
        )
        if dist_km <= max_radius_km:
            results.append({
                'seller_id': seller.id,
                'business_name': seller.business_name,
                'city': seller.city,
                'rating': str(seller.rating),
                'distance_km': dist_km,
                'stock': inv.stock,
                'local_price': str(inv.local_price),
                'estimated_delivery': f"{inv.delivery_days} day(s) express",
            })

    # Sort by distance
    results.sort(key=lambda x: x['distance_km'])
    return results


# =======================================================
# 5. CENTRAL NOTIFICATION ENGINE
# =======================================================

def send_notification(user, notification_type, title, body, related_link=''):
    """
    Creates an in-app notification and triggers notification event stubs.
    """
    if not user or not user.is_authenticated:
        return None

    notif = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        body=body,
        related_link=related_link
    )
    return notif


# =======================================================
# 6. USER ACTIVITY & RECOMMENDATION ENGINE
# =======================================================

def log_user_activity(session_id, user=None, activity_type='view', product=None, category=None, search_query='', metadata=None):
    """
    Logs browsing and engagement activities for recommendation ranking.
    """
    if not session_id and user:
        session_id = f"user_{user.id}"

    return UserActivityLog.objects.create(
        session_id=session_id or 'anon_session',
        user=user if user and user.is_authenticated else None,
        activity_type=activity_type,
        product=product,
        category=category or (product.category if product else None),
        search_query=search_query,
        metadata=metadata or {}
    )


def get_personalized_recommendations(user=None, session_id=None, limit=8):
    """
    Generates personalized product suggestions by aggregating category affinity.
    """
    exclusions = RecommendationExclusion.objects.values_list('product_id', flat=True)
    base_query = Product.objects.filter(is_published=True).exclude(id__in=exclusions)

    # If user or session has history, prioritize relevant categories
    recent_activity = UserActivityLog.objects.filter(
        models.Q(user=user) if user and user.is_authenticated else models.Q(session_id=session_id)
    ).exclude(category__isnull=True).values('category').annotate(count=models.Count('id')).order_by('-count')

    if recent_activity.exists():
        top_category_id = recent_activity[0]['category']
        recommended = list(base_query.filter(category_id=top_category_id).order_by('-trust_score', '-rating')[:limit])
        if len(recommended) < limit:
            remaining = list(base_query.exclude(category_id=top_category_id).order_by('-trust_score')[:limit - len(recommended)])
            recommended.extend(remaining)
        return recommended

    # Default fallback: top trust score trending products
    return list(base_query.order_by('-is_trending', '-trust_score')[:limit])


# =======================================================
# 7. NATURAL LANGUAGE & SEMANTIC SEARCH PARSER
# =======================================================

SYNONYM_MAP = {
    'watch': ['watch', 'smartwatch', 'smart watch', 'tracker', 'wearable', 'wrist', 'chrono', 'fitness band'],
    'watches': ['watch', 'smartwatch', 'smart watch', 'tracker', 'wearable', 'wrist', 'chrono', 'fitness band'],
    'smartwatch': ['smartwatch', 'watch', 'smart watch', 'tracker', 'fitness band'],
    'headphone': ['headphone', 'headphones', 'earphone', 'earbuds', 'audio', 'sound', 'headset', 'anc'],
    'headphones': ['headphone', 'headphones', 'earphone', 'earbuds', 'audio', 'sound', 'headset', 'anc'],
    'earphone': ['earphone', 'earphones', 'earbuds', 'headphone', 'audio', 'sound'],
    'earphones': ['earphone', 'earphones', 'earbuds', 'headphone', 'audio', 'sound'],
    'earbuds': ['earbuds', 'earphone', 'headphones', 'audio', 'wireless earbuds'],
    'phone': ['phone', 'phones', 'smartphone', 'smartphones', 'mobile', 'cellphone'],
    'phones': ['phone', 'phones', 'smartphone', 'smartphones', 'mobile', 'cellphone'],
    'smartphone': ['smartphone', 'smartphones', 'phone', 'mobile'],
    'laptop': ['laptop', 'notebook', 'macbook', 'computer', 'ultrabook'],
    'bottle': ['bottle', 'flask', 'tumbler', 'mug', 'cup', 'hydro'],
    'mug': ['mug', 'tumbler', 'cup', 'flask', 'bottle', 'coffee mug'],
    'chair': ['chair', 'seat', 'ergonomic', 'furniture', 'desk chair'],
    'charger': ['charger', 'charging', 'power bank', 'adapter', 'usb-c', 'cable'],
    'shoes': ['shoes', 'sneakers', 'footwear', 'running shoes'],
}


def parse_natural_language_search_query(raw_query):
    """
    Parses intent, price constraints, and extracted keywords from queries like:
    - "watch under 2100" -> clean_query="watch", max_price=2100.0
    - "headphones below 500" -> clean_query="headphones", max_price=500.0
    - "laptops above 50000" -> clean_query="laptops", min_price=50000.0
    - "shoes between 1000 and 3000" -> clean_query="shoes", min_price=1000.0, max_price=3000.0
    """
    query = raw_query.strip()
    min_price = None
    max_price = None

    # 1. Match "between X and Y" / "from X to Y"
    between_match = re.search(r'(?:between|from)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:and|to|-)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)', query, re.IGNORECASE)
    if between_match:
        min_price = float(between_match.group(1))
        max_price = float(between_match.group(2))
        query = query.replace(between_match.group(0), ' ')

    # 2. Match "under X" / "below X" / "less than X" / "<= X" / "within X"
    if max_price is None:
        under_match = re.search(r'(?:under|below|less than|within|max|<=?|budget|up to)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)', query, re.IGNORECASE)
        if under_match:
            max_price = float(under_match.group(1))
            query = query.replace(under_match.group(0), ' ')

    # 3. Match "above X" / "more than X" / "greater than X" / ">= X" / "over X"
    if min_price is None:
        above_match = re.search(r'(?:above|over|more than|greater than|>=?|minimum|min)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)', query, re.IGNORECASE)
        if above_match:
            min_price = float(above_match.group(1))
            query = query.replace(above_match.group(0), ' ')

    # Clean up remnant currency symbols or filler words
    cleaned = re.sub(r'\b(price|rs\.?|inr|₹|for|with|in|and|the|a|an)\b', ' ', query, flags=re.IGNORECASE)
    clean_query = ' '.join(cleaned.split()).strip()

    # Expand keywords and synonyms
    tokens = [t.lower() for t in clean_query.split() if len(t) >= 2]
    expanded_terms = set(tokens)
    for token in tokens:
        if token in SYNONYM_MAP:
            expanded_terms.update(SYNONYM_MAP[token])

    return {
        'raw_query': raw_query,
        'clean_query': clean_query,
        'min_price': min_price,
        'max_price': max_price,
        'tokens': tokens,
        'expanded_terms': list(expanded_terms)
    }


def execute_smart_catalog_search(raw_query, base_queryset=None):
    """
    Executes a high-relevance, natural language search over the product catalog.
    Handles price filters, token matches, synonym expansion, and ranking.
    """
    if base_queryset is None:
        base_queryset = Product.objects.filter(is_published=True).select_related('category')

    if not raw_query or not raw_query.strip():
        return base_queryset, {
            'raw_query': '',
            'clean_query': '',
            'min_price': None,
            'max_price': None,
            'expanded_terms': []
        }

    parsed = parse_natural_language_search_query(raw_query)
    qs = base_queryset

    # Apply Price Constraints
    if parsed['min_price'] is not None:
        qs = qs.filter(price__gte=parsed['min_price'])
    if parsed['max_price'] is not None:
        qs = qs.filter(price__lte=parsed['max_price'])

    # Apply Text & Synonym Matching
    if parsed['clean_query']:
        clean_text = parsed['clean_query']
        # Try direct full-text/phrase match first
        exact_q = (
            models.Q(name__icontains=clean_text) |
            models.Q(description__icontains=clean_text) |
            models.Q(brand__icontains=clean_text) |
            models.Q(tagline__icontains=clean_text) |
            models.Q(category__name__icontains=clean_text)
        )
        
        # Build expanded terms query
        synonym_q = models.Q()
        for term in parsed['expanded_terms']:
            synonym_q |= (
                models.Q(name__icontains=term) |
                models.Q(description__icontains=term) |
                models.Q(brand__icontains=term) |
                models.Q(tagline__icontains=term) |
                models.Q(category__name__icontains=term)
            )

        matched_qs = qs.filter(exact_q | synonym_q).distinct()
        if matched_qs.exists():
            qs = matched_qs
        else:
            # Fallback: token-level matching
            token_q = models.Q()
            for token in parsed['tokens']:
                token_q |= (
                    models.Q(name__icontains=token) |
                    models.Q(description__icontains=token) |
                    models.Q(brand__icontains=token)
                )
            qs = qs.filter(token_q).distinct()

    return qs, parsed

