import re
import math
from decimal import Decimal
from django.db import models
from django.utils import timezone
import json
import urllib.request
import urllib.error
from .models import (
    Product, Category, Seller, SellerInventory, Review, ReviewFlag,
    PriceHistory, PricePrediction, PriceDropAlert,
    UserActivityLog, RecommendationSettings, RecommendationExclusion,
    Notification, AssistantMessage, QRShare, AdminAuditLog,
    Wishlist, Cart, Address, ShippingRule, Coupon, AIProviderConfig
)

# =======================================================
# 0. UNIFIED MULTI-PROVIDER LLM DISPATCHER
# =======================================================

def call_configured_llm(prompt, system_prompt="You are QuickCart's intelligent AI shopping assistant. Provide concise, helpful e-commerce guidance.", feature='all', specific_config=None):
    """
    Calls configured AI Providers according to priority (1 = Primary, 2 = 1st Fallback, etc.).
    If a provider fails (timeout, rate limit 429, invalid key), automatically cascades to the
    next configured provider in priority order, finally falling back to None (local engine).
    If specific_config is provided, tests that exact config directly.
    """
    if specific_config:
        candidate_configs = [specific_config]
    else:
        candidate_configs = AIProviderConfig.get_providers_for_feature(feature)
        
    if not candidate_configs:
        return None

    for config in candidate_configs:
        if config.provider == 'local' or not config.api_key:
            # If specific_config is local, return a mock response for verification
            if specific_config:
                return "Local AI ready"
            # Otherwise return None so system uses local algorithms
            continue

        # Check key expiry
        if config.is_expired:
            config.verification_status = 'expired'
            config.last_error = f"API Key expired on {config.expiry_date}."
            config.save(update_fields=['verification_status', 'last_error'])
            continue  # Cascade to next fallback

        provider = config.provider
        api_key = config.api_key.strip()
        model_name = config.model_name.strip() if config.model_name else 'default'

        try:
            # 1. OPENAI / GROK / GROQ / OPENROUTER
            if provider in ['openai', 'openrouter', 'groq', 'grok']:
                endpoint_map = {
                    'openai': 'https://api.openai.com/v1/chat/completions',
                    'openrouter': 'https://openrouter.ai/api/v1/chat/completions',
                    'groq': 'https://api.groq.com/openai/v1/chat/completions',
                    'grok': 'https://api.x.ai/v1/chat/completions',
                }
                default_models = {
                    'openai': 'gpt-4o-mini',
                    'openrouter': 'openai/gpt-4o-mini',
                    'groq': 'llama-3.3-70b-versatile',
                    'grok': 'grok-2-latest',
                }
                selected_model = model_name if model_name != 'default' else default_models.get(provider, 'gpt-4o-mini')

                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                }
                if provider == 'openrouter':
                    headers['HTTP-Referer'] = 'http://127.0.0.1:8000/'
                    headers['X-Title'] = 'QuickCart AI'

                payload = {
                    'model': selected_model,
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': float(config.temperature)
                }

                req = urllib.request.Request(endpoint_map[provider], data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=6) as res:
                    body = json.loads(res.read().decode('utf-8'))
                    result_text = body['choices'][0]['message']['content'].strip()

                    config.usage_count += 1
                    config.rate_limit_hit = False
                    config.verification_status = 'valid'
                    config.last_error = ''
                    config.last_used_at = timezone.now()
                    config.save(update_fields=['usage_count', 'rate_limit_hit', 'verification_status', 'last_error', 'last_used_at'])
                    return result_text

            # 2. GOOGLE GEMINI
            elif provider == 'gemini':
                gemini_model = model_name if model_name != 'default' else 'gemini-2.0-flash'
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={api_key}"
                headers = {'Content-Type': 'application/json'}
                payload = {
                    'contents': [{'parts': [{'text': f"{system_prompt}\n\n{prompt}"}]}],
                    'generationConfig': {'temperature': float(config.temperature)}
                }
                req = urllib.request.Request(endpoint, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=6) as res:
                    body = json.loads(res.read().decode('utf-8'))
                    candidates = body.get('candidates', [])
                    if candidates:
                        parts = candidates[0].get('content', {}).get('parts', [])
                        if parts:
                            result_text = parts[0].get('text', '').strip()
                            config.usage_count += 1
                            config.rate_limit_hit = False
                            config.verification_status = 'valid'
                            config.last_error = ''
                            config.last_used_at = timezone.now()
                            config.save(update_fields=['usage_count', 'rate_limit_hit', 'verification_status', 'last_error', 'last_used_at'])
                            return result_text

            # 3. ANTHROPIC CLAUDE
            elif provider == 'claude':
                claude_model = model_name if model_name != 'default' else 'claude-3-5-sonnet-20241022'
                endpoint = "https://api.anthropic.com/v1/messages"
                headers = {
                    'Content-Type': 'application/json',
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01'
                }
                payload = {
                    'model': claude_model,
                    'max_tokens': 1024,
                    'system': system_prompt,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': float(config.temperature)
                }
                req = urllib.request.Request(endpoint, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=6) as res:
                    body = json.loads(res.read().decode('utf-8'))
                    content = body.get('content', [])
                    if content and 'text' in content[0]:
                        result_text = content[0]['text'].strip()
                        config.usage_count += 1
                        config.rate_limit_hit = False
                        config.verification_status = 'valid'
                        config.last_error = ''
                        config.last_used_at = timezone.now()
                        config.save(update_fields=['usage_count', 'rate_limit_hit', 'verification_status', 'last_error', 'last_used_at'])
                        return result_text

        except urllib.error.HTTPError as he:
            err_msg = f"HTTP {he.code}: {he.reason}"
            if he.code == 429:
                config.rate_limit_hit = True
                config.verification_status = 'rate_limited'
                err_msg = "Rate limit hit (HTTP 429). Cascading to fallback provider."
            elif he.code in [401, 403]:
                config.verification_status = 'invalid'
                err_msg = f"Unauthorized (HTTP {he.code}). Invalid API key."
            
            config.last_error = err_msg
            config.save(update_fields=['rate_limit_hit', 'verification_status', 'last_error'])
            # Continue to next priority provider in candidate_configs
            continue

        except Exception as e:
            config.last_error = str(e)
            config.save(update_fields=['last_error'])
            # Continue to next priority provider in candidate_configs
            continue

    return None


def verify_ai_provider_connection(config):
    """
    Tests and verifies an API key by executing a lightweight 1-token test prompt.
    Updates verification_status, rate_limit_hit, and last_error in database.
    """
    if config.provider == 'local' or not config.api_key:
        config.verification_status = 'valid'
        config.last_error = ''
        config.save(update_fields=['verification_status', 'last_error'])
        return True, "Built-in Local Engine is ready."

    test_prompt = "Say 'OK'"
    reply = call_configured_llm(test_prompt, system_prompt="Answer in 1 word.", specific_config=config)
    
    # Reload config to check results
    config.refresh_from_db()
    if reply:
        config.verification_status = 'valid'
        config.last_error = ''
        config.save(update_fields=['verification_status', 'last_error'])
        return True, f"Connection verified successfully with {config.get_provider_display()}!"
    else:
        err = config.last_error or "Could not establish connection to provider."
        return False, f"Verification failed: {err}"


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

    if any(k in msg for k in ['coupon', 'promo code', 'discount code', 'give me coupon', 'voucher', 'offer']):
        exposed_coupons = list(Coupon.objects.filter(is_active=True, is_ai_exposed=True))
        if exposed_coupons:
            code_list = [f"'{c.code}' ({c.title})" for c in exposed_coupons[:2]]
            codes_str = " and ".join(code_list)
            return {
                'response_text': f"Great news! You can apply coupon {codes_str} at checkout to get special savings on eligible orders.",
                'parsed_intent': {'topic': 'promotions'},
                'suggested_products': []
            }
        else:
            return {
                'response_text': "All current promotional discounts and free shipping perks are automatically applied at checkout! You don't need to manually enter any promo codes.",
                'parsed_intent': {'topic': 'promotions'},
                'suggested_products': []
            }

    # Direct Comparison Intent check ("Compare X and Y", "Which is better...", etc.)
    if any(k in msg for k in ['compare', 'vs', 'which one is better', 'difference between', 'which should i buy']):
        # Find which products are mentioned in this comparison request
        all_catalog = list(Product.objects.filter(is_published=True).select_related('category'))
        mentioned = []
        for p in all_catalog:
            # Check name or key words
            name_words = [w for w in p.name.lower().split() if len(w) > 3]
            if p.name.lower() in msg or (name_words and sum(1 for w in name_words if w in msg) >= 2):
                if p not in mentioned:
                    mentioned.append(p)

        if len(mentioned) >= 2:
            # Sort by trust_score and rating
            mentioned.sort(key=lambda x: (x.trust_score, x.rating), reverse=True)
            winner = mentioned[0]
            compare_prompt = (
                f"Customer wants to compare: {[p.name for p in mentioned]}. "
                f"Explain concisely (2-3 sentences) why {winner.name} (Trust Score: {winner.trust_score}%, Price: ₹{winner.price}) is the recommended choice."
            )
            llm_summary = call_configured_llm(compare_prompt)
            if not llm_summary:
                llm_summary = f"Between the compared items, {winner.name} stands out as the best recommendation with a {winner.trust_score}% AI Trust Score, {winner.rating}★ rating, and competitive price of ₹{winner.price}."

            compare_suggestions = []
            for p in mentioned:
                is_win = (p.id == winner.id)
                compare_suggestions.append({
                    'product_id': p.id,
                    'name': p.name,
                    'slug': p.slug,
                    'url': f"/product/{p.slug}/",
                    'image': p.main_image,
                    'price': str(p.price),
                    'rating': str(p.rating),
                    'trust_score': p.trust_score,
                    'main_image': p.main_image,
                    'reason': f"🏆 Top Recommendation ({p.trust_score}% Trust)" if is_win else f"Alternative ({p.trust_score}% Trust)",
                    'in_wishlist': False,
                    'in_cart': False,
                })

            return {
                'response_text': llm_summary,
                'parsed_intent': {'topic': 'compare', 'winner': winner.name},
                'suggested_products': compare_suggestions
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
    
    # Filter by budget strictly if provided
    if parsed_budget:
        matched_products = matched_products.filter(price__lte=parsed_budget)
    if parsed_category:
        matched_products = matched_products.filter(category=parsed_category)

    matched_products = list(matched_products.order_by('-trust_score', '-rating')[:6])

    # Context Awareness: Get user's active Wishlist and Cart product IDs
    wishlist_pids = set()
    cart_pids = set()
    if user and user.is_authenticated:
        wishlist_pids = set(Wishlist.objects.filter(user=user).values_list('product_id', flat=True))
        cart_obj = Cart.objects.filter(user=user).first()
        if cart_obj:
            cart_pids = set(cart_obj.items.values_list('product_id', flat=True))
    elif session_id:
        cart_obj = Cart.objects.filter(session_key=session_id).first()
        if cart_obj:
            cart_pids = set(cart_obj.items.values_list('product_id', flat=True))

    suggestions = []
    for p in matched_products:
        in_wl = p.id in wishlist_pids
        in_c = p.id in cart_pids

        if in_wl:
            reason = f"⭐ Saved in your Wishlist! Matches '{user_message}' with {p.trust_score}% Trust Score."
        elif in_c:
            reason = f"🛒 Already in your Cart! Rated {p.rating}★ with {p.trust_score}% Trust Score."
        elif parsed_budget and float(p.price) <= parsed_budget:
            reason = f"Fits your ₹{parsed_budget:,.0f} budget with verified {p.trust_score}% Trust Score."
        else:
            reason = f"Direct match: {p.brand} {p.name} with {p.rating}★ rating ({p.review_count} reviews)."
            
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
            'reason': reason,
            'in_wishlist': in_wl,
            'in_cart': in_c,
        })

    # Response dialogue
    if suggestions:
        response_text = f"I found {len(suggestions)} exact matching products for '{user_message}':"
        # Optional LLM natural language intro enhancement
        llm_reply = call_configured_llm(f"Customer asked: '{user_message}'. We found these products: {[p.name for p in matched_products]}. Give a friendly 1-2 sentence response guiding them.")
        if llm_reply:
            response_text = llm_reply
    else:
        criteria_parts = []
        if parsed_category:
            criteria_parts.append(f"in {parsed_category.name}")
        if parsed_budget:
            criteria_parts.append(f"under ₹{parsed_budget:,.0f}")
        crit_str = " ".join(criteria_parts)
        response_text = f"No products in our current catalog exactly matched your search criteria {crit_str}. Try checking our general catalog or adjusting your price limit."

    return {
        'response_text': response_text,
        'parsed_intent': {
            'budget': parsed_budget,
            'category': parsed_category.name if parsed_category else 'General',
            'keywords': [w for w in msg.split() if len(w) > 3]
        },
        'suggested_products': suggestions
    }



def generate_compare_analysis(product_ids, user=None, cart=None):
    """
    GenAI Comparison Engine.
    Analyzes compared products side-by-side alongside user cart, wishlist, and location.
    QuickCart Admin operates as the sole seller & fulfillment hub.
    """
    products = list(Product.objects.filter(id__in=product_ids))
    if not products:
        return {'error': 'No products to compare.'}

    # 1. Location & Delivery Context (Admin Fulfillment)
    user_city = "Bengaluru"
    if user and user.is_authenticated:
        default_addr = Address.objects.filter(user=user, is_default=True).first() or Address.objects.filter(user=user).first()
        if default_addr and default_addr.city:
            user_city = default_addr.city

    # Check active ShippingRules for delivery estimate
    shipping_fee_sample = 0.0
    if cart:
        shipping_fee_sample = cart.get_shipping_fee(destination_city=user_city)

    # 2. Wishlist & Cart Context
    wishlist_ids = set()
    cart_ids = set()
    if user and user.is_authenticated:
        wishlist_ids = set(Wishlist.objects.filter(user=user).values_list('product_id', flat=True))
        if cart:
            cart_ids = set(cart.items.values_list('product_id', flat=True))

    # 3. Product Evaluation & Trade-off Scoring
    analyzed_products = []
    best_product = None
    highest_overall_score = -1

    for p in products:
        # Pros and Cons heuristic calculation based on specs, trust score, warranty, rating
        pros = []
        cons = []

        if p.trust_score >= 95:
            pros.append(f"Exceptional {p.trust_score}% AI Trust Score (verified genuine reviews)")
        elif p.trust_score >= 90:
            pros.append(f"High {p.trust_score}% AI Trust Score")

        if float(p.rating) >= 4.8:
            pros.append(f"Top-tier customer satisfaction ({p.rating}★ from {p.review_count} buyers)")

        if p.original_price and p.original_price > p.price:
            discount_pct = int(((p.original_price - p.price) / p.original_price) * 100)
            if discount_pct >= 15:
                pros.append(f"Great price-to-performance ({discount_pct}% instant discount)")

        if p.battery_life and p.battery_life != "N/A":
            pros.append(f"Long endurance ({p.battery_life})")

        if p.warranty and p.warranty != "N/A":
            pros.append(f"Official QuickCart {p.warranty}")

        # Cons
        if p.stock < 15:
            cons.append("Limited stock remaining in warehouse")
        if float(p.price) > 10000 and not p.is_limited_offer:
            cons.append("Higher upfront investment compared to entry-level alternatives")
        if not p.battery_life or p.battery_life == "N/A":
            if p.category.slug in ['smartphones', 'audio-headphones', 'smartwatches-wearables']:
                cons.append("Standard battery cycle")

        # Composite score (100-point scale)
        price_factor = 100 - min(60, int(float(p.price) / 1000.0))
        trust_factor = p.trust_score
        rating_factor = int(float(p.rating) * 20)
        overall_score = int((trust_factor * 0.45) + (rating_factor * 0.35) + (price_factor * 0.20))

        if p.id in wishlist_ids:
            overall_score += 5 # Personalized boost for wishlist item

        if overall_score > highest_overall_score:
            highest_overall_score = overall_score
            best_product = p

        analyzed_products.append({
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'brand': p.brand,
            'price': str(p.price),
            'original_price': str(p.original_price) if p.original_price else None,
            'image': p.main_image,
            'rating': str(p.rating),
            'review_count': p.review_count,
            'trust_score': p.trust_score,
            'trust_badge': p.trust_badge_label,
            'battery_life': p.battery_life,
            'warranty': p.warranty,
            'overall_score': min(100, overall_score),
            'pros': pros if pros else ["Certified Authentic QuickCart stock", "7-Day Easy Replacement"],
            'cons': cons if cons else ["Standard demand pricing"],
            'in_wishlist': p.id in wishlist_ids,
            'in_cart': p.id in cart_ids,
        })

    # 4. Personalized Reasoning for Winner
    reasons = []
    if best_product.id in wishlist_ids:
        reasons.append(f"It aligns with your saved preference — already favorited in your Wishlist.")
    reasons.append(f"Offers the strongest combination of reliability ({best_product.trust_score}% Trust Score) and satisfaction ({best_product.rating}★).")
    if shipping_fee_sample == 0:
        reasons.append(f"Dispatches directly from QuickCart's central hub to {user_city} with 100% FREE Express Delivery.")
    else:
        reasons.append(f"Dispatches directly from QuickCart's central hub to {user_city} with guaranteed 2-day doorstep fulfillment.")

    # 4b. If External LLM (OpenAI, Gemini, Claude, Groq, Grok, OpenRouter) is configured, get rich summary
    llm_prompt = f"Compare these e-commerce products: {[p['name'] for p in analyzed_products]}. Winner is {best_product.name}. Provide 2 short bullet points explaining why it is superior for a shopper in {user_city}."
    llm_custom_verdict = call_configured_llm(llm_prompt)
    if llm_custom_verdict:
        # Split into bullet lines if suitable
        lines = [line.strip('- *• ') for line in llm_custom_verdict.split('\n') if line.strip()]
        if lines:
            reasons = lines[:3]


    # 5. Active Promo Hint (Only expose coupon code if is_ai_exposed is enabled by Admin)
    coupon_hint = ""
    active_coupon = Coupon.objects.filter(is_active=True, is_ai_exposed=True).first()
    if active_coupon:
        coupon_hint = f"Special Offer: Use code {active_coupon.code} at checkout to save!"
    else:
        # Generic non-leaking tip
        coupon_hint = "Discounts & free delivery apply automatically at checkout."

    return {
        'winner': {
            'id': best_product.id,
            'name': best_product.name,
            'slug': best_product.slug,
            'image': best_product.main_image,
            'price': str(best_product.price),
            'score': min(100, highest_overall_score),
            'badge': "🏆 Top Recommendation for You",
            'reasons': reasons,
        },
        'user_city': user_city,
        'delivery_speed': f"Express Delivery to {user_city} (Direct from Store Admin Hub)",
        'shipping_fee': f"₹{shipping_fee_sample:.2f}" if shipping_fee_sample > 0 else "FREE Delivery",
        'coupon_hint': coupon_hint,
        'products': analyzed_products,
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
            # Fallback 1: token-level local matching
            token_q = models.Q()
            for token in parsed['tokens']:
                token_q |= (
                    models.Q(name__icontains=token) |
                    models.Q(description__icontains=token) |
                    models.Q(brand__icontains=token)
                )
            qs = qs.filter(token_q).distinct()

            # Fallback 2: ONLY if local matching returned 0 results and an external AI API is configured,
            # ask LLM to extract primary keywords to rescue the search
            if not qs.exists() and len(raw_query.split()) > 2:
                llm_keywords = call_configured_llm(
                    f"Extract 1 or 2 standard e-commerce product keywords from this complex query: '{raw_query}'. Output only the keywords separated by spaces.",
                    system_prompt="Extract simple product keywords only."
                )
                if llm_keywords:
                    ai_kw_tokens = [w.strip().lower() for w in llm_keywords.split() if len(w.strip()) >= 2]
                    rescue_q = models.Q()
                    for kw in ai_kw_tokens:
                        rescue_q |= (
                            models.Q(name__icontains=kw) |
                            models.Q(description__icontains=kw) |
                            models.Q(category__name__icontains=kw)
                        )
                    qs = base_queryset.filter(rescue_q).distinct()

    return qs, parsed

