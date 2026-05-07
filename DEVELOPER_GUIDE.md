# Ellar Mini Mart IMS - Developer Quick Start Guide

## Prerequisites
- Python 3.13+
- Django 6.0.3
- SQLite3
- Modern web browser

## Installation & Setup

### 1. Clone/Setup Project
```bash
cd EllarStore
```

### 2. Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply Migrations
```bash
python manage.py migrate
```

### 5. Create Admin User
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
admin = User.objects.create_user(
    username='EllarMiniMart',
    email='admin@ellarminimart.com',
    password='AdminPassword123!',
    is_staff=True,
    is_superuser=True
)
print("Admin user created successfully!")
exit()
```

### 6. Start Development Server
```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:8000/`

---

## Project Structure

```
EllarStore/
├── config/                      # Django configuration
│   ├── settings.py              # Main settings
│   ├── urls.py                  # URL routing
│   ├── wsgi.py                  # Production server config
│   └── asgi.py                  # Async server config
│
├── inventory/                   # Main app
│   ├── models.py                # Database models
│   ├── views.py                 # Business logic
│   ├── forms.py                 # Form definitions
│   ├── urls.py                  # App URL routing
│   ├── admin.py                 # Admin interface config
│   ├── signals.py               # Signal handlers
│   ├── apps.py                  # App configuration
│   ├── migrations/              # Database migrations
│   └── tests.py                 # Unit tests
│
├── templates/                   # HTML templates
│   ├── base.html                # Legacy base
│   ├── modern_base.html         # Main layout template
│   └── inventory/               # App-specific templates
│       ├── modern_dashboard.html
│       ├── modern_pos.html
│       ├── modern_product_list.html
│       ├── modern_product_form.html
│       ├── modern_reports.html
│       ├── settings.html        # NEW: Settings page
│       ├── user_register.html   # UPDATED: Registration
│       └── ...
│
├── static/                      # Static files
│   ├── modern-styles.css        # Main stylesheet
│   └── styles.css               # Legacy styles
│
├── scripts/                     # Utility scripts
│   └── manual_checks/           # Testing scripts
│
├── db.sqlite3                   # Database file
├── manage.py                    # Django management
├── requirements.txt             # Python dependencies
├── README.md                    # Project readme
├── IMPLEMENTATION_REPORT.md     # NEW: Implementation details
└── USER_GUIDE.md                # NEW: User manual
```

---

## Database Schema

### New/Updated Models (Migration 0011)
```python
# UserProfile - Theme preferences per user
- user (OneToOne to User)
- dark_mode (Boolean)
- primary_color (choices: pink, blue, green, purple, orange, red, teal, indigo)
- created_at, updated_at

# UserRegistration - Pending user accounts
- username, email, first_name, last_name
- phone, location (NEW in 0011)
- branch (NEW in 0011)
- password (hashed)
- is_approved
- created_at, approved_at, approved_by

# Notification - Admin alerts
- type (choices)
- title, message
- created_by
- created_at, is_read
- product, transaction (optional)
- quantity

# Transaction - Sales records
- transaction_id (unique)
- subtotal, discount, total
- cash_received, change
- created_at

# TransactionItem - Sale line items
- transaction (ForeignKey)
- product, quantity, unit_price
- subtotal

# Product - Inventory items
- name, sku, product_type, quantity
- purchase_price, unit_price
- expiration_date, reorder_level
- total_sold, created_at, updated_at

# StockMovement - Inventory adjustments
- product (ForeignKey)
- movement_type (IN/OUT)
- quantity, note, created_at
```

---

## Key Views & URL Patterns

### Authentication
- `POST /login/` → `login_view()`
- `GET /logout/` → `logout_view()`
- `POST /register/` → `register_user()`

### Core Features
- `GET /dashboard/` → `dashboard()`
- `GET /pos/` → `pos()`
- `GET /products/` → `product_list()`
- `GET /reports/` → `reports()`
- `GET /settings/` → `settings_view()`

### APIs
- `GET /api/theme-config/` → `api_theme_config()`
- `POST /api/update-theme/` → `api_update_theme()`
- `GET /api/notifications/` → `api_notifications()`

### POS APIs
- `POST /pos/search/` → `pos_search_product()`
- `POST /pos/add-item/` → `pos_add_item()`
- `POST /pos/remove-item/` → `pos_remove_item()`
- `POST /pos/checkout/` → `pos_checkout()`

### Admin Functions
- `GET /user-approvals/` → `user_approvals()`
- `POST /approve-user/<id>/` → `approve_user()`
- `POST /staff-list/` → `staff_list()`
- `GET /notifications/` → `notifications()`

---

## Settings Configuration

### Key Django Settings (config/settings.py)
```python
DEBUG = True  # Set to False in production
SECRET_KEY = "your-secret-key-here"

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'inventory',  # Our app
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

---

## Frontend Architecture

### CSS System
**CSS Variables** (modern-styles.css):
```css
:root {
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --dark-bg: #0f0f23;
    --light-bg: #f8fafc;
    --spacing-md: 1rem;
    --radius-lg: 0.75rem;
    --glass-bg: rgba(255, 255, 255, 0.1);
    --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
    /* ... many more ... */
}
```

### Dynamic Theme System
1. **On page load**: Fetch user's theme config from API
2. **Apply CSS**: Create `<style id="dynamic-theme-css">` with user colors
3. **Persist changes**: Save to database on toggle
4. **LocalStorage**: Fallback for theme preference

### Glassmorphism Components
- **Login Card**: `backdrop-filter: blur(20px)`
- **Sidebar**: Semi-transparent with backdrop blur
- **Modals**: Overlay with semi-transparent background
- **Cards**: `background: rgba(255,255,255,0.95)`

---

## Testing

### Django Admin
1. Go to `http://localhost:8000/admin/`
2. Login with EllarMiniMart / AdminPassword123!
3. View/manage all models

### Manual Testing Checklist
- [ ] Login as admin
- [ ] Register new staff account
- [ ] Approve new user
- [ ] Login as staff
- [ ] Add product
- [ ] Complete POS transaction
- [ ] View reports
- [ ] Change theme and dark mode
- [ ] Test responsive layout

### Test Accounts to Create
```python
# Staff account 1
username: staff1
email: staff1@test.com
password: Staff@123
branch: main

# Staff account 2
username: staff2
email: staff2@test.com
password: Staff@456
branch: branch1
```

---

## Development Workflow

### Making Changes
1. Modify Python files (views, models, forms)
2. Server auto-reloads (StatReloader)
3. For model changes:
   ```bash
   python manage.py makemigrations inventory
   python manage.py migrate inventory
   ```
4. For template changes: Just refresh browser

### Code Style
- Follow PEP 8
- Use descriptive variable names
- Add docstrings to functions
- Keep functions small and focused

### Adding New Features
1. **Model** → `inventory/models.py`
2. **Form** → `inventory/forms.py`
3. **View** → `inventory/views.py`
4. **URL** → `inventory/urls.py`
5. **Template** → `templates/inventory/*.html`
6. **Migration** → `python manage.py makemigrations`

---

## Common Development Tasks

### Create Superuser (for admin panel)
```bash
python manage.py createsuperuser
```

### Reset Database
```bash
# Delete migrations (except __init__.py and 0001_initial.py)
# Delete db.sqlite3
python manage.py migrate
```

### Create Test Data
```bash
python manage.py shell
```

```python
from inventory.models import Product

Product.objects.create(
    name="Test Product",
    sku="TEST-001",
    product_type="SNACKS",
    quantity=10,
    purchase_price=10.00,
    unit_price=15.00,
)
```

### Export Data
```bash
python manage.py dumpdata inventory > backup.json
```

### Import Data
```bash
python manage.py loaddata backup.json
```

---

## Debugging

### Enable Debug Toolbar (optional)
1. Install: `pip install django-debug-toolbar`
2. Add to INSTALLED_APPS
3. Add to MIDDLEWARE
4. Appears as sidebar in development

### Common Errors

| Error | Solution |
|-------|----------|
| `TemplateDoesNotExist` | Check TEMPLATES['DIRS'] in settings |
| `No such table` | Run `python manage.py migrate` |
| `AttributeError: 'User' object has no attribute 'profile'` | Check UserProfile signal is loaded |
| `CSRF token missing` | Include `{% csrf_token %}` in forms |
| `Static files not loading` | Run `python manage.py collectstatic` |

---

## Production Checklist

Before deploying to production:
- [ ] Set `DEBUG = False`
- [ ] Generate new SECRET_KEY
- [ ] Set ALLOWED_HOSTS
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set up HTTPS/SSL
- [ ] Configure email backend
- [ ] Set up logging
- [ ] Run security checks: `python manage.py check --deploy`
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Use Gunicorn/uWSGI server
- [ ] Set up database backups

---

## Resources

- Django Docs: https://docs.djangoproject.com/
- Django Template Language: https://docs.djangoproject.com/en/6.0/topics/templates/
- CSS Grid/Flexbox: https://developer.mozilla.org/en-US/docs/Web/CSS/
- Lucide Icons: https://lucide.dev/
- Chart.js: https://www.chartjs.org/

---

## File Sizes & Performance

| File | Size | Purpose |
|------|------|---------|
| modern-styles.css | ~50KB | Glassmorphism styles |
| modern_base.html | ~20KB | Main layout |
| db.sqlite3 | ~500KB | Database |
| Total JS | ~200KB | Lucide + Chart.js |

---

**Last Updated**: May 5, 2026  
**Version**: 1.0  
**Status**: Ready for Development & Testing
