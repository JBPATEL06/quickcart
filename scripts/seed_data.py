import os
import sys
import django
from decimal import Decimal
from datetime import timedelta

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quickcart_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from app.models import (
    Address, Category, Product, ProductImage, Review, ReviewFlag, Wishlist,
    Cart, CartItem, Order, OrderItem, OrderTrackingEvent, FAQItem,
    Coupon, Seller, SellerInventory, PriceHistory, PricePrediction,
    HomepageBanner, Notification, AdminRole, ShippingRule
)

User = get_user_model()

def run():
    print("=" * 70)
    print(" QUICKCART — DATABASE RE-SEEDING (HIGH QUALITY MATCHED PRODUCTS)")
    print("=" * 70)

    # 1. CLEAN EXISTING STORE PRODUCTS & CATEGORIES
    print("[*] Cleaning legacy products, categories, reviews, orders...")
    OrderItem.objects.all().delete()
    OrderTrackingEvent.objects.all().delete()
    Order.objects.all().delete()
    CartItem.objects.all().delete()
    Cart.objects.all().delete()
    Wishlist.objects.all().delete()
    ReviewFlag.objects.all().delete()
    Review.objects.all().delete()
    PricePrediction.objects.all().delete()
    PriceHistory.objects.all().delete()
    SellerInventory.objects.all().delete()
    ProductImage.objects.all().delete()
    Product.objects.all().delete()
    Category.objects.all().delete()
    Seller.objects.all().delete()
    Coupon.objects.all().delete()
    HomepageBanner.objects.all().delete()
    FAQItem.objects.all().delete()
    print("[+] Database cleaned successfully.")

    # 2. CREATE ADMIN ROLE & USERS
    print("[*] Creating Admin & Customer accounts...")
    super_admin_role, _ = AdminRole.objects.get_or_create(
        name='Super Admin',
        defaults={
            'description': 'Full unrestricted access to all store modules and settings.',
            'permissions': ['all', 'products_manage', 'orders_manage', 'customers_view', 'promotions_manage', 'reports_export']
        }
    )

    admin_user, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@quickcart.com',
            'first_name': 'Super',
            'last_name': 'Admin',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True,
            'admin_role': super_admin_role,
            'theme_mode': 'light',
        }
    )
    admin_user.email = 'admin@quickcart.com'
    admin_user.role = 'admin'
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.admin_role = super_admin_role
    admin_user.set_password('admin123')
    admin_user.save()
    print("[+] Admin created: admin@quickcart.com / admin123")

    maya, _ = User.objects.get_or_create(
        username='maya',
        defaults={
            'email': 'maya@example.com',
            'first_name': 'Maya',
            'last_name': 'Thompson',
            'phone': '+91 98765 43210',
            'role': 'customer',
            'theme_mode': 'light',
            'email_notifications': True,
            'order_updates': True,
            'marketing_emails': False,
        }
    )
    maya.email = 'maya@example.com'
    maya.first_name = 'Maya'
    maya.last_name = 'Thompson'
    maya.role = 'customer'
    maya.set_password('password123')
    maya.save()
    print("[+] Customer created: maya@example.com / password123")

    alex, _ = User.objects.get_or_create(
        username='alex',
        defaults={
            'email': 'alex@example.com',
            'first_name': 'Alex',
            'last_name': 'Rivera',
            'phone': '+91 98765 11223',
            'role': 'customer',
            'theme_mode': 'light',
        }
    )
    alex.set_password('password123')
    alex.save()

    # 3. ADDRESSES FOR MAYA
    Address.objects.create(
        user=maya,
        label='home',
        recipient_name='Maya Thompson',
        street_address='42 Silver Oak Avenue, Koramangala',
        city='Bengaluru',
        state='Karnataka',
        postal_code='560034',
        country='India',
        phone='+91 98765 43210',
        is_default=True,
    )
    Address.objects.create(
        user=maya,
        label='work',
        recipient_name='Maya Thompson (Tech Park)',
        street_address='TechPark Tower B, 4th Floor, Whitefield',
        city='Bengaluru',
        state='Karnataka',
        postal_code='560066',
        country='India',
        phone='+91 98765 43210',
        is_default=False,
    )
    print("[+] Addresses created.")

    # 4. SELLERS (LOCAL REGIONAL HUBS FOR HAVERSINE FINDER)
    print("[*] Creating local sellers...")
    seller_blr = Seller.objects.create(
        business_name="QuickCart Hub Koramangala",
        owner_name="Rajesh Sharma",
        email="blr-hub@quickcart.com",
        phone="+91 80 4455 6677",
        address="100 Feet Rd, 4th Block, Koramangala",
        city="Bengaluru",
        postal_code="560034",
        latitude=Decimal("12.9352"),
        longitude=Decimal("77.6245"),
        status="verified",
        rating=Decimal("4.9")
    )
    seller_indiranagar = Seller.objects.create(
        business_name="SonicRetail Indiranagar",
        owner_name="Pooja Mehta",
        email="indira@sonicretail.com",
        phone="+91 80 2233 4455",
        address="12th Main Road, HAL 2nd Stage, Indiranagar",
        city="Bengaluru",
        postal_code="560038",
        latitude=Decimal("12.9784"),
        longitude=Decimal("77.6408"),
        status="verified",
        rating=Decimal("4.8")
    )
    seller_whitefield = Seller.objects.create(
        business_name="Whitefield Prime Electronics",
        owner_name="Vikram Verma",
        email="support@whitefieldprime.com",
        phone="+91 80 9988 7766",
        address="ITPL Main Rd, Whitefield",
        city="Bengaluru",
        postal_code="560066",
        latitude=Decimal("12.9698"),
        longitude=Decimal("77.7500"),
        status="verified",
        rating=Decimal("4.7")
    )
    sellers = [seller_blr, seller_indiranagar, seller_whitefield]
    print("[+] Sellers created.")

    # 5. CATEGORIES
    print("[*] Creating curated categories...")
    categories_def = [
        {"name": "Audio & Headphones", "slug": "audio-headphones", "icon_name": "bi-headphones", "order": 1},
        {"name": "Smartphones & Tablets", "slug": "smartphones", "icon_name": "bi-phone", "order": 2},
        {"name": "Laptops & Computers", "slug": "laptops-computers", "icon_name": "bi-display", "order": 3},
        {"name": "Smartwatches & Wearables", "slug": "smartwatches-wearables", "icon_name": "bi-smartwatch", "order": 4},
        {"name": "Cameras & Photography", "slug": "cameras-photography", "icon_name": "bi-camera", "order": 5},
        {"name": "Footwear & Sneakers", "slug": "footwear-sneakers", "icon_name": "bi-slash-circle", "order": 6},
        {"name": "Bags & Luggage", "slug": "bags-luggage", "icon_name": "bi-backpack", "order": 7},
        {"name": "Eyewear & Sunglasses", "slug": "eyewear-sunglasses", "icon_name": "bi-eyeglasses", "order": 8},
        {"name": "Smart Home & Gadgets", "slug": "smart-home", "icon_name": "bi-cpu", "order": 9},
        {"name": "Gourmet Coffee & Kitchen", "slug": "coffee-tea", "icon_name": "bi-cup-straw", "order": 10},
        {"name": "Beauty & Skincare", "slug": "beauty-skincare", "icon_name": "bi-stars", "order": 11},
        {"name": "Gaming & Consoles", "slug": "gaming-consoles", "icon_name": "bi-controller", "order": 12},
    ]

    cat_map = {}
    for c in categories_def:
        cat_obj = Category.objects.create(
            name=c['name'],
            slug=c['slug'],
            icon_name=c['icon_name'],
            order=c['order'],
            is_active=True
        )
        cat_map[c['slug']] = cat_obj
    print(f"[+] {len(cat_map)} categories created.")

    # 6. CURATED & MATCHED PRODUCTS
    print("[*] Seeding matched products with accurate images & specs...")

    raw_products = [
        # --- AUDIO & HEADPHONES ---
        {
            "name": "AeroSound Pro Wireless ANC Headphones",
            "slug": "aerosound-pro-wireless-headphones",
            "category": cat_map["audio-headphones"],
            "brand": "AeroSound",
            "tagline": "Studio-grade sound with 40-hour hybrid active noise cancellation.",
            "description": "Engineered for deep focus and pure acoustics. AeroSound Pro combines 40mm custom dynamic drivers with smart hybrid active noise cancellation, ultra-plush memory foam earcups, and dual beamforming microphones.",
            "price": Decimal("7999.00"),
            "original_price": Decimal("9999.00"),
            "trust_score": 96,
            "trust_badge_label": "Top Rated",
            "stock": 45,
            "main_image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&q=80",
            "rating": Decimal("4.8"),
            "review_count": 248,
            "battery_life": "40 hours",
            "connectivity": "Bluetooth 5.3 + 3.5mm Aux",
            "warranty": "2 Years Official Warranty",
            "specifications": {
                "Driver Size": "40mm Custom Neodymium",
                "Noise Cancellation": "Hybrid Active Noise Cancellation (35dB)",
                "Battery Life": "40 Hours (ANC On) / 55 Hours (ANC Off)",
                "Charging": "USB-C Fast Charge (10 min = 5 hours)",
                "Weight": "245 grams"
            },
            "is_trending": True,
            "is_limited_offer": True,
        },
        {
            "name": "SonicBlast Ultra Wireless Over-Ear Headset",
            "slug": "sonicblast-ultra-wireless-headset",
            "category": cat_map["audio-headphones"],
            "brand": "SonicBlast",
            "tagline": "Ultra-lightweight design with crisp spatial audio.",
            "description": "Experience lossless high-resolution audio with custom tuned acoustics, seamless multi-point Bluetooth pairing, and foldable ergonomic headband designed for creators and music enthusiasts.",
            "price": Decimal("5499.00"),
            "original_price": Decimal("7499.00"),
            "trust_score": 94,
            "trust_badge_label": "Verified",
            "stock": 38,
            "main_image": "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=600&q=80",
            "rating": Decimal("4.7"),
            "review_count": 182,
            "battery_life": "50 hours",
            "connectivity": "Bluetooth 5.3",
            "warranty": "1 Year Warranty",
            "specifications": {
                "Acoustics": "Hi-Res Audio Certified",
                "Battery": "50 Hours Playback",
                "Microphones": "4x Environmental Noise Cancellation",
                "Weight": "230 grams"
            },
            "is_trending": True,
            "is_limited_offer": False,
        },
        {
            "name": "BassPulse True Wireless Earbuds with ANC",
            "slug": "basspulse-true-wireless-earbuds",
            "category": cat_map["audio-headphones"],
            "brand": "BassPulse",
            "tagline": "Compact in-ear earbuds with punchy bass and IPX5 water resistance.",
            "description": "Ergonomic in-ear earbuds delivering deep bass, low latency gaming mode, touch controls, and up to 32 hours total playback with the pocketable wireless charging case.",
            "price": Decimal("2499.00"),
            "original_price": Decimal("3999.00"),
            "trust_score": 91,
            "trust_badge_label": "Verified",
            "stock": 80,
            "main_image": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600&q=80",
            "rating": Decimal("4.6"),
            "review_count": 315,
            "battery_life": "32 hours total",
            "connectivity": "Bluetooth 5.2",
            "warranty": "1 Year Replacement Warranty",
            "specifications": {
                "Driver": "10mm Graphene Drivers",
                "Water Resistance": "IPX5 Sweat & Splash Proof",
                "Battery": "8h Earbuds + 24h Charging Case",
                "Weight": "4.1g per earbud"
            },
            "is_trending": True,
            "is_limited_offer": True,
        },

        # --- SMARTPHONES & TABLETS ---
        {
            "name": "NovaPixel 5G Smartphone 256GB",
            "slug": "novapixel-5g-smartphone-256gb",
            "category": cat_map["smartphones"],
            "brand": "NovaPixel",
            "tagline": "Flagship 120Hz AMOLED display with 108MP AI triple camera.",
            "description": "Powered by modern octa-core 5G processor, stunning 6.7-inch 120Hz curved AMOLED panel, 5000mAh all-day battery, and 65W Turbo Dart charge.",
            "price": Decimal("29999.00"),
            "original_price": Decimal("34999.00"),
            "trust_score": 98,
            "trust_badge_label": "Top Rated",
            "stock": 25,
            "main_image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&q=80",
            "rating": Decimal("4.9"),
            "review_count": 420,
            "battery_life": "5000 mAh (2 Days)",
            "connectivity": "5G, Dual SIM, Wi-Fi 6",
            "warranty": "1 Year Brand Warranty",
            "specifications": {
                "Display": "6.7\" 1.5K AMOLED 120Hz HDR10+",
                "Processor": "Snapdragon 8 Gen 2",
                "Camera": "108MP OIS + 8MP Ultrawide + 2MP Macro",
                "Storage / RAM": "256GB UFS 3.1 / 12GB LPDDR5X",
                "Charging": "65W Fast Charging"
            },
            "is_trending": True,
            "is_limited_offer": False,
        },
        {
            "name": "ZenPad Air 11-inch Tablet with Stylus",
            "slug": "zenpad-air-11-inch-tablet",
            "category": cat_map["smartphones"],
            "brand": "ZenPad",
            "tagline": "Ultra-thin aluminum chassis with 2K 90Hz eye-care display.",
            "description": "Ideal for students, digital note-taking, and multimedia streaming. Features quad stereo speakers tuned by Dolby Atmos, magnetic stylus support, and 7500mAh battery.",
            "price": Decimal("18999.00"),
            "original_price": Decimal("22999.00"),
            "trust_score": 93,
            "trust_badge_label": "Trusted",
            "stock": 30,
            "main_image": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=600&q=80",
            "rating": Decimal("4.7"),
            "review_count": 160,
            "battery_life": "12 hours video playback",
            "connectivity": "Wi-Fi 6, Bluetooth 5.2",
            "warranty": "1 Year Warranty",
            "specifications": {
                "Screen": "11.0-inch 2K IPS LCD (2000 x 1200)",
                "Audio": "Quad Speakers Dolby Atmos",
                "RAM / ROM": "8GB RAM / 128GB ROM",
                "Weight": "475 grams"
            },
            "is_trending": False,
            "is_limited_offer": False,
        },

        # --- LAPTOPS & COMPUTERS ---
        {
            "name": "NovaBook Pro 15.6 OLED Creator Laptop",
            "slug": "novabook-pro-15-oled-laptop",
            "category": cat_map["laptops-computers"],
            "brand": "NovaTech",
            "tagline": "Intel Core Ultra 7 with 32GB RAM and 2.8K 120Hz OLED screen.",
            "description": "Crafted in CNC aerospace aluminum, NovaBook Pro is a powerhouse for software development, video editing, and intensive multitasking with Thunderbolt 4 connectivity.",
            "price": Decimal("84999.00"),
            "original_price": Decimal("99999.00"),
            "trust_score": 97,
            "trust_badge_label": "Top Rated",
            "stock": 14,
            "main_image": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&q=80",
            "rating": Decimal("4.9"),
            "review_count": 94,
            "battery_life": "14 hours battery",
            "connectivity": "Wi-Fi 6E, Thunderbolt 4, HDMI 2.1",
            "warranty": "2 Years On-Site Warranty",
            "specifications": {
                "CPU": "Intel Core Ultra 7 155H",
                "Memory": "32GB LPDDR5X 7467MHz",
                "Storage": "1TB PCIe Gen4 NVMe SSD",
                "Display": "15.6\" 2.8K OLED (100% DCI-P3, 120Hz)",
                "Weight": "1.58 kg"
            },
            "is_trending": True,
            "is_limited_offer": True,
        },
        {
            "name": "UltraVision 27-inch 4K UHD IPS Designer Monitor",
            "slug": "ultravision-27-inch-4k-monitor",
            "category": cat_map["laptops-computers"],
            "brand": "UltraVision",
            "tagline": "3840x2160 IPS panel with 90W USB-C single cable power delivery.",
            "description": "True color accuracy (99% sRGB, Delta E < 2) with height adjustable stand, built-in USB hub, and flicker-free blue light reduction.",
            "price": Decimal("24999.00"),
            "original_price": Decimal("29999.00"),
            "trust_score": 95,
            "trust_badge_label": "Verified",
            "stock": 22,
            "main_image": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=600&q=80",
            "rating": Decimal("4.8"),
            "review_count": 112,
            "battery_life": "AC Powered",
            "connectivity": "USB-C (90W PD), HDMI 2.0 x2, DP 1.4",
            "warranty": "3 Years Panel Warranty",
            "specifications": {
                "Resolution": "3840 x 2160 (4K UHD)",
                "Color Space": "99% sRGB, HDR400",
                "Stand": "Height, Pivot, Swivel & Tilt",
                "Speakers": "Integrated 2x 3W Stereo"
            },
            "is_trending": False,
            "is_limited_offer": False,
        },
        {
            "name": "KeyCraft RGB Mechanical Keyboard (Hot-Swap)",
            "slug": "keycraft-rgb-mechanical-keyboard",
            "category": cat_map["laptops-computers"],
            "brand": "KeyCraft",
            "tagline": "75% compact layout with pre-lubed linear switches and gasket mount.",
            "description": "Buttery smooth typing experience with sound-dampening silicone foam, PBT doubleshot keycaps, south-facing RGB, and multi-device Bluetooth/2.4G wireless switching.",
            "price": Decimal("4999.00"),
            "original_price": Decimal("6499.00"),
            "trust_score": 94,
            "trust_badge_label": "Verified",
            "stock": 40,
            "main_image": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600&q=80",
            "rating": Decimal("4.7"),
            "review_count": 178,
            "battery_life": "200 hours (RGB off)",
            "connectivity": "Tri-Mode (Bluetooth, 2.4GHz, USB-C)",
            "warranty": "1 Year Warranty",
            "specifications": {
                "Layout": "75% with Aluminum Volume Knob",
                "Switches": "Pre-lubed Custom Yellow Linear",
                "Keycaps": "PBT Doubleshot Cherry Profile",
                "Mount": "Gasket Mounted Structure"
            },
            "is_trending": True,
            "is_limited_offer": False,
        },

        # --- SMARTWATCHES & WEARABLES ---
        {
            "name": "SmartFit Chrono Titanium Smartwatch Gen 4",
            "slug": "smartfit-chrono-titanium-smartwatch",
            "category": cat_map["smartwatches-wearables"],
            "brand": "SmartFit",
            "tagline": "Sapphire glass, ECG heart monitoring, and 10-day battery life.",
            "description": "Crafted from aerospace titanium with always-on AMOLED display, accurate GPS dual-band tracking, blood oxygen SpO2 monitoring, and 50m water resistance.",
            "price": Decimal("12999.00"),
            "original_price": Decimal("15999.00"),
            "trust_score": 97,
            "trust_badge_label": "Top Rated",
            "stock": 35,
            "main_image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&q=80",
            "rating": Decimal("4.8"),
            "review_count": 380,
            "battery_life": "10 days typical use",
            "connectivity": "Bluetooth 5.3, Dual-band GPS",
            "warranty": "1 Year Warranty",
            "specifications": {
                "Display": "1.43\" AMOLED 466x466 (1000 nits)",
                "Material": "Aerospace Titanium & Sapphire Crystal",
                "Sensors": "ECG, SpO2, Heart Rate, Stress, Sleep",
                "Water Rating": "5ATM (50 meters swimproof)"
            },
            "is_trending": True,
            "is_limited_offer": True,
        },
        {
            "name": "PulseFit Active Fitness Tracker Smartwatch",
            "slug": "pulsefit-active-fitness-tracker",
            "category": cat_map["smartwatches-wearables"],
            "brand": "PulseFit",
            "tagline": "Lightweight 24/7 activity and workout tracker with sleep analysis.",
            "description": "100+ sport tracking modes, real-time heart rate zones, guided breathing exercises, and music controls in a sleek 32-gram featherweight design.",
            "price": Decimal("3499.00"),
            "original_price": Decimal("4999.00"),
            "trust_score": 92,
            "trust_badge_label": "Verified",
            "stock": 50,
            "main_image": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=600&q=80",
            "rating": Decimal("4.6"),
            "review_count": 210,
            "battery_life": "14 days battery",
            "connectivity": "Bluetooth 5.1",
            "warranty": "1 Year Warranty",
            "specifications": {
                "Display": "1.3\" HD Color Touchscreen",
                "Sports Modes": "100+ Workout Tracking Modes",
                "Battery": "14 Days Long Battery",
                "Weight": "32 grams"
            },
            "is_trending": False,
            "is_limited_offer": False,
        },

        # --- CAMERAS & PHOTOGRAPHY ---
        {
            "name": "LumixPro 4K Mirrorless Digital Camera Kit",
            "slug": "lumixpro-4k-mirrorless-camera",
            "category": cat_map["cameras-photography"],
            "brand": "LumixPro",
            "tagline": "24.2MP full-frame sensor with 5-axis in-body image stabilization.",
            "description": "Capture cinematic 4K 60fps video and razor sharp stills. Features real-time eye autofocus, dual SD card slots, and bundled 24-70mm f/2.8 versatile zoom lens.",
            "price": Decimal("74999.00"),
            "original_price": Decimal("89999.00"),
            "trust_score": 96,
            "trust_badge_label": "Top Rated",
            "stock": 10,
            "main_image": "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=600&q=80",
            "rating": Decimal("4.9"),
            "review_count": 76,
            "battery_life": "600 shots per charge",
            "connectivity": "Wi-Fi, Bluetooth, Micro HDMI, USB-C",
            "warranty": "2 Years Official Warranty",
            "specifications": {
                "Sensor": "24.2MP Full-Frame CMOS",
                "Stabilization": "5-Axis In-Body Sensor-Shift",
                "Video": "4K 60p 10-bit 4:2:2 Internal",
                "Autofocus": "759 Phase-Detection Points"
            },
            "is_trending": True,
            "is_limited_offer": False,
        },

        # --- FOOTWEAR & SNEAKERS ---
        {
            "name": "AeroStride Air Cushion Running Shoes",
            "slug": "aerostride-air-cushion-running-shoes",
            "category": cat_map["footwear-sneakers"],
            "brand": "AeroStride",
            "tagline": "Responsive nitrogen-infused foam midsole with breathable mesh.",
            "description": "Engineered for road running, workouts, and daily walking comfort. The dynamic flex sole absorbs shock while the seamless engineered mesh keeps your feet cool.",
            "price": Decimal("3299.00"),
            "original_price": Decimal("4499.00"),
            "trust_score": 95,
            "trust_badge_label": "Verified",
            "stock": 65,
            "main_image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&q=80",
            "rating": Decimal("4.8"),
            "review_count": 480,
            "battery_life": "N/A",
            "connectivity": "N/A",
            "warranty": "6 Months Sole Warranty",
            "specifications": {
                "Upper": "Engineered Breathable Mesh",
                "Midsole": "High-Rebound Nitrogen Foam",
                "Outsole": "Anti-Skid High Grip Rubber",
                "Weight": "260g (Size 9)"
            },
            "is_trending": True,
            "is_limited_offer": True,
        },
        {
            "name": "UrbanClassic Minimalist White Leather Sneakers",
            "slug": "urbanclassic-white-leather-sneakers",
            "category": cat_map["footwear-sneakers"],
            "brand": "UrbanClassic",
            "tagline": "Full-grain Italian calfskin leather with cushioned memory insole.",
            "description": "Timeless clean silhouette that pairs effortlessly with denim, chinos, or casual tailoring. Features waxed cotton laces and durable stitched rubber cupsole.",
            "price": Decimal("3999.00"),
            "original_price": Decimal("5499.00"),
            "trust_score": 93,
            "trust_badge_label": "Verified",
            "stock": 42,
            "main_image": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=600&q=80",
            "rating": Decimal("4.7"),
            "review_count": 195,
            "battery_life": "N/A",
            "connectivity": "N/A",
            "warranty": "6 Months Warranty",
            "specifications": {
                "Material": "Full Grain Leather Upper",
                "Insole": "Removable Memory Foam Footbed",
                "Sole": "Hand-Stitched Rubber Cupsole",
                "Origin": "Handcrafted"
            },
            "is_trending": False,
            "is_limited_offer": False,
        },

        # --- BAGS & LUGGAGE ---
        {
            "name": "CanvasCraft Heavy-Duty Organic Tote Bag",
            "slug": "canvascraft-organic-tote-bag",
            "category": cat_map["bags-luggage"],
            "brand": "CanvasCraft",
            "tagline": "16oz washed cotton canvas with reinforced double handles.",
            "description": "Spacious, eco-friendly everyday tote designed for farmer markets, books, laptops, and travel. Features interior zip pocket and magnetic clasp closure.",
            "price": Decimal("999.00"),
            "original_price": Decimal("1499.00"),
            "trust_score": 92,
            "trust_badge_label": "Verified",
            "stock": 90,
            "main_image": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=600&q=80",
            "rating": Decimal("4.7"),
            "review_count": 230,
            "battery_life": "N/A",
            "connectivity": "N/A",
            "warranty": "1 Year Stitching Warranty",
            "specifications": {
                "Fabric": "100% Organic 16oz Cotton Canvas",
                "Capacity": "22 Liters",
                "Pockets": "1 Main Compartment + 1 Inner Zip Pocket",
                "Dimensions": "40cm x 35cm x 12cm"
            },
            "is_trending": True,
            "is_limited_offer": False,
        },
        {
            "name": "UrbanExplorer Weatherproof Commuter Backpack",
            "slug": "urbanexplorer-commuter-backpack",
            "category": cat_map["bags-luggage"],
            "brand": "UrbanExplorer",
            "tagline": "Water-resistant ballistic nylon with dedicated 16-inch laptop vault.",
            "description": "Ergonomic air-mesh back padding, hidden passport pocket, luggage pass-through strap, and water bottle holder for seamless daily commuting and travel.",
            "price": Decimal("2999.00"),
            "original_price": Decimal("4299.00"),
            "trust_score": 96,
            "trust_badge_label": "Top Rated",
            "stock": 55,
            "main_image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&q=80",
            "rating": Decimal("4.8"),
            "review_count": 310,
            "battery_life": "N/A",
            "connectivity": "N/A",
            "warranty": "3 Years Warranty",
            "specifications": {
                "Material": "900D Water-Repellent Ballistic Nylon",
                "Laptop Sleeve": "Padded Up to 16-inch MacBook Pro",
                "Capacity": "26 Liters",
                "Zippers": "YKK Weatherproof Aquaguard"
            },
            "is_trending": True,
            "is_limited_offer": False,
        },

        # --- EYEWEAR & SUNGLASSES ---
        {
            "name": "Aviator Classic Polarized Sunglasses",
            "slug": "aviator-classic-polarized-sunglasses",
            "category": cat_map["eyewear-sunglasses"],
            "brand": "Solaris",
            "tagline": "UV400 anti-glare polarized lenses with ultra-thin gold wire frame.",
            "description": "Timeless teardrop pilot style crafted with spring-loaded hinges, adjustable silicone nose pads, and 100% UVA/UVB eye protection.",
            "price": Decimal("1799.00"),
            "original_price": Decimal("2499.00"),
            "trust_score": 94,
            "trust_badge_label": "Verified",
            "stock": 48,
            "main_image": "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=600&q=80",
            "rating": Decimal("4.7"),
            "review_count": 140,
            "battery_life": "N/A",
            "connectivity": "N/A",
            "warranty": "1 Year Frame Warranty",
            "specifications": {
                "Lens": "Triacetate Cellulose Polarized (UV400)",
                "Frame": "Monel Metal Alloy",
                "Lens Width": "58mm",
                "Includes": "Hard Leather Case & Microfiber Cloth"
            },
            "is_trending": True,
            "is_limited_offer": False,
        },

        # --- SMART HOME & GADGETS ---
        {
            "name": "LumiSmart Ambient Desk Lamp & Wireless Charger",
            "slug": "lumismart-ambient-desk-lamp",
            "category": cat_map["smart-home"],
            "brand": "LumiSmart",
            "tagline": "Adjustable color temperature, touch dimmer, and 15W Qi wireless charging base.",
            "description": "Elevate your desk setup with flicker-free natural light (CRI > 95), 5 brightness levels, memory function, and integrated wireless fast charging for your phone.",
            "price": Decimal("2199.00"),
            "original_price": Decimal("2999.00"),
            "trust_score": 95,
            "trust_badge_label": "Verified",
            "stock": 35,
            "main_image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600&q=80",
            "rating": Decimal("4.8"),
            "review_count": 175,
            "battery_life": "AC Powered",
            "connectivity": "Qi Wireless Charger (15W)",
            "warranty": "1 Year Warranty",
            "specifications": {
                "Color Temperature": "2700K - 6500K (5 Presets)",
                "Brightness": "Max 800 Lumens (CRI > 95)",
                "Wireless Charge": "15W Fast Charge Base",
                "Arm": "Double-Jointed Multi-Angle Rotation"
            },
            "is_trending": True,
            "is_limited_offer": False,
        },

        # --- GOURMET COFFEE & KITCHEN ---
        {
            "name": "HydroThermal Double-Wall Insulated Tumbler 500ml",
            "slug": "hydrothermal-insulated-tumbler-500ml",
            "category": cat_map["coffee-tea"],
            "brand": "HydroThermal",
            "tagline": "Keeps drinks cold for 24 hours or piping hot for 12 hours.",
            "description": "Made from food-grade 18/8 stainless steel with leak-proof flip lid, sweat-free powder coating, and condensation-free vacuum insulation.",
            "price": Decimal("1199.00"),
            "original_price": Decimal("1699.00"),
            "trust_score": 97,
            "trust_badge_label": "Top Rated",
            "stock": 70,
            "main_image": "https://images.unsplash.com/photo-1577705998148-6da4f3963bc8?w=600&q=80",
            "rating": Decimal("4.9"),
            "review_count": 390,
            "battery_life": "N/A",
            "connectivity": "N/A",
            "warranty": "Lifetime Warranty on Insulation",
            "specifications": {
                "Material": "18/8 Pro-Grade Stainless Steel",
                "Capacity": "500 ml (17 oz)",
                "Insulation": "TempShield Double Wall Vacuum",
                "BPA Free": "100% Non-Toxic & BPA Free"
            },
            "is_trending": True,
            "is_limited_offer": False,
        },

        # --- BEAUTY & SKINCARE ---
        {
            "name": "Botanical Glow Hydrating Vitamin C Face Serum",
            "slug": "botanical-glow-vitamin-c-serum",
            "category": cat_map["beauty-skincare"],
            "brand": "Botanical Glow",
            "tagline": "20% Vitamin C + Hyaluronic Acid for radiant, glowing skin.",
            "description": "Cruelty-free, dermatologically tested brightening serum that visibly reduces dark spots, evens skin tone, and deeply hydrates with natural plant extracts.",
            "price": Decimal("899.00"),
            "original_price": Decimal("1299.00"),
            "trust_score": 93,
            "trust_badge_label": "Verified",
            "stock": 85,
            "main_image": "https://images.unsplash.com/photo-1608248597359-bb43ef859608?w=600&q=80",
            "rating": Decimal("4.7"),
            "review_count": 280,
            "battery_life": "N/A",
            "connectivity": "N/A",
            "warranty": "100% Satisfaction Guarantee",
            "specifications": {
                "Active Ingredients": "20% Vitamin C, 2% Hyaluronic Acid, Ferulic Acid",
                "Volume": "30 ml (1.0 fl oz)",
                "Skin Type": "Suitable for all skin types",
                "Certification": "Cruelty-Free & Paraben-Free"
            },
            "is_trending": True,
            "is_limited_offer": False,
        },

        # --- GAMING & CONSOLES ---
        {
            "name": "ProStrike Wireless Haptic Game Controller",
            "slug": "prostrike-wireless-game-controller",
            "category": cat_map["gaming-consoles"],
            "brand": "ProStrike",
            "tagline": "Hall-effect anti-drift joysticks with customizable rear paddle buttons.",
            "description": "Engineered for competitive esports on PC, Steam Deck, Switch, and Mobile. Features magnetic hall effect triggers, dual rumble vibration motors, and 1000Hz polling rate.",
            "price": Decimal("3499.00"),
            "original_price": Decimal("4999.00"),
            "trust_score": 96,
            "trust_badge_label": "Top Rated",
            "stock": 35,
            "main_image": "https://images.unsplash.com/photo-1592840496073-e80bb52b4122?w=600&q=80",
            "rating": Decimal("4.8"),
            "review_count": 215,
            "battery_life": "20 hours per charge",
            "connectivity": "Bluetooth, 2.4G Wireless Dongle, USB-C",
            "warranty": "1 Year Replacement Warranty",
            "specifications": {
                "Joysticks": "Hall Effect Magnetic Anti-Drift",
                "Polling Rate": "1000Hz Ultra Low Latency",
                "Battery": "1000 mAh Rechargeable",
                "Compatibility": "PC, Windows, Android, iOS, Nintendo Switch"
            },
            "is_trending": True,
            "is_limited_offer": True,
        },
    ]

    product_objs = []
    for item in raw_products:
        p = Product.objects.create(
            name=item["name"],
            slug=item["slug"],
            category=item["category"],
            brand=item["brand"],
            tagline=item["tagline"],
            description=item["description"],
            price=item["price"],
            original_price=item["original_price"],
            trust_score=item["trust_score"],
            trust_badge_label=item["trust_badge_label"],
            stock=item["stock"],
            main_image=item["main_image"],
            rating=item["rating"],
            review_count=item["review_count"],
            battery_life=item.get("battery_life", ""),
            connectivity=item.get("connectivity", ""),
            warranty=item.get("warranty", ""),
            specifications=item.get("specifications", {}),
            is_trending=item.get("is_trending", False),
            is_limited_offer=item.get("is_limited_offer", False),
            is_published=True
        )
        product_objs.append(p)

        # Additional Gallery Images
        ProductImage.objects.create(
            product=p,
            image_url=item["main_image"],
            alt_text=p.name,
            order=1
        )

        # Seller Inventory for Haversine distances
        for seller in sellers:
            SellerInventory.objects.create(
                seller=seller,
                product=p,
                local_price=p.price,
                stock=20,
                delivery_days=1,
                is_available=True
            )

        # Price History (for AI Price trend forecast chart)
        base_price = float(p.price)
        for days_ago, multiplier in [(30, 1.15), (20, 1.10), (10, 1.05), (5, 1.02), (0, 1.0)]:
            PriceHistory.objects.create(
                product=p,
                old_price=Decimal(str(round(base_price * multiplier, 2))),
                new_price=p.price,
                changed_by=admin_user
            )

        PricePrediction.objects.create(
            product=p,
            predicted_trend='drop' if p.is_limited_offer else 'stable',
            confidence_score=92,
            suggestion_text=f"High trust rating of {p.trust_score}% and competitive discount. Best time to buy.",
            predicted_next_price=Decimal(str(round(base_price * 0.95, 2)))
        )

        # Authentic Reviews
        r1 = Review.objects.create(
            product=p,
            user=maya,
            author_name="Maya Thompson",
            rating=5,
            title=f"Excellent build quality — {p.name}",
            content=f"Received the {p.name} quickly! Exceeded my expectations in build quality, finish, and performance.",
            trust_tag='Verified Buyer',
            is_verified_purchase=True
        )
        ReviewFlag.objects.create(
            review=r1,
            suspicion_score=5,
            flag_reason='Verified purchase pattern',
            status='approved',
            is_moderated=True,
            moderated_by=admin_user
        )

        r2 = Review.objects.create(
            product=p,
            user=alex,
            author_name="Alex Rivera",
            rating=4,
            title="Great value for money",
            content=f"Solid performance for the price point. Packaging was secure and delivered in 24 hours.",
            trust_tag='Verified Buyer',
            is_verified_purchase=True
        )
        ReviewFlag.objects.create(
            review=r2,
            suspicion_score=8,
            flag_reason='Organic positive review',
            status='approved',
            is_moderated=True,
            moderated_by=admin_user
        )

    print(f"[+] {len(product_objs)} matched products created.")

    # 7. PROMOTIONAL COUPONS
    print("[*] Creating promotional coupons...")
    coupons = [
        {"code": "QUICK20", "title": "20% Off Storewide", "discount_value": Decimal("20.00"), "min_order_amount": Decimal("1000.00")},
        {"code": "WELCOME10", "title": "Welcome 10% Discount", "discount_value": Decimal("10.00"), "min_order_amount": Decimal("500.00")},
        {"code": "FLAT50", "title": "Flat 15% Savings", "discount_value": Decimal("15.00"), "min_order_amount": Decimal("2000.00")},
        {"code": "FREESHIP", "title": "Free Delivery Offer", "discount_value": Decimal("5.00"), "min_order_amount": Decimal("499.00")},
    ]
    for c in coupons:
        Coupon.objects.create(
            code=c["code"],
            title=c["title"],
            discount_type="percentage",
            discount_value=c["discount_value"],
            min_order_amount=c["min_order_amount"],
            is_active=True,
            valid_until=timezone.now() + timedelta(days=90)
        )
    print("[+] Coupons created.")

    # 8. HOMEPAGE BANNERS
    print("[*] Creating homepage hero banners...")
    HomepageBanner.objects.create(
        title="Big Savings, Better Choices",
        subtitle="Up to 40% Off Audio, Laptops, Smartphones & Lifestyle Gear",
        cta_text="Shop Trending Deals",
        cta_link="/search/",
        badge_text="LIMITED TIME OFFER",
        image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=1200&q=80",
        is_active=True,
        order=1
    )
    HomepageBanner.objects.create(
        title="Next-Gen Wearables & Tech",
        subtitle="AI-Powered Trust Verification on All Electronics",
        cta_text="Explore Smartwatches",
        cta_link="/category/smartwatches-wearables/",
        badge_text="NEW ARRIVALS",
        image_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=1200&q=80",
        is_active=True,
        order=2
    )

    # 9. SAMPLE ORDERS & TRACKING TIMELINE FOR MAYA
    print("[*] Creating sample orders with live tracking...")
    order1 = Order.objects.create(
        order_number="QC-2026-88912",
        user=maya,
        recipient_name="Maya Thompson",
        phone="+91 98765 43210",
        shipping_address="42 Silver Oak Avenue, Koramangala, Bengaluru, Karnataka - 560034",
        status="shipped",
        payment_method="Card ending in 4242",
        is_paid=True,
        subtotal=Decimal("7999.00"),
        discount_amount=Decimal("1599.80"),
        shipping_fee=Decimal("0.00"),
        tax=Decimal("1151.85"),
        total_amount=Decimal("7551.05"),
        promo_code="QUICK20",
        tracking_number="QCEXP88912IN",
        carrier="QuickCart Express",
        estimated_delivery="Tomorrow by 5:00 PM",
        created_at=timezone.now() - timedelta(days=2)
    )
    OrderItem.objects.create(
        order=order1,
        product=product_objs[0],
        product_name=product_objs[0].name,
        price=product_objs[0].price,
        quantity=1,
        image_url=product_objs[0].main_image
    )
    # Order 1 Tracking Milestones
    OrderTrackingEvent.objects.create(order=order1, stage="placed", title="Order Placed", description="Order confirmed and authorized by customer.", timestamp=timezone.now() - timedelta(days=2), is_completed=True, order_step=1)
    OrderTrackingEvent.objects.create(order=order1, stage="packed", title="Packed at Central Hub", description="Packed securely in QuickCart Eco-Box at Bengaluru Central Hub.", timestamp=timezone.now() - timedelta(days=1, hours=12), is_completed=True, order_step=2)
    OrderTrackingEvent.objects.create(order=order1, stage="shipped", title="In Transit", description="Dispatched with express courier. In transit to Koramangala hub.", timestamp=timezone.now() - timedelta(hours=6), is_completed=True, order_step=3)

    order2 = Order.objects.create(
        order_number="QC-2026-77341",
        user=maya,
        recipient_name="Maya Thompson",
        phone="+91 98765 43210",
        shipping_address="42 Silver Oak Avenue, Koramangala, Bengaluru, Karnataka - 560034",
        status="delivered",
        payment_method="UPI (maya@okhdfcbank)",
        is_paid=True,
        subtotal=Decimal("3299.00"),
        discount_amount=Decimal("0.00"),
        shipping_fee=Decimal("0.00"),
        tax=Decimal("593.82"),
        total_amount=Decimal("3892.82"),
        tracking_number="QCEXP77341IN",
        carrier="QuickCart Express",
        estimated_delivery="Delivered",
        created_at=timezone.now() - timedelta(days=7)
    )
    OrderItem.objects.create(
        order=order2,
        product=product_objs[11], # Running shoes
        product_name=product_objs[11].name,
        price=product_objs[11].price,
        quantity=1,
        image_url=product_objs[11].main_image
    )
    OrderTrackingEvent.objects.create(order=order2, stage="placed", title="Order Placed", description="Order placed successfully.", timestamp=timezone.now() - timedelta(days=7), is_completed=True, order_step=1)
    OrderTrackingEvent.objects.create(order=order2, stage="packed", title="Packed", description="Package verified and packed.", timestamp=timezone.now() - timedelta(days=6), is_completed=True, order_step=2)
    OrderTrackingEvent.objects.create(order=order2, stage="shipped", title="Shipped", description="Shipped via Express Delivery.", timestamp=timezone.now() - timedelta(days=5), is_completed=True, order_step=3)
    OrderTrackingEvent.objects.create(order=order2, stage="delivered", title="Delivered", description="Delivered directly to customer at 42 Silver Oak Avenue.", timestamp=timezone.now() - timedelta(days=4), is_completed=True, order_step=4)

    # 10. FAQ ITEMS
    print("[*] Creating FAQ items...")
    faqs = [
        ("How does QuickCart calculate the Trust Score?", "Our AI Fake Review Classifier examines linguistic patterns, verified purchase metadata, repetitive phrases, and account credibility to compute a transparent 0-100 Trust Score for each item."),
        ("What is the return and refund policy?", "QuickCart offers a hassle-free 7-day return policy on eligible electronics and accessories. Simply visit your Orders page and select 'Request Return'."),
        ("How does Voice Search work?", "Click the microphone icon in the search bar, speak your query clearly, and QuickCart's Web Speech engine will transcribe and filter matching products instantly."),
        ("How do I track my delivery in real-time?", "Go to 'My Orders' in your account menu and click 'Track Shipment' to see every transit milestone from warehouse packing to doorstep delivery."),
    ]
    for idx, (q, a) in enumerate(faqs, start=1):
        FAQItem.objects.create(category='general', question=q, answer=a, order=idx)

    # 11. LOCATION & STOREWIDE SHIPPING RULES (ADMIN IS SELLER)
    print("[*] Creating delivery & shipping rules...")
    ShippingRule.objects.all().delete()
    ShippingRule.objects.create(
        label="Free Delivery on Orders Above ₹999",
        rule_type="storewide",
        min_order_amount=Decimal("999.00"),
        delivery_fee=Decimal("0.00"),
        priority=1,
        is_active=True
    )
    ShippingRule.objects.create(
        label="Free Local Delivery in Bengaluru (Central Hub City)",
        rule_type="city",
        city="Bengaluru",
        min_order_amount=Decimal("0.00"),
        delivery_fee=Decimal("0.00"),
        priority=2,
        is_active=True
    )
    ShippingRule.objects.create(
        label="Standard Express Flat Delivery",
        rule_type="storewide",
        min_order_amount=Decimal("0.00"),
        delivery_fee=Decimal("50.00"),
        priority=100,
        is_active=True
    )
    print("[+] Delivery rules created.")

    print("=" * 70)
    print(" [+] QUICKCART DATABASE SEEDING COMPLETE!")
    print(f" * Products:   {Product.objects.count()} (100% matched names, photos & categories)")
    print(f" * Categories: {Category.objects.count()}")
    print(f" * Orders:     {Order.objects.count()} (with live tracking milestones)")
    print(f" * Coupons:    {Coupon.objects.count()} (QUICK20, WELCOME10, FLAT50, FREESHIP)")
    print(f" * Shipping:   {ShippingRule.objects.count()} rules")
    print(f" * Admin:      admin@quickcart.com / admin123")
    print(f" * Customer:   maya@example.com / password123")
    print("=" * 70)

if __name__ == '__main__':
    run()
