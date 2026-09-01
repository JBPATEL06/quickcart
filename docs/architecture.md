# Architecture

## Tech Stack
- **Frontend**: HTML5, Vanilla CSS3 (CSS Variables, responsive layout, dark/light theme), Vanilla JavaScript, jQuery 3.7.1, AJAX, Bootstrap 5.3.3 & Bootstrap Icons.
- **Backend**: Django 6.1 (Python 3.14) with Django ORM, Templates, Context Processors, and Session authentication.
- **Database**: XAMPP MySQL / MariaDB (`quickcart_db`) via `pymysql`.

## Key Decisions
- **PyMySQL with MySQLdb patch**: Enabled seamless connection between Django 6.1 and XAMPP MySQL without C-compiler prerequisites on Windows.
- **Unified Single App Architecture**: Consolidated all modules into `app/` (`models.py`, `views.py`, `api_views.py`, `ai_services.py`, `urls.py`) to eliminate IDE clutter and file fragmentation.
- **11-Module REST API (`/api/v1/`)**: Complete RESTful interface covering Auth, Catalog, Nearby Sellers, Cart & Checkout, AI Reviews, Price Prediction, AI Shopping Assistant, Recommendations, Voice/QR, Notifications, and Admin Analytics.
- **Pluggable AI Interfaces**: Rule-based mock implementations for Fake Review Classification, Price Trend Prediction, and NLP Shopping Intent Parsing.
- **Haversine Nearby Seller Calculation**: Real-time geographic radius distance calculation in kilometers.

## Folder / File Map
- `quickcart_project/`: Master Django configuration, MySQL settings, and root dispatcher.
- `app/`:
  - `models.py`: Unified database tables (30+ entities across all 11 modules).
  - `views.py`: Server-rendered storefront, customer portal, and admin controllers.
  - `api_views.py`: REST API endpoints for all 11 modules with standard `{ success, data, error }` envelopes.
  - `ai_services.py`: Pluggable AI engines (Fake Review Classifier, Price Predictor, NLP Assistant, Haversine Seller Finder, Activity Logger).
  - `urls.py`: Master URL dispatcher mapping storefront HTML and `/api/v1/` routes.
  - `admin.py`: Django Admin dashboard model registrations.
  - `tests.py`: Automated integration test suite.
- `static/css/style.css`: Flowstep design tokens, themes, cards, steppers, and admin styling.
- `static/js/main.js`: Theme toggle, Voice Search, Autocomplete, Promo Code engine, and AJAX cart handlers.
- `templates/`:
  - `admin/`: Screen 21–26 admin dashboard and management templates.
  - `customer/`: Customer portal templates.
  - `store/`, `cart/`, `accounts/`, `support/`: Storefront templates.

