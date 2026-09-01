import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from app.models import (
    User, Category, Product, Cart, CartItem, Order,
    Seller, SellerInventory, Review, Coupon, Address
)

class QuickCart11ModuleIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()

        # 1. Test User
        self.user = User.objects.create_user(
            username='tester@example.com',
            email='tester@example.com',
            password='testpassword123',
            first_name='Alex',
            last_name='Tester'
        )

        # 2. Test Category & Product
        self.category = Category.objects.create(name='Audio', slug='audio', icon_name='bi-headphones')
        self.product = Product.objects.create(
            category=self.category,
            name='QuickSound Elite Headphones',
            slug='quicksound-elite',
            price=Decimal('150.00'),
            original_price=Decimal('200.00'),
            trust_score=90,
            stock=25,
            main_image='https://images.unsplash.com/photo-1505740420928-5e560c06d30e'
        )

        # 3. Test Coupon
        self.coupon = Coupon.objects.create(
            code='SAVE20',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            min_order_amount=Decimal('50.00'),
            is_active=True
        )

        # 4. Test Verified Seller
        self.seller = Seller.objects.create(
            business_name='Bangalore Central Audio',
            owner_name='Vikram Rao',
            email='vikram@example.com',
            phone='+91 99999 88888',
            address='MG Road',
            city='Bengaluru',
            postal_code='560001',
            latitude=Decimal('12.9716'),
            longitude=Decimal('77.5946'),
            status='verified'
        )
        SellerInventory.objects.create(
            seller=self.seller,
            product=self.product,
            stock=10,
            local_price=Decimal('145.00'),
            delivery_days=1,
            is_available=True
        )

    def test_01_auth_and_guest_session(self):
        # Test Guest Session
        res = self.client.get('/api/v1/auth/guest-session/')
        self.assertEqual(res.status_code, 200)
        data = res.json()['data']
        self.assertTrue('session_id' in data)

        # Test Signup
        res_signup = self.client.post('/api/v1/auth/signup/', json.dumps({
            'email': 'newuser@example.com',
            'password': 'Password@123',
            'first_name': 'New',
            'last_name': 'Shopper'
        }), content_type='application/json')
        self.assertEqual(res_signup.status_code, 201)

    def test_02_catalog_endpoints(self):
        # Product listing
        res = self.client.get('/api/v1/catalog/products/?category=audio')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['data'][0]['name'], 'QuickSound Elite Headphones')

        # Product detail with price prediction
        res_detail = self.client.get(f'/api/v1/catalog/products/{self.product.slug}/')
        self.assertEqual(res_detail.status_code, 200)
        detail = res_detail.json()['data']
        self.assertEqual(detail['name'], 'QuickSound Elite Headphones')
        self.assertTrue('price_prediction' in detail)

    def test_03_nearby_seller_finder(self):
        # Given Bangalore GPS coordinates (12.9352, 77.6245)
        res = self.client.get(f'/api/v1/sellers/nearby/?product_id={self.product.id}&lat=12.9352&lng=77.6245&radius_km=25')
        self.assertEqual(res.status_code, 200)
        sellers = res.json()['data']
        self.assertGreaterEqual(len(sellers), 1)
        self.assertEqual(sellers[0]['business_name'], 'Bangalore Central Audio')
        self.assertLess(sellers[0]['distance_km'], 10.0)

    def test_04_cart_checkout_and_order_tracking(self):
        self.client.login(username='tester@example.com', password='testpassword123')

        # Add Item to Cart
        res_add = self.client.post('/api/v1/cart/items/', json.dumps({
            'product_id': self.product.id,
            'quantity': 2
        }), content_type='application/json')
        self.assertEqual(res_add.status_code, 200)

        # Checkout
        res_checkout = self.client.post('/api/v1/orders/checkout/', json.dumps({
            'recipient_name': 'Alex Tester',
            'shipping_address': 'Flat 102, Palm Residency',
            'phone': '+91 99999 00000',
            'payment_method': 'Card ending in 4242'
        }), content_type='application/json')
        self.assertEqual(res_checkout.status_code, 201)
        order_data = res_checkout.json()['data']
        order_num = order_data['order_number']

        # Order Tracking
        res_track = self.client.get(f'/api/v1/orders/{order_num}/tracking/')
        self.assertEqual(res_track.status_code, 200)
        track_data = res_track.json()['data']
        self.assertEqual(track_data['order_number'], order_num)
        self.assertGreaterEqual(len(track_data['tracking_events']), 1)

    def test_05_review_and_ai_fake_classifier(self):
        # 1. Clean Review
        res_clean = self.client.post('/api/v1/reviews/create/', json.dumps({
            'product_id': self.product.id,
            'title': 'Outstanding sound quality',
            'content': 'Crisp highs and deep bass. Comfortable ear cushions for all-day wear.',
            'rating': 5
        }), content_type='application/json')
        self.assertEqual(res_clean.status_code, 201)
        self.assertEqual(res_clean.json()['data']['moderation_status'], 'approved')

        # 2. Spam / Fake Review
        res_spam = self.client.post('/api/v1/reviews/create/', json.dumps({
            'product_id': self.product.id,
            'title': 'Click here for free bonus',
            'content': 'Visit http://spam-site.com to get free vouchers! best best best',
            'rating': 5
        }), content_type='application/json')
        self.assertEqual(res_spam.status_code, 201)
        self.assertGreaterEqual(res_spam.json()['data']['suspicion_score'], 60)
        self.assertEqual(res_spam.json()['data']['moderation_status'], 'flagged_fake')

    def test_06_ai_shopping_assistant(self):
        # Test Query: "I want headphones under 200"
        res_ai = self.client.post('/api/v1/assistant/message/', json.dumps({
            'message': 'Looking for great headphones under ₹200 with good battery'
        }), content_type='application/json')
        self.assertEqual(res_ai.status_code, 200)
        data = res_ai.json()['data']
        self.assertEqual(data['parsed_intent']['budget'], 200.0)
        self.assertGreaterEqual(len(data['suggested_products']), 1)
        self.assertEqual(data['suggested_products'][0]['name'], 'QuickSound Elite Headphones')

    def test_07_recommendations_and_voice_search(self):
        # Recommendations
        res_rec = self.client.get('/api/v1/recommendations/home/')
        self.assertEqual(res_rec.status_code, 200)
        self.assertGreaterEqual(len(res_rec.json()['data']), 1)

        # Voice Search
        res_voice = self.client.post('/api/v1/voice/query/', json.dumps({
            'transcript': 'QuickSound'
        }), content_type='application/json')
        self.assertEqual(res_voice.status_code, 200)
        self.assertGreaterEqual(len(res_voice.json()['data']['results']), 1)
