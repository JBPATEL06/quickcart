import uuid
import random
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.conf import settings

# ==========================================
# 1. USER, ROLES & AUDIT LOG MODELS
# ==========================================

class AdminRole(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list, help_text="List of granted permission keys")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
        ('superadmin', 'Super Admin'),
    ]

    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    admin_role = models.ForeignKey(AdminRole, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    theme_mode = models.CharField(max_length=10, choices=[('light', 'Light'), ('dark', 'Dark')], default='light')
    
    # 2FA and Security
    is_two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=64, blank=True, null=True)
    auth_provider = models.CharField(max_length=30, default='email') # email, google, apple, phone_otp

    # Preferences
    email_notifications = models.BooleanField(default=True)
    order_updates = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)

    @property
    def initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.first_name:
            return self.first_name[:2].upper()
        elif self.username:
            return self.username[:2].upper()
        return "QC"

    @property
    def display_name(self):
        if self.first_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username

    def has_admin_permission(self, permission_key):
        if self.is_superuser or self.role == 'superadmin':
            return True
        if self.admin_role and permission_key in self.admin_role.permissions:
            return True
        return False

    def __str__(self):
        return self.display_name or self.username


class AdminAuditLog(models.Model):
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('status_change', 'Status Change'),
        ('override', 'Manual Override'),
        ('login_2fa', '2FA Login'),
    ]

    admin_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    target_entity = models.CharField(max_length=100) # e.g. "Product", "Order", "ReviewFlag"
    target_id = models.CharField(max_length=100)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.admin_user} - {self.action_type} on {self.target_entity} #{self.target_id}"


class Address(models.Model):
    ADDRESS_TYPES = [
        ('default', 'Default'),
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=20, choices=ADDRESS_TYPES, default='home')
    recipient_name = models.CharField(max_length=100)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='India')
    phone = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.recipient_name} ({self.get_label_display()}) - {self.city}"


# ==========================================
# 2. CATALOG & COMPARISON MODELS
# ==========================================

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    icon_name = models.CharField(max_length=50, default='bi-grid', help_text='Bootstrap Icon Name')
    description = models.TextField(blank=True)
    image_url = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ComparisonAttribute(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='comparison_attributes')
    name = models.CharField(max_length=100) # e.g. "Battery Life", "Noise Cancellation", "Warranty"
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.category.name} -> {self.name}"


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    brand = models.CharField(max_length=100, default='QuickCart Brand')
    tagline = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    trust_score = models.PositiveIntegerField(default=92)
    trust_badge_label = models.CharField(max_length=50, default='Trusted')
    stock = models.PositiveIntegerField(default=50)
    main_image = models.CharField(max_length=500)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.8)
    review_count = models.PositiveIntegerField(default=248)
    
    battery_life = models.CharField(max_length=100, default='40 hours', blank=True)
    connectivity = models.CharField(max_length=100, default='Bluetooth 5.3', blank=True)
    warranty = models.CharField(max_length=100, default='1 year', blank=True)
    specifications = models.JSONField(default=dict, blank=True)

    is_published = models.BooleanField(default=True)
    is_trending = models.BooleanField(default=False)
    is_limited_offer = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_trending', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0

    def recalculate_trust_score(self):
        """Recompute trust score from non-flagged reviews"""
        clean_reviews = self.reviews.filter(flags__status__in=['approved', None]).exclude(flags__status='flagged_fake')
        if clean_reviews.exists():
            avg_rating = clean_reviews.aggregate(models.Avg('rating'))['rating__avg'] or 4.5
            # Trust score formula: weighted by verified percentage and average rating
            score = min(100, int((avg_rating / 5.0) * 80 + 18))
            self.trust_score = score
            self.rating = round(avg_rating, 1)
            self.review_count = clean_reviews.count()
            self.save(update_fields=['trust_score', 'rating', 'review_count'])

    def __str__(self):
        return f"{self.name} (₹{self.price})"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url = models.CharField(max_length=500)
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specs')
    spec_key = models.CharField(max_length=100) # e.g. "Weight", "Frequency Response"
    spec_value = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'spec_key']

    def __str__(self):
        return f"{self.product.name}: {self.spec_key} = {self.spec_value}"


# ==========================================
# 3. SELLER MODULE (KYC & NEARBY FINDER)
# ==========================================

class Seller(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending KYC'),
        ('verified', 'Verified'),
        ('suspended', 'Suspended'),
    ]

    business_name = models.CharField(max_length=150)
    owner_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=28.6139) # Delhi default
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=77.2090)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.9)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.business_name} ({self.city}) - {self.get_status_display()}"


class SellerDocument(models.Model):
    DOC_TYPES = [
        ('gst', 'GST Registration Certificate'),
        ('pan', 'Company PAN Card'),
        ('identity', 'Government ID Proof'),
        ('address_proof', 'Business Address Proof'),
    ]
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOC_TYPES)
    file_url = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    rejection_reason = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.seller.business_name} - {self.get_document_type_display()}"


class SellerInventory(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='inventories')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='seller_stocks')
    stock = models.PositiveIntegerField(default=10)
    local_price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_days = models.PositiveIntegerField(default=1, help_text="Estimated local delivery days")
    is_available = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('seller', 'product')

    def __str__(self):
        return f"{self.seller.business_name}: {self.product.name} ({self.stock} in stock)"


# ==========================================
# 4. REVIEWS & AI TRUST SCORE CLASSIFIER
# ==========================================

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    author_name = models.CharField(max_length=100, default='Verified Customer')
    title = models.CharField(max_length=150)
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)
    trust_tag = models.CharField(max_length=50, default='Trusted')
    is_verified_purchase = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.rating}★ by {self.author_name}"


class ReviewFlag(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Moderation'),
        ('approved', 'Approved Real Review'),
        ('flagged_fake', 'Marked Fake/Spam'),
        ('escalated', 'Escalated to Senior Team'),
    ]

    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='flags')
    suspicion_score = models.PositiveSmallIntegerField(default=0, help_text="0 (Real) to 100 (Highly Suspicious Bot/Spam)")
    flag_reason = models.CharField(max_length=255, blank=True)
    ai_classification_details = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_moderated = models.BooleanField(default=False)
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_reviews')
    moderated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-suspicion_score', '-created_at']

    def __str__(self):
        return f"Flag on Review #{self.review_id} (Suspicion: {self.suspicion_score}%)"


# ==========================================
# 5. PRICING HISTORY & AI PRICE PREDICTIONS
# ==========================================

class PriceHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_history')
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.product.name}: ₹{self.old_price} -> ₹{self.new_price}"


class PricePrediction(models.Model):
    TREND_CHOICES = [
        ('drop', 'Likely to Drop'),
        ('stable', 'Price Stable'),
        ('rise', 'Likely to Rise'),
    ]

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='price_prediction')
    predicted_trend = models.CharField(max_length=20, choices=TREND_CHOICES, default='stable')
    confidence_score = models.PositiveSmallIntegerField(default=85, help_text="AI confidence %")
    suggestion_text = models.CharField(max_length=255, default='Best time to buy in current cycle.')
    predicted_next_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} Prediction: {self.get_predicted_trend_display()} ({self.confidence_score}%)"


class PriceDropAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='price_alerts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_alerts')
    target_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    triggered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.email} -> {self.product.name} @ ₹{self.target_price}"


# ==========================================
# 6. CART, COUPONS, WISHLIST & ORDERS
# ==========================================

class Coupon(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage Discount'),
        ('fixed', 'Fixed Amount Discount'),
        ('free_shipping', 'Free Delivery'),
    ]

    DISCOUNT_SCOPES = [
        ('all', 'All Products / Entire Order'),
        ('category', 'Specific Category'),
    ]

    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=150, default='Special Offer')
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_discount_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Auto-apply vs Coupon-based
    is_auto_apply = models.BooleanField(default=False, help_text="If True, auto-applies without needing coupon code")
    discount_scope = models.CharField(max_length=20, choices=DISCOUNT_SCOPES, default='all')
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='promotions')

    valid_until = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(default=1000)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_savings(self, subtotal_amount):
        sub = float(subtotal_amount)
        if sub < float(self.min_order_amount):
            return 0.00
        if self.discount_type == 'percentage':
            savings = sub * (float(self.discount_value) / 100.0)
            if self.max_discount_limit:
                savings = min(savings, float(self.max_discount_limit))
            return round(savings, 2)
        elif self.discount_type == 'fixed':
            return round(min(float(self.discount_value), sub), 2)
        elif self.discount_type == 'free_shipping':
            return 0.00 # Handled in shipping fee deduction
        return 0.00

    def __str__(self):
        auto_label = " (Auto-Apply)" if self.is_auto_apply else ""
        return f"{self.code}{auto_label} ({self.get_discount_type_display()} - {self.discount_value})"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    notify_on_discount = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.product.name}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    promo_code = models.CharField(max_length=50, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def estimated_shipping(self):
        if self.promo_code == 'FREESHIP' or (self.coupon and self.coupon.discount_type == 'free_shipping') or self.subtotal > 999 or self.subtotal == 0:
            return 0
        return 50

    @property
    def estimated_tax(self):
        taxable = max(0, float(self.subtotal) - float(self.discount_amount))
        return round(taxable * 0.05, 2)

    @property
    def grand_total(self):
        total = max(0, float(self.subtotal) - float(self.discount_amount)) + self.estimated_shipping + self.estimated_tax
        return round(total, 2)

    def recalculate_discounts(self):
        # 1. Manual coupon code applied
        if self.coupon and not self.coupon.is_auto_apply:
            if self.coupon.discount_scope == 'category' and self.coupon.category:
                cat_subtotal = sum(item.total_price for item in self.items.filter(product__category=self.coupon.category))
                self.discount_amount = self.coupon.calculate_savings(cat_subtotal)
            else:
                self.discount_amount = self.coupon.calculate_savings(self.subtotal)
            self.save()
            return self.discount_amount

        # 2. Check for automatic storewide/category promotions
        auto_promos = Coupon.objects.filter(is_active=True, is_auto_apply=True)
        best_savings = 0.0
        best_promo = None
        
        for promo in auto_promos:
            if promo.discount_scope == 'category' and promo.category:
                cat_subtotal = sum(item.total_price for item in self.items.filter(product__category=promo.category))
                savings = promo.calculate_savings(cat_subtotal)
            else:
                savings = promo.calculate_savings(self.subtotal)
                
            if savings > best_savings:
                best_savings = savings
                best_promo = promo

        if best_promo and best_savings > 0:
            self.coupon = best_promo
            self.promo_code = best_promo.code
            self.discount_amount = best_savings
            self.save()
        elif self.coupon and self.coupon.is_auto_apply:
            self.coupon = None
            self.promo_code = None
            self.discount_amount = 0.0
            self.save()

        return self.discount_amount

    def __str__(self):
        return f"Cart #{self.id} ({self.user or self.session_key})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')

    @property
    def total_price(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('placed', 'Placed'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='placed')
    recipient_name = models.CharField(max_length=100)
    shipping_address = models.TextField()
    phone = models.CharField(max_length=20)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    promo_code = models.CharField(max_length=50, blank=True, null=True)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='Card ending in 4242')
    is_paid = models.BooleanField(default=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    carrier = models.CharField(max_length=100, default='QuickCart Express')
    estimated_delivery = models.CharField(max_length=100, default='3-5 business days')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @classmethod
    def generate_order_number(cls):
        return f"QC-{random.randint(10000, 99999)}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"Order #{self.order_number}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    image_url = models.CharField(max_length=500, blank=True)

    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"


class OrderTrackingEvent(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking_events')
    stage = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField()
    is_completed = models.BooleanField(default=True)
    order_step = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['order_step']

    def __str__(self):
        return f"{self.order.order_number} - {self.title}"


# ==========================================
# 7. AI ASSISTANT, CONVERSATIONS & INTENT
# ==========================================

class AssistantConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='assistant_conversations')
    session_id = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=150, default='Shopping Advice')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation #{self.id} ({self.session_id})"


class AssistantMessage(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('assistant', 'AI Assistant'),
    ]

    conversation = models.ForeignKey(AssistantConversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES)
    message_text = models.TextField()
    parsed_intent = models.JSONField(default=dict, blank=True) # {budget, category, preference}
    suggested_products = models.JSONField(default=list, blank=True) # List of product IDs/cards with rationale
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.sender}] {self.message_text[:40]}..."


# ==========================================
# 8. RECOMMENDATIONS & USER ACTIVITY LOG
# ==========================================

class UserActivityLog(models.Model):
    ACTIVITY_TYPES = [
        ('view', 'View Product'),
        ('search', 'Search Query'),
        ('wishlist_add', 'Add to Wishlist'),
        ('cart_add', 'Add to Cart'),
        ('compare', 'Add to Compare'),
        ('purchase', 'Purchase Order'),
    ]

    session_id = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    search_query = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.activity_type} by {self.user or self.session_id} @ {self.timestamp}"


class RecommendationSettings(models.Model):
    view_weight = models.FloatField(default=1.0)
    cart_weight = models.FloatField(default=3.0)
    wishlist_weight = models.FloatField(default=2.5)
    purchase_weight = models.FloatField(default=5.0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Recommendation Weights (View: {self.view_weight}, Buy: {self.purchase_weight})"


class RecommendationExclusion(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    reason = models.CharField(max_length=200, default='Excluded from public feed')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Excluded Product: {self.product.name}"


# ==========================================
# 9. VOICE SEARCH & QR MARKETING DEEP LINKS
# ==========================================

class VoiceSearchLog(models.Model):
    session_id = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    transcript = models.CharField(max_length=255)
    duration_ms = models.PositiveIntegerField(default=1200)
    matched_products_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Voice Search: '{self.transcript}' ({self.matched_products_count} results)"


class QRShare(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='qr_shares')
    campaign_name = models.CharField(max_length=100, default='Product Deep Link')
    qr_code_token = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    deep_link_url = models.CharField(max_length=500)
    scan_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"QR for {self.product.name} ({self.scan_count} scans)"


# ==========================================
# 10. NOTIFICATION ENGINE
# ==========================================

class NotificationTemplate(models.Model):
    slug = models.SlugField(max_length=50, unique=True)
    title_template = models.CharField(max_length=200)
    body_template = models.TextField()

    def __str__(self):
        return self.slug


class Notification(models.Model):
    TYPE_CHOICES = [
        ('price_drop', 'Price Drop Alert'),
        ('order_status', 'Order Shipment Update'),
        ('discount_alert', 'Wishlist Discount Offer'),
        ('assistant_alert', 'AI Personal Shopper Recommendation'),
        ('system', 'System Notice'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='system')
    title = models.CharField(max_length=200)
    body = models.TextField()
    related_link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.user.email}: {self.title}"


# ==========================================
# 11. CMS & HOMEPAGE BANNERS
# ==========================================

class HomepageBanner(models.Model):
    title = models.CharField(max_length=150)
    subtitle = models.CharField(max_length=255, blank=True)
    badge_text = models.CharField(max_length=50, default='Limited Offer')
    image_url = models.CharField(max_length=500)
    cta_text = models.CharField(max_length=50, default='Shop Now')
    cta_link = models.CharField(max_length=255, default='/category/electronics/')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title


class SupportMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    order_number = models.CharField(max_length=50, blank=True)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.name}"


class FAQItem(models.Model):
    CATEGORIES = [
        ('orders', 'Orders & Delivery'),
        ('payment', 'Payments & Account'),
        ('returns', 'Returns & Refunds'),
        ('general', 'General'),
    ]

    category = models.CharField(max_length=50, choices=CATEGORIES, default='orders')
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['category', 'order']

    def __str__(self):
        return self.question
