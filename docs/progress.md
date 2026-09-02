# Progress

## Done
- Connected and extracted all 20 screens from **Flowstep MCP** (`e8b9563d-b05b-48f5-9e7f-ee19cf6d0042`).
- Set up Django 6.1 with XAMPP MySQL database (`quickcart_db`).
- Built complete data models across `accounts`, `store`, `cart`, `orders`, `support`.
- Populated database with seed script (`scripts/seed_data.py`).
- Implemented responsive frontend matching Flowstep screens with HTML5, CSS3, JavaScript, jQuery, and Bootstrap 5.
- Implemented Voice Search via Web Speech API and AJAX Autocomplete.
- Implemented Sticky Multi-Product Comparison Bar (2-3 items) and Comparison Table.
- Implemented Cart with live quantity steppers, calculations, and checkout.
- Implemented Promo Code System in Cart & Checkout with real-time AJAX validation, discount badges, and total recalculation.
- Implemented Admin Customer Support Inquiries Management (`/admin-panel/support/`) with full status filter (`All`, `Pending`, `Resolved`), inquiry details modal, and resolve handler.
- Fixed Public Help & FAQ URL collision (`/help/` and `/faq/`), allowing unauthenticated guest visitors to view FAQs directly without redirection to login.
- Upgraded Voice Search with animated listening pulse feedback, Web Speech API integration, and automatic query dispatch.
- Redesigned QuickCart AI Shopping Assistant widget with non-overlapping prompt chips, smooth horizontal scroll, high-contrast monochrome response bubbles, and clean recommendation cards.
- Configured and verified Admin test account (`admin@quickcart.com` / `admin123`) and Customer test account (`maya@example.com` / `password123`) in MySQL database.
- Completely removed demo credentials box and pre-filled inputs from login form, creating a clean login interface.
- Enforced strict role-based landing redirects: Admin automatically routes to `/admin-panel/`, Customer to `/customer/orders/`, and Guests browse without redirection.
- Added multi-image upload file selector to Admin Add and Edit Product modals with backend media storage.
- Fixed guest cart and payment security bug: enforced `@login_required` on checkout and payment, removed demo maya account fallback, and added 401 error guard on `api_add_to_cart`.
- Implemented **GenAI Product Comparison Engine** with dynamic **GenUI Verdict Card** (`/compare/`), personalized recommendations, pros/cons breakdowns, and 1-click cart addition.
- Upgraded **Natural Language AI Search** to enforce strict matching with zero irrelevant fallbacks, showing inline wishlist and cart awareness badges.
- Implemented **Admin Location-Based Delivery Rules** (`/admin-panel/shipping/`): configurable city, storewide, category, and product-specific delivery charges and free shipping rules with priority ordering.
- Implemented **Admin Homepage Banner & Promotion Manager** (`/admin-panel/banners/`): create, toggle, and reorder hero carousels and product spotlights linked to catalog items.
- Configured Store Admin as the sole seller & fulfillment entity for direct first-party e-commerce.
- Built **Admin AI Provider Key Management System** in [`/admin-panel/settings/`](http://127.0.0.1:8000/admin-panel/settings/):
  - Database-persisted configuration (`AIProviderConfig`) supporting OpenAI, OpenRouter, Google Gemini, Anthropic Claude, Groq, and xAI Grok.
  - Multi-feature integration: product comparison, AI shopping assistant chat, and complex query resolution.
  - Smart search protection: fuzzy search runs on the local algorithm first, reserving external API calls only as an emergency fallback when zero local matches are found.
  - Key Expiry Date tracking with automatic fallback to local engine upon expiration.
  - Live "Test & Verify" connectivity check and "Delete Key" reset action.
  - Usage call counter, HTTP 429 rate limit detection, and masked key display (`sk-••••••••1234`).
  - Proactive warning alerts on the Admin Dashboard (`/admin-panel/`) for expired keys, quota hits (429), or invalid credentials.
- Tested and verified with 100% passing test suite (7/7 tests OK) and HTTP 200 checks on settings and dashboard pages.

- Converted Delivery & Fulfillment System to PIN / Postal Code based rules (`/admin-panel/shipping/` and live AJAX PIN check on PDP and checkout).
- Fixed Admin Order Status Filter (`/admin-panel/orders/?status=pending`) to correctly match `placed`, `confirmed`, `processing`, and `pending` orders with active UI pill highlighting.
- Upgraded Admin Promotional Banners (`/admin-panel/banners/`) to support direct image file uploads (`image_file` ImageField stored in `media/banners/`) alongside external URLs.
- Converted Admin Reports (`/admin-panel/reports/`) into a dedicated **Customer Feedback & Reviews** stream displaying customer ratings, delivered purchase verification badges, sentiment metrics, and revenue analytics.
- Implemented **Delivered-Only Verified Reviews System**: Customers can only write, edit, or delete reviews for products that have been successfully delivered (`status='delivered'`) to their address, with strict server-side and UI security enforcement.
- Implemented **Review Pagination & Rating Tiers Filter** (`4-5 High`, `3 Mid`, `1-2 Low`) across both the Storefront Product Detail Page (`/product/<slug>/#tab-reviews`) and the Admin Customer Feedback Stream (`/admin-panel/reports/`).
- Removed the redundant "Top Rated Products" table from the Admin Feedback & Reviews page (`/admin-panel/reports/`).
- Fixed shipment tracking status display: Replaced "Estimated Delivery" badge with "Delivered Successfully" once the package is marked delivered.
- Added direct **"Write / Edit Review"** action buttons on delivered items in Customer Order Details (`/customer/orders/<order_number>/`), My Orders list (`/customer/orders/`), and Cart past orders tab (`/cart/?tab=orders`).
- **Dynamic Address System & Validation**: Replaced hardcoded dummy delivery details on the checkout/payment page (`/cart/payment/`). The checkout now dynamically queries the authenticated user's saved addresses (`Address.objects.filter(user=request.user)`), auto-populates their default address, provides an interactive address picker, and enforces strict server-side validation rejecting empty addresses before order creation.
- **Zero-Reload AJAX Review Filtering & Pagination**: Product detail page review filters (`All`, `4-5 High`, `3 Mid`, `1-2 Low`) and pagination now use smooth asynchronous AJAX requests (`filterReviewsAjax`), updating ratings and pages instantly without reloading the page.
- **Fixed "Buy Now" Direct Checkout**: Fixed the Buy Now button submitting directly to `/cart/api/add/` and dumping raw JSON in the browser. Updated `api_add_to_cart` and `buy-now-form` so Buy Now adds the item to the cart and instantly redirects the user to the Payment & Checkout page (`/cart/payment/`).
- **Fixed Hardcoded / Stale Review Count**: Fixed the Reviews tab badge (e.g., showing static `175` on LumiSmart Lamp instead of actual reviews). Updated `Product.review_count` to automatically synchronize with actual database reviews via `product.real_review_count` (`self.reviews.count()`) in [`app/models.py`](file:///d:/Projets/ecommerce_project/ecommerce_project/quickcart/app/models.py), and updated [`templates/store/product_detail.html`](file:///d:/Projets/ecommerce_project/ecommerce_project/quickcart/templates/store/product_detail.html) to render `total_reviews_count|default:product.real_review_count`.
- Removed the **"Direct First-Party Store Fulfillment"** callout banner from Admin Shipping & Delivery Management (`/admin-panel/shipping/`).

## In Progress
- None.

## Broken / Known-Bad
- None. All features tested and verified working.
