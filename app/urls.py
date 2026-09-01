from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # ==========================================
    # HTML STOREFRONT & PAGES
    # ==========================================
    path('', views.home_view, name='home'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('search/', views.search_view, name='search'),
    path('product/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('compare/', views.compare_view, name='compare'),

    # Cart & Checkout
    path('cart/', views.cart_detail_view, name='cart_detail'),
    path('cart/checkout/', views.checkout_view, name='checkout'),
    path('cart/payment/', views.payment_gateway_view, name='payment_gateway'),
    path('cart/api/add/', views.api_add_to_cart, name='api_add'),
    path('cart/api/update/', views.api_update_cart, name='api_update'),
    path('cart/api/remove/', views.api_remove_from_cart, name='api_remove'),
    path('cart/api/promo/apply/', views.api_apply_promo, name='api_apply_promo'),
    path('cart/api/promo/remove/', views.api_remove_promo, name='api_remove_promo'),

    # Content & Informational Pages
    path('about/', views.about_view, name='about'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.terms_view, name='privacy'),
    path('help/', views.help_faq_view, name='help'),
    path('faq/', views.help_faq_view, name='faq'),

    # Authentication
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/signup/', views.signup_view, name='signup'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('accounts/forgot-password/done/', views.forgot_password_done_view, name='forgot_password_done'),
    path('accounts/reset-password/', views.reset_password_view, name='reset_password_demo'),

    # Customer Portal
    path('customer/orders/', views.orders_view, name='orders'),
    path('customer/orders/<str:order_number>/', views.order_detail_view, name='order_detail'),
    path('customer/wishlist/', views.wishlist_view, name='wishlist'),
    path('customer/addresses/', views.addresses_view, name='addresses'),
    path('customer/settings/', views.settings_view, name='settings'),
    path('customer/help/', views.help_view, name='customer_help'),

    # Support
    path('support/contact/', views.contact_view, name='contact'),
    path('support/contact/success/', views.contact_success_view, name='contact_success'),

    # Admin Panel (Flowstep Screens 21-26)
    path('admin-panel/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-panel/orders/', views.admin_orders_view, name='admin_orders'),
    path('admin-panel/orders/<str:order_number>/', views.admin_order_detail_view, name='admin_order_detail'),
    path('admin-panel/orders/<str:order_number>/update-status/', views.admin_update_order_status, name='admin_update_order_status'),
    path('admin-panel/products/', views.admin_products_view, name='admin_products'),
    path('admin-panel/products/edit/<int:product_id>/', views.admin_edit_product, name='admin_edit_product'),
    path('admin-panel/products/delete/<int:product_id>/', views.admin_delete_product, name='admin_delete_product'),
    path('admin-panel/categories/create/', views.admin_create_category, name='admin_create_category'),
    path('admin-panel/customers/', views.admin_customers_view, name='admin_customers'),
    path('admin-panel/promotions/', views.admin_promotions_view, name='admin_promotions'),
    path('admin-panel/promotions/create/', views.admin_create_promotion, name='admin_create_promotion'),
    path('admin-panel/promotions/edit/<int:coupon_id>/', views.admin_edit_promotion, name='admin_edit_promotion'),
    path('admin-panel/promotions/delete/<int:coupon_id>/', views.admin_delete_promotion, name='admin_delete_promotion'),
    path('admin-panel/reports/', views.admin_reports_view, name='admin_reports'),
    path('admin-panel/support/', views.admin_support_view, name='admin_support'),
    path('admin-panel/support/resolve/<int:message_id>/', views.admin_resolve_support, name='admin_resolve_support'),
    path('admin-panel/settings/', views.admin_settings_view, name='admin_settings'),

    # AJAX Utilities
    path('api/wishlist/toggle/', views.api_toggle_wishlist, name='api_wishlist_toggle'),
    path('api/search/autocomplete/', views.api_search_autocomplete, name='api_search_autocomplete'),

    # ==========================================
    # REST API V1 ENDPOINTS (11 MODULES)
    # ==========================================
    
    # 1. Auth & Session Module
    path('api/v1/auth/signup/', api_views.api_signup, name='api_signup'),
    path('api/v1/auth/login/', api_views.api_login, name='api_login'),
    path('api/v1/auth/guest-session/', api_views.api_guest_session, name='api_guest_session'),
    path('api/v1/auth/me/', api_views.api_current_user, name='api_current_user'),

    # 2. Catalog Module
    path('api/v1/catalog/products/', api_views.api_list_products, name='api_list_products'),
    path('api/v1/catalog/products/<str:slug_or_id>/', api_views.api_product_detail, name='api_product_detail'),
    path('api/v1/catalog/categories/', api_views.api_list_categories, name='api_list_categories'),

    # 3. Seller Module (Nearby Seller Finder)
    path('api/v1/sellers/nearby/', api_views.api_nearby_sellers, name='api_nearby_sellers'),
    path('api/v1/sellers/onboard/', api_views.api_seller_onboard, name='api_seller_onboard'),

    # 4. Cart, Checkout & Orders Module
    path('api/v1/cart/', api_views.api_get_cart, name='api_get_cart'),
    path('api/v1/cart/items/', api_views.api_add_cart_item, name='api_add_cart_item'),
    path('api/v1/orders/checkout/', api_views.api_checkout, name='api_checkout'),
    path('api/v1/orders/<str:order_number>/tracking/', api_views.api_order_tracking, name='api_order_tracking'),

    # 5. Reviews & AI Trust Score Classifier
    path('api/v1/reviews/create/', api_views.api_create_review, name='api_create_review'),

    # 6. Pricing & AI Prediction Module
    path('api/v1/pricing/history/<int:product_id>/', api_views.api_price_history, name='api_price_history'),

    # 7. AI Shopping Assistant Module
    path('api/v1/assistant/message/', api_views.api_assistant_message, name='api_assistant_message'),

    # 8. Recommendations & Personalization Module
    path('api/v1/recommendations/home/', api_views.api_recommendations_home, name='api_recommendations_home'),

    # 9. Voice Search & QR Deep Linking Module
    path('api/v1/voice/query/', api_views.api_voice_search, name='api_voice_search'),
    path('api/v1/qr/generate/', api_views.api_qr_generate, name='api_qr_generate'),

    # 10. Notifications Module
    path('api/v1/notifications/', api_views.api_list_notifications, name='api_list_notifications'),

    # 11. Coupons, Audit & CSV Analytics Export
    path('api/v1/coupons/', api_views.api_list_coupons, name='api_list_coupons'),
    path('api/v1/admin/analytics/export/', api_views.api_export_sales_csv, name='api_export_sales_csv'),

    # Pluggable Internal AI Mock Endpoints
    path('api/v1/internal/classify-review/', api_views.internal_ai_classify_review, name='internal_ai_classify_review'),
    path('api/v1/internal/predict-price/', api_views.internal_ai_predict_price, name='internal_ai_predict_price'),
    path('api/v1/internal/parse-intent/', api_views.internal_ai_parse_intent, name='internal_ai_parse_intent'),
]
