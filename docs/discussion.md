# Discussion

## [2026-09-01] QuickCart Web Application Build & Verification Session

**What was discussed:**
- User requested checking QuickCart in Kankali MCP Drive, connecting Flowstep MCP, and implementing the front-end and back-end web application matching the Flowstep screens.
- User specified strict technology stack: HTML, CSS, JavaScript (with jQuery, AJAX, and Bootstrap 5), Django (Python), and XAMPP MySQL database.

**Decisions made:**
- Used Flowstep design file `e8b9563d-b05b-48f5-9e7f-ee19cf6d0042` containing all 20 guest and customer panel screens.
- Configured Django with PyMySQL and compatibility patch for XAMPP MariaDB/MySQL without RETURNING insert constraints.
- Integrated Web Speech API for voice search mic on header.
- Implemented persistent sticky compare bar for 2–3 products.
- Seeded realistic product catalog with Trust Scores, Specs, and demo user `maya@example.com`.

**Changes made to code/project:**
- Created Django project and apps (`accounts`, `store`, `cart`, `orders`, `support`).
- Created custom models, views, URL routes, context processors, and migrations on XAMPP MySQL `quickcart_db`.
- Created master stylesheet `static/css/style.css`, interactive JavaScript `static/js/main.js`, and semantic templates matching Flowstep screens.
- Verified all user flows via browser subagent with visual proof.
- Cleaned up legacy non-Django folders (`backend/`, `frontend/`, `ai_models/`, `PLAN.md`).
- Added `.vscode/settings.json` to automatically hide `__pycache__` and `.pyc` from the file explorer, and added `.gitignore`.
- Consolidated 5 separate Django app folders (`accounts`, `store`, `cart`, `orders`, `support`) into a single clean `app/` folder with 1 `models.py`, 1 `views.py`, and 1 `urls.py`.
- Fixed theme contrasts: resolved button hover blend issues, added theme-adaptive `.qc-pill-btn`, ensured high-contrast text and dark mode card surfaces, and verified in browser.
- Implemented Promo Code engine in Shopping Cart & Checkout with dynamic discount calculations (`QUICK20`, `WELCOME10`, `FLAT50`, `FREESHIP`), instant AJAX apply/remove, and verified live in browser.
- Converted all blue outlines, icons, focus rings, hover borders, and text to high-contrast monochrome (crisp black in light mode and pure white in dark mode).
- Added Dashboard Sub-Navbar with "Back to Shopping" action, breadcrumb trail, "Browse Categories", "View Cart", and sidebar "Continue Shopping" link.
- Implemented QuickCart Admin Panel Frontend (Flowstep Screens 21-26: Dashboard Overview, Orders Management, Product Catalog, Customers, Promotions, Reports & Analytics, Settings) with live KPI cards, sales trend chart, donut order meter, and light/dark theme switching.
- Implemented complete 11-Module Backend Architecture & REST APIs (`/api/v1/`) with MySQL schema migration, pluggable AI mocks (review classifier, price predictor, NLP intent parser), Haversine nearby seller finder, and automated integration test suite (7/7 passed).
- Built Dedicated Admin Order Details View (`/admin-panel/orders/<order_number>/`) keeping admins strictly within the Admin layout.
- Added Product Management with Edit Product Modal, Delete Product confirmation, and "Add Custom Category" on-the-fly creator.
- Added Customer Profile Overview Modal displaying lifetime spend, orders count, default address, and join date.
- Added Dynamic Promotions Management with Create, Edit, Delete coupon modals and real `Coupon` database records.
- Built 100% Dynamic Admin Dashboard with real DB revenue and order metrics, live Chart.js sales trajectory, order fulfillment donut distribution, Recent Orders list, and Needs Attention alerts.
- Added Universal Numbered Pagination across Storefront Search, Category pages, Admin Orders, Admin Products, and Admin Customers.
- Implemented Amazon-Style Category Navigation (Header "All Departments" megamenu dropdown + search sidebar top 8 categories with "+ Show all 40+ categories" accordion).
- Added `QuickCartAuthRoleMiddleware` enforcing clean session isolation: prevents logged-in users from accessing login/signup and blocks non-staff users from accessing `/admin-panel/*`.
- Added Dedicated Admin Customer Support Inquiries Management (`/admin-panel/support/`) with status filtering (`All`, `Pending`, `Resolved`), customer inquiry details modal, and instant resolve action.
- Resolved Help & FAQ footer redirect issue by separating public `help_faq_view` (`/help/`) from customer portal `customer_help` (`/customer/help/`), enabling seamless guest access to store policies without requiring login.
- Upgraded Voice Search with animated pulse state, Web Speech API speech-to-text transcription, and automated query submission.
- Completely redesigned the QuickCart AI Assistant widget with non-overlapping prompt chips, smooth horizontal scroll, high-contrast monochrome response bubbles, and clean recommendation cards.
- Overhauled color palette to complete Monochrome Black & White styling, eliminating all blue accent colors across buttons, text, active links, focus rings, and badges.
- Created and verified active database credentials for Admin test user (`admin@quickcart.com` / `admin123`) and Customer test user (`maya@example.com` / `password123`) in MySQL.
- Completely removed the demo credentials banner and prefilled form values from `templates/accounts/login.html`, presenting a clean, secure login surface.
- Hardened login redirection: Admins landing on login are routed strictly to `/admin-panel/`, Customers to `/customer/orders/`, and Guests browse freely across the storefront.
- Integrated multi-image file uploads with `FileSystemStorage` in the Admin Product Catalog modals.
- Completed comprehensive visual verification with browser subagent and verified test suite pass (7/7 tests OK).

**Open questions / follow-ups:**
- Phase 2 ML-based recommendation refinements when needed.
