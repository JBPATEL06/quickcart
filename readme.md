# QuickCart 🛒

QuickCart is an e-commerce platform built with **Django 5+** and **MySQL (XAMPP)**.

---

## 📋 Prerequisites

Before running the project, ensure you have the following installed on your system:

- **Python 3.10+** — [Download Python](https://www.python.org/downloads/)
- **Git** — [Download Git](https://git-scm.com/)
- **XAMPP / MySQL Server** — [Download XAMPP](https://www.apachefriends.org/)

---

## 🚀 Setup & Installation Guide

Follow these step-by-step instructions after cloning the repository.

### 1. Clone the Repository
```bash
git clone <repository-url>
cd quickcart
```

### 2. Create and Activate a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup (MySQL / XAMPP)
1. Start **MySQL** from your **XAMPP Control Panel**.
2. Open phpMyAdmin at `http://localhost/phpmyadmin/` (or use MySQL CLI).
3. Create a new database named `quickcart_db`.

> **Default Database Configuration in `quickcart_project/settings.py`:**
> - **Host:** `127.0.0.1`
> - **Port:** `3306`
> - **Database Name:** `quickcart_db`
> - **User:** `root`
> - **Password:** `""` (empty)

### 5. Apply Database Migrations
Create the database tables schema:
```bash
python manage.py migrate
```

### 6. (Optional) Seed Sample Data
Populate the database with sample products, categories, users, and orders:
```bash
python scripts/seed_data.py
```

### 7. Create an Admin Account
To access the admin dashboard, create a superuser:
```bash
python manage.py createsuperuser
```

### 8. Run the Development Server
```bash
python manage.py runserver
```

---

## 🌐 Accessing the Application

- **Store Front:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Admin Dashboard:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 📌 Project TODOs & Notes
- Admin: Order filter pending issue resolution
- Admin banner: Allow file upload support
- Convert report section to feedback view
- Review system: Allow user write/edit/delete reviews only for delivered products
