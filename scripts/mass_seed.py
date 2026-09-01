import os
import sys
import random
import django
from decimal import Decimal
from datetime import timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quickcart_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from app.models import (
    User, Address, Category, Product, ProductImage, Review, ReviewFlag,
    Coupon, Seller, SellerInventory, PriceHistory, PricePrediction, HomepageBanner
)

User = get_user_model()

# ==========================================
# 1. 40+ CATEGORIES DEFINITIONS
# ==========================================
CATEGORY_DEFINITIONS = [
    ("Electronics", "electronics", "bi-laptop"),
    ("Audio & Headphones", "audio-headphones", "bi-headphones"),
    ("Smartphones & Tablets", "smartphones", "bi-phone"),
    ("Laptops & Computers", "laptops-computers", "bi-display"),
    ("Smartwatches & Wearables", "smartwatches-wearables", "bi-smartwatch"),
    ("Cameras & Photography", "cameras-photography", "bi-camera"),
    ("Gaming & Consoles", "gaming-consoles", "bi-controller"),
    ("Home & Kitchen", "home-kitchen", "bi-house-door"),
    ("Smart Home & Automation", "smart-home", "bi-cpu"),
    ("Furniture & Living", "furniture-living", "bi-lamp"),
    ("Kitchen Appliances", "kitchen-appliances", "bi-cup-hot"),
    ("Cookware & Dining", "cookware-dining", "bi-egg-fried"),
    ("Men's Fashion", "mens-fashion", "bi-person"),
    ("Women's Fashion", "womens-fashion", "bi-bag"),
    ("Footwear & Sneakers", "footwear-sneakers", "bi-slash-circle"),
    ("Watches & Chronos", "watches-chronos", "bi-watch"),
    ("Jewelry & Accessories", "jewelry-accessories", "bi-gem"),
    ("Bags & Luggage", "bags-luggage", "bi-backpack"),
    ("Eyewear & Sunglasses", "eyewear-sunglasses", "bi-eyeglasses"),
    ("Health & Wellness", "health-wellness", "bi-heart-pulse"),
    ("Fitness & Exercise", "fitness-exercise", "bi-activity"),
    ("Sports & Outdoors", "sports-outdoors", "bi-bicycle"),
    ("Beauty & Skincare", "beauty-skincare", "bi-stars"),
    ("Haircare & Grooming", "haircare-grooming", "bi-scissors"),
    ("Fragrances & Perfumes", "fragrances-perfumes", "bi-droplet"),
    ("Baby & Kids", "baby-kids", "bi-emoji-smile"),
    ("Toys & Board Games", "toys-games", "bi-puzzle"),
    ("Books & Stationery", "books-stationery", "bi-book"),
    ("Musical Instruments", "musical-instruments", "bi-music-note-beamed"),
    ("Automotive Accessories", "automotive-accessories", "bi-car-front"),
    ("Tools & Home Hardware", "tools-hardware", "bi-tools"),
    ("Garden & Patio", "garden-patio", "bi-flower1"),
    ("Pet Supplies", "pet-supplies", "bi-tencent-qq"),
    ("Gourmet Coffee & Tea", "coffee-tea", "bi-cup-straw"),
    ("Office Supplies & Desk", "office-desk", "bi-briefcase"),
    ("Travel Gear & Accessories", "travel-gear", "bi-airplane"),
    ("Art & Craft Supplies", "art-craft", "bi-palette"),
    ("Eco-Friendly Living", "eco-friendly", "bi-tree"),
    ("Personal Safety & Care", "personal-safety", "bi-shield-check"),
    ("Party & Celebration", "party-celebration", "bi-balloon"),
    ("Bedding & Bath", "bedding-bath", "bi-moon-stars"),
    ("Smart Storage & Organizers", "smart-storage", "bi-box-seam"),
]

# High quality Unsplash imagery per theme
IMAGES_POOL = [
    "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&q=80",
    "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&q=80",
    "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=600&q=80",
    "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=600&q=80",
    "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=600&q=80",
    "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=600&q=80",
    "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=600&q=80",
    "https://images.unsplash.com/photo-1560343090-f0409e92791a?w=600&q=80",
    "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=600&q=80",
    "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&q=80",
    "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=600&q=80",
    "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=600&q=80",
    "https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=600&q=80",
    "https://images.unsplash.com/photo-1581291518857-4e27b48ff24e?w=600&q=80",
    "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=600&q=80",
    "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&q=80",
    "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&q=80",
    "https://images.unsplash.com/photo-1564466809058-bf4114d55352?w=600&q=80",
    "https://images.unsplash.com/photo-1580828343064-fde4fc206bc6?w=600&q=80",
    "https://images.unsplash.com/photo-1544816155-12df9643f363?w=600&q=80"
]

FIRST_NAMES = [
    "Aarav", "Aditi", "Rohan", "Ananya", "Vikram", "Pooja", "Rahul", "Sneha", "Karan", "Priya",
    "Siddharth", "Neha", "Arjun", "Kavya", "Varun", "Meera", "Aditya", "Rhea", "Manish", "Divya",
    "Tanmay", "Isha", "Nikhil", "Shreya", "Sameer", "Tanvi", "Akash", "Anushka", "Gaurav", "Simran",
    "Harsh", "Deepika", "Kunal", "Swati", "Rajat", "Sakshi", "Pranav", "Bhavna", "Abhishek", "Aishwarya",
    "Karthik", "Ritu", "Vivek", "Payal", "Amit", "Nandini", "Tarun", "Rashmi", "Deepak", "Maya"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Mehta", "Reddy", "Nair", "Gupta", "Iyer", "Chopra", "Malhotra",
    "Kulkarni", "Deshmukh", "Singhania", "Joshi", "Bhatia", "Bansal", "Kapoor", "Saxena", "Roy", "Sen"
]

CITIES = [
    ("Bengaluru", "Karnataka", "560001"),
    ("Mumbai", "Maharashtra", "400001"),
    ("New Delhi", "Delhi", "110001"),
    ("Pune", "Maharashtra", "411001"),
    ("Hyderabad", "Telangana", "500001"),
    ("Chennai", "Tamil Nadu", "600001"),
    ("Kolkata", "West Bengal", "700001"),
    ("Ahmedabad", "Gujarat", "380001"),
    ("Jaipur", "Rajasthan", "302001"),
    ("Chandigarh", "Punjab", "160001"),
]

REVIEW_TEMPLATES = [
    ("Outstanding product!", "Exceeded my expectations in quality and speed of delivery. Highly recommended.", 5),
    ("Very good value for money", "Solid build quality and performs exactly as advertised. Satisfied with the purchase.", 4),
    ("Premium feel and finish", "Looks and feels amazing. Packaging was neat and delivery was prompt.", 5),
    ("Decent performance", "Good daily use item. Works well, though battery could have been slightly better.", 4),
    ("Best in this price segment", "I compared multiple brands before buying this. Unbeatable value and certified trust.", 5),
    ("Satisfied with the purchase", "Smooth experience, customer support was responsive when I had a question.", 4),
    ("Top notch quality", "Using it for two weeks now and zero complaints. Five stars without a doubt.", 5),
    ("Reliable & authentic", "Was hesitant at first but verified authenticity and QuickCart guarantee delivered.", 5),
    ("Good build quality", "Feels sturdy, well crafted and meets all listed specifications.", 4),
    ("Prompt delivery & great item", "Arrived in 2 days in immaculate packaging. 10/10.", 5),
    ("Pleasantly surprised", "The performance is noticeably better than my previous one. Glad I picked this.", 5),
    ("Worth every rupee", "Super easy to set up and very user friendly. Highly recommend.", 5),
]

def run_mass_seed():
    print("\n=======================================================")
    print("[*] QuickCart Mass Data Seeder Starting...")
    print("=======================================================\n")

    # 1. SEED 50 CUSTOMERS
    print("[1/4] Seeding 50 Customer Accounts & Addresses...")
    created_users = []
    
    # Ensure primary demo customer Maya exists
    maya, _ = User.objects.get_or_create(
        username='maya@example.com',
        defaults={
            'email': 'maya@example.com',
            'first_name': 'Maya',
            'last_name': 'Thompson',
            'phone': '+91 98765 43210',
            'theme_mode': 'light'
        }
    )
    if not maya.has_usable_password():
        maya.set_password('password123')
        maya.save()
    created_users.append(maya)

    for i in range(1, 50):
        first = FIRST_NAMES[i % len(FIRST_NAMES)]
        last = LAST_NAMES[i % len(LAST_NAMES)]
        email = f"{first.lower()}.{last.lower()}{i}@example.com"
        
        user, _ = User.objects.get_or_create(
            username=email,
            defaults={
                'email': email,
                'first_name': first,
                'last_name': last,
                'phone': f"+91 98{random.randint(10000000, 99999999)}",
                'theme_mode': random.choice(['light', 'dark'])
            }
        )
        if not user.has_usable_password():
            user.set_password('password123')
            user.save()
        created_users.append(user)

        # Create Default Address
        city, state, pcode = CITIES[i % len(CITIES)]
        Address.objects.get_or_create(
            user=user,
            defaults={
                'recipient_name': f"{first} {last}",
                'street_address': f"Flat {random.randint(101, 909)}, Block {chr(65 + (i % 6))}, Tech Park Residency",
                'city': city,
                'state': state,
                'postal_code': pcode,
                'phone': user.phone,
                'is_default': True
            }
        )

    print(f"  [+] {len(created_users)} Customer accounts and default addresses ready.")

    # 2. SEED 40+ CATEGORIES
    print("\n[2/4] Seeding 40+ Structured Categories...")
    category_objs = []
    for idx, (cname, cslug, cicon) in enumerate(CATEGORY_DEFINITIONS, start=1):
        cat = Category.objects.filter(name=cname).first() or Category.objects.filter(slug=cslug).first()
        if not cat:
            cat = Category.objects.create(name=cname, slug=cslug, icon_name=cicon, order=idx)
        else:
            cat.icon_name = cicon
            cat.order = idx
            cat.save()
        category_objs.append(cat)
    print(f"  [+] {len(category_objs)} Categories created/updated.")

    # 3. SEED 400+ PRODUCTS (10 per category)
    print("\n[3/4] Seeding 400+ Catalog Products with Specifications & Trust Badges...")
    brands = ["AeroSound", "SonicBlast", "PulseTrack", "Vanguard", "ChronoStyle", "SmartFit", "OptiMax", "Zenith", "VoltTech", "Nordic", "LuxeCraft", "Nova"]
    
    products_created = 0
    all_products = []

    for cat in category_objs:
        for p_idx in range(1, 11): # 10 products per category
            brand = random.choice(brands)
            prod_name = f"{brand} {cat.name.split('&')[0].strip()} Pro Series {p_idx}"
            slug = slugify(f"{cat.slug}-{brand.lower()}-series-{p_idx}-{products_created + 1}")
            
            price = Decimal(str(random.randint(199, 4999) + 0.99))
            orig_price = Decimal(str(float(price) * random.uniform(1.2, 1.6))).quantize(Decimal('0.01'))
            trust_score = random.randint(88, 99)
            rating = Decimal(str(round(random.uniform(4.3, 5.0), 1)))
            review_count = random.randint(15, 250)
            stock = random.randint(15, 120)
            img_url = IMAGES_POOL[(products_created + p_idx) % len(IMAGES_POOL)]

            prod, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': prod_name,
                    'category': cat,
                    'brand': brand,
                    'tagline': f"Next-gen {cat.name.lower()} with certified {trust_score}% Trust Score.",
                    'description': f"Designed for peak performance and daily reliability, {prod_name} delivers premium craft, precision engineering, and verified authenticity backed by QuickCart Buyer Protection.",
                    'price': price,
                    'original_price': orig_price,
                    'trust_score': trust_score,
                    'trust_badge_label': 'Certified Trusted' if trust_score >= 95 else 'Verified Authentic',
                    'stock': stock,
                    'main_image': img_url,
                    'rating': rating,
                    'review_count': review_count,
                    'battery_life': f"{random.randint(10, 60)} hours" if 'audio' in cat.slug or 'watch' in cat.slug else 'N/A',
                    'connectivity': 'Bluetooth 5.3 + Dual-Band Wi-Fi' if 'electronic' in cat.slug or 'phone' in cat.slug else 'Standard',
                    'warranty': f"{random.choice([1, 2])} years manufacturer warranty",
                    'specifications': {
                        'Category': cat.name,
                        'Brand': brand,
                        'Material': 'Aerospace Grade Aluminum & Polycarbonate',
                        'Certification': 'ISO-9001 & QuickCart Trust Verified',
                        'In the Box': f"1x {prod_name}, Quick Start Guide, Warranty Card, Accessories"
                    },
                    'is_trending': random.choice([True, False, False]),
                    'is_limited_offer': random.choice([True, False, False, False]),
                    'is_published': True
                }
            )
            all_products.append(prod)
            products_created += 1

            # Seed Product Image
            ProductImage.objects.get_or_create(
                product=prod,
                image_url=img_url,
                defaults={'alt_text': prod_name, 'order': 1}
            )

    print(f"  [+] {len(all_products)} Products created across {len(category_objs)} categories.")

    # 4. SEED 4000+ REVIEWS (minimum 10 per product)
    print("\n[4/4] Seeding 4,000+ Verified Reviews (Min 10 per Product)...")
    reviews_to_create = []
    
    # We will build bulk review objects for blazing fast insertion
    for prod in all_products:
        # Check existing review count
        existing_count = prod.reviews.count()
        needed = max(0, 10 - existing_count)

        for r_idx in range(needed):
            reviewer = created_users[(r_idx + prod.id) % len(created_users)]
            title, content, score = REVIEW_TEMPLATES[(r_idx + prod.id) % len(REVIEW_TEMPLATES)]
            
            reviews_to_create.append(Review(
                product=prod,
                user=reviewer,
                author_name=f"{reviewer.first_name} {reviewer.last_name}",
                title=title,
                content=content,
                rating=score,
                is_verified_purchase=True,
                created_at=timezone.now() - timedelta(days=random.randint(1, 90))
            ))

    if reviews_to_create:
        Review.objects.bulk_create(reviews_to_create, batch_size=1000)
        print(f"  [+] {len(reviews_to_create)} Reviews successfully bulk inserted into MySQL.")

    print("\n=======================================================")
    print("[SUCCESS] MASS SEEDING COMPLETE!")
    print(f"  - Total Customers: {User.objects.count()}")
    print(f"  - Total Categories: {Category.objects.count()}")
    print(f"  - Total Products: {Product.objects.count()}")
    print(f"  - Total Reviews: {Review.objects.count()}")
    print("=======================================================\n")

if __name__ == '__main__':
    run_mass_seed()
