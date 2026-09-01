import os
import sys
import django
from decimal import Decimal

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quickcart_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from app.models import (
    Address, Category, Product, ProductImage, Review, Wishlist,
    Cart, CartItem, Order, OrderItem, OrderTrackingEvent, FAQItem
)
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def run():
    print("[*] Seeding QuickCart Database...")

    # 1. Create Default Customer Account (Maya Thompson matching Flowstep UI)
    maya, created = User.objects.get_or_create(
        username='maya@example.com',
        email='maya@example.com',
        defaults={
            'first_name': 'Maya',
            'last_name': 'Thompson',
            'phone': '+91 98765 43210',
            'theme_mode': 'light',
            'email_notifications': True,
            'order_updates': True,
            'marketing_emails': False,
        }
    )
    if created or not maya.has_usable_password():
        maya.set_password('password123')
        maya.save()
    print("[+] User Maya Thompson created (maya@example.com / password123)")

    # 2. Addresses for Maya
    Address.objects.get_or_create(
        user=maya,
        label='home',
        defaults={
            'recipient_name': 'Maya Thompson',
            'street_address': '42 Silver Oak Avenue, Koramangala',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'postal_code': '560034',
            'country': 'India',
            'phone': '+91 98765 43210',
            'is_default': True,
        }
    )
    Address.objects.get_or_create(
        user=maya,
        label='work',
        defaults={
            'recipient_name': 'Maya Thompson (Office)',
            'street_address': 'TechPark Tower B, 4th Floor, Whitefield',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'postal_code': '560066',
            'country': 'India',
            'phone': '+91 98765 43210',
            'is_default': False,
        }
    )
    print("[+] Addresses created.")

    # 3. Categories matching Flowstep design
    categories_data = [
        {'name': 'Electronics', 'slug': 'electronics', 'icon_name': 'bi-laptop', 'order': 1},
        {'name': 'Audio & Headphones', 'slug': 'audio-headphones', 'icon_name': 'bi-headphones', 'order': 2},
        {'name': 'Smartphones', 'slug': 'smartphones', 'icon_name': 'bi-phone', 'order': 3},
        {'name': 'Home & Kitchen', 'slug': 'home-kitchen', 'icon_name': 'bi-house-door', 'order': 4},
        {'name': 'Fashion & Apparel', 'slug': 'fashion', 'icon_name': 'bi-bag', 'order': 5},
        {'name': 'Health & Wellness', 'slug': 'wellness', 'icon_name': 'bi-heart-pulse', 'order': 6},
    ]

    cat_map = {}
    for c in categories_data:
        cat_obj, _ = Category.objects.get_or_create(
            slug=c['slug'],
            defaults={'name': c['name'], 'icon_name': c['icon_name'], 'order': c['order']}
        )
        cat_map[c['slug']] = cat_obj
    print("[+] Categories seeded.")

    # 4. Products matching Flowstep design screens
    products_data = [
        {
            'name': 'AeroSound Pro Wireless Headphones',
            'slug': 'aerosound-pro-wireless-headphones',
            'category': cat_map['audio-headphones'],
            'brand': 'AeroSound',
            'tagline': 'Studio-grade sound with adaptive noise cancellation.',
            'description': 'Designed for deep focus and effortless listening, AeroSound Pro combines studio-grade sound with adaptive noise cancellation. The lightweight frame and plush memory-foam cushions stay comfortable all day.',
            'price': Decimal('129.00'),
            'original_price': Decimal('179.00'),
            'trust_score': 92,
            'trust_badge_label': 'Trusted',
            'stock': 45,
            'main_image': 'https://images.unsplash.com/photo-1723961617032-ef69c454cb31?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=600',
            'rating': Decimal('4.8'),
            'review_count': 248,
            'battery_life': '40 hours',
            'connectivity': 'Bluetooth 5.3',
            'warranty': '1 year warranty',
            'specifications': {
                'Battery Life': '40 hours',
                'Connectivity': 'Bluetooth 5.3 + 3.5mm Aux',
                'Noise Cancellation': 'Active Hybrid ANC',
                'Weight': '245 grams',
                'Drivers': '40mm Custom Dynamic',
                'Charging': 'USB-C Fast Charge (10 min = 4h)'
            },
            'is_trending': True,
            'is_limited_offer': True,
        },
        {
            'name': 'SonicBlast Ultra ANC Headset',
            'slug': 'sonicblast-ultra-anc-headset',
            'category': cat_map['audio-headphones'],
            'brand': 'SonicBlast',
            'tagline': 'High fidelity audio with 50-hour ultra battery.',
            'description': 'Immerse yourself in rich acoustics, deep bass, and crystal clear phone calls with SonicBlast Ultra ANC Headset.',
            'price': Decimal('149.00'),
            'original_price': Decimal('199.00'),
            'trust_score': 95,
            'trust_badge_label': 'Top Rated',
            'stock': 30,
            'main_image': 'https://images.unsplash.com/photo-1638803782506-d975a6809f43?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=600',
            'rating': Decimal('4.9'),
            'review_count': 512,
            'battery_life': '50 hours',
            'connectivity': 'Bluetooth 5.3',
            'warranty': '2 years warranty',
            'specifications': {
                'Battery Life': '50 hours',
                'Connectivity': 'Bluetooth 5.3',
                'Noise Cancellation': 'Smart Adaptive ANC 2.0',
                'Weight': '260 grams',
                'Drivers': '45mm Neodymium',
                'Charging': 'USB-C Fast Charge'
            },
            'is_trending': True,
            'is_limited_offer': False,
        },
        {
            'name': 'BassPulse Ergonomic Earbuds',
            'slug': 'basspulse-ergonomic-earbuds',
            'category': cat_map['audio-headphones'],
            'brand': 'BassPulse',
            'tagline': 'True wireless earbuds with punchy bass and water resistance.',
            'description': 'Compact, sweat-proof, and designed for workouts and daily commutes. Features touch controls and environmental noise cancelling microphones.',
            'price': Decimal('69.00'),
            'original_price': Decimal('89.00'),
            'trust_score': 88,
            'trust_badge_label': 'Verified',
            'stock': 60,
            'main_image': 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=600',
            'rating': Decimal('4.6'),
            'review_count': 180,
            'battery_life': '32 hours (with case)',
            'connectivity': 'Bluetooth 5.2',
            'warranty': '1 year warranty',
            'specifications': {
                'Battery Life': '32 hours total',
                'Water Resistance': 'IPX5 Water Resistant',
                'Connectivity': 'Bluetooth 5.2',
                'Weight': '4.2 grams per bud'
            },
            'is_trending': True,
            'is_limited_offer': False,
        },
        {
            'name': 'NovaBook Pro 15 Laptop',
            'slug': 'novabook-pro-15-laptop',
            'category': cat_map['electronics'],
            'brand': 'NovaTech',
            'tagline': 'Powerhouse productivity with OLED 120Hz display.',
            'description': 'Engineered for creators and professionals with Intel Core Ultra processor, 32GB RAM, and razor-sharp OLED display.',
            'price': Decimal('1199.00'),
            'original_price': Decimal('1399.00'),
            'trust_score': 96,
            'trust_badge_label': 'Top Rated',
            'stock': 15,
            'main_image': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=600',
            'rating': Decimal('4.9'),
            'review_count': 142,
            'battery_life': '14 hours',
            'connectivity': 'Wi-Fi 6E, Thunderbolt 4',
            'warranty': '2 years on-site',
            'specifications': {
                'Processor': 'Intel Core Ultra 7 155H',
                'RAM': '32GB LPDDR5X',
                'Storage': '1TB NVMe Gen4 SSD',
                'Display': '15.6" 2.8K OLED 120Hz',
                'Weight': '1.58 kg'
            },
            'is_trending': True,
            'is_limited_offer': True,
        },
        {
            'name': 'UltraVision 4K Smart Monitor 27"',
            'slug': 'ultravision-4k-smart-monitor',
            'category': cat_map['electronics'],
            'brand': 'UltraVision',
            'tagline': 'IPS 4K UHD with USB-C 90W power delivery.',
            'description': 'Crisp detail and true-to-life colors for design, coding, and multimedia entertainment with built-in stereo speakers.',
            'price': Decimal('349.00'),
            'original_price': Decimal('429.00'),
            'trust_score': 91,
            'trust_badge_label': 'Trusted',
            'stock': 22,
            'main_image': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=600',
            'rating': Decimal('4.7'),
            'review_count': 89,
            'battery_life': 'N/A (AC Powered)',
            'connectivity': 'USB-C (90W), HDMI 2.1, DisplayPort 1.4',
            'warranty': '3 years warranty',
            'specifications': {
                'Resolution': '3840 x 2160 (4K UHD)',
                'Panel Type': 'IPS 99% sRGB',
                'Refresh Rate': '75Hz',
                'Power Delivery': '90W USB-C'
            },
            'is_trending': False,
            'is_limited_offer': False,
        },
        {
            'name': 'SmartFit Chrono Gen 4 Smartwatch',
            'slug': 'smartfit-chrono-gen-4-smartwatch',
            'category': cat_map['wellness'],
            'brand': 'SmartFit',
            'tagline': 'Advanced health tracking, AMOLED display and ECG monitor.',
            'description': 'Track heart rate, SpO2, sleep stages, and workout telemetry with 7-day battery life and stainless steel case.',
            'price': Decimal('199.00'),
            'original_price': Decimal('249.00'),
            'trust_score': 93,
            'trust_badge_label': 'Trusted',
            'stock': 35,
            'main_image': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=600',
            'rating': Decimal('4.8'),
            'review_count': 320,
            'battery_life': '7 days typical',
            'connectivity': 'Bluetooth 5.3 + GPS',
            'warranty': '1 year warranty',
            'specifications': {
                'Display': '1.43" AMOLED 466x466',
                'Sensors': 'Optical Heart Rate, ECG, SpO2, Altimeter',
                'Water Resistance': '5 ATM / 50m'
            },
            'is_trending': True,
            'is_limited_offer': False,
        },
        {
            'name': 'PulseTrack Active Smartwatch',
            'slug': 'pulsetrack-active-smartwatch',
            'category': cat_map['electronics'],
            'brand': 'PulseTrack',
            'tagline': 'All-day fitness tracking with HD color touch display and heart rate monitoring.',
            'description': 'PulseTrack Active Smartwatch features real-time SpO2, sleep tracking, 20+ sports modes, smart notifications, and up to 10 days of battery life.',
            'price': Decimal('1499.00'),
            'original_price': Decimal('2499.00'),
            'trust_score': 94,
            'trust_badge_label': 'Best Value',
            'stock': 40,
            'main_image': 'https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=600',
            'rating': Decimal('4.7'),
            'review_count': 195,
            'battery_life': '10 days battery',
            'connectivity': 'Bluetooth 5.2',
            'warranty': '1 year warranty',
            'specifications': {
                'Display': '1.69" HD Touch Screen',
                'Sensors': 'Optical Heart Rate, SpO2, Sleep Tracker',
                'Water Resistance': 'IP68 Waterproof'
            },
            'is_trending': True,
            'is_limited_offer': True,
        },
        {
            'name': 'AeroWatch Pro GPS Smartwatch',
            'slug': 'aerowatch-pro-gps-smartwatch',
            'category': cat_map['electronics'],
            'brand': 'AeroSound',
            'tagline': 'Precision GPS navigation, Bluetooth calling, and titanium bezel.',
            'description': 'Engineered for athletes and outdoor enthusiasts, AeroWatch Pro includes built-in standalone GPS, Bluetooth phone calls, and music storage.',
            'price': Decimal('1899.00'),
            'original_price': Decimal('2999.00'),
            'trust_score': 96,
            'trust_badge_label': 'Top Rated',
            'stock': 28,
            'main_image': 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=600',
            'rating': Decimal('4.9'),
            'review_count': 380,
            'battery_life': '14 days battery',
            'connectivity': 'Bluetooth 5.3 + Dual GPS',
            'warranty': '2 years warranty',
            'specifications': {
                'Display': '1.4" Always-On AMOLED',
                'Sensors': 'Dual GPS, Heart Rate, ECG, Barometer',
                'Water Resistance': '50m Water Resistant'
            },
            'is_trending': True,
            'is_limited_offer': False,
        },
        {
            'name': 'Vanguard Elite Rugged Watch',
            'slug': 'vanguard-elite-rugged-watch',
            'category': cat_map['electronics'],
            'brand': 'Vanguard',
            'tagline': 'Military-grade rugged construction with sapphire glass.',
            'description': 'Built to survive extreme conditions with shock resistance, sapphire crystal glass, and tactical outdoor mode.',
            'price': Decimal('2899.00'),
            'original_price': Decimal('4299.00'),
            'trust_score': 91,
            'trust_badge_label': 'Heavy Duty',
            'stock': 15,
            'main_image': 'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=600',
            'rating': Decimal('4.6'),
            'review_count': 110,
            'battery_life': '21 days battery',
            'connectivity': 'Bluetooth 5.0 + GPS',
            'warranty': '2 years warranty',
            'specifications': {
                'Glass': 'Sapphire Crystal',
                'Bezel': 'Titanium Alloy',
                'Water Resistance': '10 ATM / 100m'
            },
            'is_trending': False,
            'is_limited_offer': False,
        }
    ]

    prod_objs = []
    for p in products_data:
        prod, _ = Product.objects.get_or_create(
            slug=p['slug'],
            defaults=p
        )
        prod_objs.append(prod)

        ProductImage.objects.get_or_create(
            product=prod,
            image_url=p['main_image'],
            defaults={'alt_text': p['name'], 'order': 1}
        )

        Review.objects.get_or_create(
            product=prod,
            author_name='David Miller',
            title='Excellent sound and comfort',
            defaults={
                'content': 'The ANC is impressive and they are comfortable for long flights and extended work sessions.',
                'rating': 5,
                'trust_tag': 'Trusted'
            }
        )
        Review.objects.get_or_create(
            product=prod,
            author_name='Sarah Jenkins',
            title='Great battery life and seamless connection',
            defaults={
                'content': 'Easy pairing, rich sound, and the battery really lasts for days without needing a charge.',
                'rating': 5,
                'trust_tag': 'Verified'
            }
        )

    print("[+] Products & Reviews seeded.")

    # 5. Maya's Wishlist Items
    Wishlist.objects.get_or_create(user=maya, product=prod_objs[0])
    Wishlist.objects.get_or_create(user=maya, product=prod_objs[1])
    Wishlist.objects.get_or_create(user=maya, product=prod_objs[3])
    print("[+] Wishlist seeded.")

    # 6. Sample Orders matching Flowstep Order History Screen (#QC-10482)
    order1, created = Order.objects.get_or_create(
        order_number='QC-10482',
        defaults={
            'user': maya,
            'status': 'delivered',
            'recipient_name': 'Maya Thompson',
            'shipping_address': '42 Silver Oak Avenue, Koramangala, Bengaluru - 560034',
            'phone': '+91 98765 43210',
            'subtotal': Decimal('129.00'),
            'shipping_fee': Decimal('0.00'),
            'tax': Decimal('6.45'),
            'total_amount': Decimal('135.45'),
            'payment_method': 'Mastercard ending in 4242',
            'tracking_number': 'TRK-98319204',
            'carrier': 'QuickCart Express',
            'estimated_delivery': 'Delivered on Oct 12, 2024',
        }
    )
    if created:
        OrderItem.objects.create(
            order=order1,
            product=prod_objs[0],
            product_name=prod_objs[0].name,
            price=prod_objs[0].price,
            quantity=1,
            image_url=prod_objs[0].main_image
        )
        events = [
            {'stage': 'placed', 'title': 'Order Placed', 'description': 'Order confirmed and verified', 'location': 'Bengaluru Hub', 'step': 1},
            {'stage': 'shipped', 'title': 'Shipped', 'description': 'Package handed over to courier', 'location': 'Central Fulfillment Center', 'step': 2},
            {'stage': 'in_transit', 'title': 'In Transit', 'description': 'Arrived at local sorting facility', 'location': 'Koramangala Station', 'step': 3},
            {'stage': 'out_for_delivery', 'title': 'Out for Delivery', 'description': 'Driver is on the way with your package', 'location': 'Koramangala South', 'step': 4},
            {'stage': 'delivered', 'title': 'Delivered', 'description': 'Signed and delivered to recipient', 'location': 'Delivered to Front Door', 'step': 5},
        ]
        base_time = timezone.now() - timedelta(days=2)
        for idx, ev in enumerate(events):
            OrderTrackingEvent.objects.create(
                order=order1,
                stage=ev['stage'],
                title=ev['title'],
                description=ev['description'],
                location=ev['location'],
                timestamp=base_time + timedelta(hours=idx * 6),
                is_completed=True,
                order_step=ev['step']
            )

    order2, _ = Order.objects.get_or_create(
        order_number='QC-10495',
        defaults={
            'user': maya,
            'status': 'in_transit',
            'recipient_name': 'Maya Thompson',
            'shipping_address': '42 Silver Oak Avenue, Koramangala, Bengaluru - 560034',
            'phone': '+91 98765 43210',
            'subtotal': Decimal('199.00'),
            'shipping_fee': Decimal('0.00'),
            'tax': Decimal('9.95'),
            'total_amount': Decimal('208.95'),
            'payment_method': 'UPI (maya@okaxis)',
            'tracking_number': 'TRK-98319255',
            'carrier': 'QuickCart Express',
            'estimated_delivery': 'Estimated Delivery: Tomorrow by 6 PM',
        }
    )
    if created:
        OrderItem.objects.create(
            order=order2,
            product=prod_objs[5],
            product_name=prod_objs[5].name,
            price=prod_objs[5].price,
            quantity=1,
            image_url=prod_objs[5].main_image
        )

    # 7. FAQs matching Flowstep Help Center Screen
    faqs = [
        ('orders', 'How do I track my order?', 'You can track your order in real-time from the "My Orders" tab under your customer profile. Click on any active order to view the full live tracking timeline.'),
        ('orders', 'What is the return policy?', 'QuickCart provides an easy 7-day hassle-free return window for all verified purchases. Items must be in original condition with tags and packaging intact.'),
        ('payment', 'Is my payment information secure?', 'Yes. All payments on QuickCart are processed through bank-grade 256-bit SSL encryption. We never store full card numbers on our servers.'),
        ('general', 'Can I shop without creating an account?', 'Yes! You can freely browse, search, compare products, and add items to your guest cart. Account creation is only requested during checkout to safely save your shipping address and order updates.'),
    ]
    for cat, q, a in faqs:
        FAQItem.objects.get_or_create(question=q, defaults={'category': cat, 'answer': a})
    print("[+] FAQs seeded.")

    # 8. Coupons (Module 11)
    from app.models import Coupon, Seller, SellerInventory, PriceHistory, PricePrediction, HomepageBanner, Notification, AdminRole
    coupons = [
        ('QUICK20', '20% Storewide Off', 'percentage', 20.00, 0.00),
        ('WELCOME10', '10% Welcome Discount', 'percentage', 10.00, 0.00),
        ('FLAT50', '₹50 Flat Savings', 'fixed', 50.00, 499.00),
        ('FREESHIP', 'Free Delivery', 'free_shipping', 0.00, 0.00),
    ]
    for code, title, dtype, dval, min_ord in coupons:
        Coupon.objects.get_or_create(
            code=code,
            defaults={
                'title': title,
                'discount_type': dtype,
                'discount_value': Decimal(str(dval)),
                'min_order_amount': Decimal(str(min_ord)),
                'is_active': True
            }
        )
    print("[+] Coupons seeded.")

    # 9. Verified Sellers for Nearby Finder (Module 3)
    sellers_data = [
        {
            'business_name': 'TechBazaar Express Hub',
            'owner_name': 'Rajesh Kumar',
            'email': 'techbazaar@example.com',
            'phone': '+91 98450 11223',
            'address': 'Plot 14, 5th Block, Koramangala',
            'city': 'Bengaluru',
            'postal_code': '560095',
            'latitude': Decimal('12.9352'),
            'longitude': Decimal('77.6245'),
            'status': 'verified',
            'rating': Decimal('4.9')
        },
        {
            'business_name': 'AudioZone Premium Store',
            'owner_name': 'Sanjay Gupta',
            'email': 'audiozone@example.com',
            'phone': '+91 98110 44556',
            'address': 'Connaught Place Outer Circle',
            'city': 'New Delhi',
            'postal_code': '110001',
            'latitude': Decimal('28.6328'),
            'longitude': Decimal('77.2197'),
            'status': 'verified',
            'rating': Decimal('4.8')
        }
    ]
    for sdata in sellers_data:
        s_obj, _ = Seller.objects.get_or_create(email=sdata['email'], defaults=sdata)
        # Add inventory for headphones
        if prod_objs:
            SellerInventory.objects.get_or_create(
                seller=s_obj,
                product=prod_objs[0],
                defaults={
                    'stock': 15,
                    'local_price': prod_objs[0].price,
                    'delivery_days': 1,
                    'is_available': True
                }
            )
    print("[+] Verified Sellers & Local Inventories seeded.")

    # 10. Price History & AI Predictions (Module 6)
    for prod in prod_objs[:4]:
        PriceHistory.objects.get_or_create(
            product=prod,
            old_price=Decimal(str(float(prod.price) * 1.15)),
            new_price=prod.price,
            defaults={'changed_at': timezone.now() - timedelta(days=10)}
        )
        PricePrediction.objects.get_or_create(
            product=prod,
            defaults={
                'predicted_trend': 'stable' if prod.price > 200 else 'drop',
                'confidence_score': 88,
                'suggestion_text': 'Fair price cycle. High probability of maintaining value.',
                'predicted_next_price': prod.price
            }
        )
    print("[+] Price Histories & Predictions seeded.")

    # 11. Homepage Banners (Module 11)
    banners_data = [
        {
            'title': 'Next-Gen Audio Excellence',
            'subtitle': 'Immerse in crystal-clear studio acoustics with active noise cancellation.',
            'badge_text': 'Up to 30% Off',
            'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80',
            'cta_text': 'Explore Audio',
            'cta_link': '/category/audio-headphones/',
            'order': 1
        },
        {
            'title': 'Smart Living & Automation',
            'subtitle': 'Elevate your daily lifestyle with intelligent workspace and kitchen essentials.',
            'badge_text': 'New Arrivals',
            'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80',
            'cta_text': 'Discover Home',
            'cta_link': '/category/home-kitchen/',
            'order': 2
        }
    ]
    for b in banners_data:
        HomepageBanner.objects.get_or_create(title=b['title'], defaults=b)
    print("[+] CMS Homepage Banners seeded.")

    # 12. Notifications for Maya (Module 10)
    Notification.objects.get_or_create(
        user=maya,
        title="Welcome to QuickCart VIP!",
        defaults={
            'notification_type': 'system',
            'body': 'Your account is active. Use promo code QUICK20 on your next order for 20% savings.',
            'related_link': '/cart/'
        }
    )
    print("[+] Notifications seeded.")

    print("[SUCCESS] QuickCart 11-Module Database Seeding Complete!")

if __name__ == '__main__':
    run()

