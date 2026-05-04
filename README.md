# EllarStore Inventory System

## Setup

```powershell
cd EllarStore
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:
- App: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Features
- Product list with SKU, quantity, price, and reorder level
- Add, edit, and delete products
- Stock in / stock out adjustments with validation
- Dashboard with total products, low-stock count, and stock value
- Recent stock movement history

## Project layout

- `config/` - Django project settings and root URLs
- `inventory/` - Inventory app models, views, forms, URLs, tests, and migrations
- `templates/` - Shared and inventory page templates
- `static/` - CSS and frontend assets
- `docs/` - Project notes and user instructions
- `scripts/manual_checks/` - Manual verification scripts for POS and dashboard behavior

## Manual checks

Run these from the project root after starting the server:

```powershell
.\.venv\Scripts\python.exe scripts\manual_checks\pos.py
.\.venv\Scripts\python.exe scripts\manual_checks\checkout.py
.\.venv\Scripts\python.exe scripts\manual_checks\dashboard_analytics.py
.\.venv\Scripts\python.exe scripts\manual_checks\sold_products.py
```
