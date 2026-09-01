from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Address, Category, Product, ProductImage, 
    Review, Wishlist, Cart, CartItem, Order, OrderItem, 
    OrderTrackingEvent, SupportMessage, FAQItem, Coupon, ReviewFlag
)

# User & Address
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'is_staff')

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('recipient_name', 'user', 'label', 'city', 'state', 'is_default')

# Store & Products
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'trust_score', 'rating', 'stock', 'is_trending')
    list_filter = ('category', 'is_trending', 'is_limited_offer')
    search_fields = ('name', 'brand', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'product', 'author_name', 'rating', 'trust_tag', 'created_at')

@admin.register(ReviewFlag)
class ReviewFlagAdmin(admin.ModelAdmin):
    list_display = ('review', 'suspicion_score', 'flag_reason', 'status', 'is_moderated', 'created_at')
    list_filter = ('status', 'is_moderated')

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'discount_type', 'discount_value', 'is_active', 'valid_until')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code', 'title')

# Cart
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'total_items', 'created_at')
    inlines = [CartItemInline]

# Orders
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderTrackingEventInline(admin.TabularInline):
    model = OrderTrackingEvent
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'recipient_name', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'recipient_name', 'phone')
    inlines = [OrderItemInline, OrderTrackingEventInline]

# Support
@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'order_number', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('name', 'email', 'order_number', 'message')

@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order')
    list_filter = ('category',)

