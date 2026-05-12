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

## Deploying to Render

Render's normal web-service filesystem is temporary. If this app uses the local
`db.sqlite3` file in production, new products, sales, users, and settings can
disappear after a redeploy or restart. Use Render Postgres instead.

This repo includes a `render.yaml` Blueprint that creates:
- a Python web service
- a Render Postgres database
- a `DATABASE_URL` environment variable connecting the app to that database

Recommended deploy flow:

```bash
git add .
git commit -m "Configure Render Postgres deployment"
git push
```

Then in Render, create a new Blueprint from this repository. Render will use
`bash build.sh` to install dependencies, collect static files, and run
migrations.

If you already created the web service manually, keep the service but add a
Render Postgres database and set these values in the web service:

```text
Build Command: bash build.sh
Start Command: python -m gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
DATABASE_URL: your Render Postgres internal connection string
SECRET_KEY: a generated secret value
DEBUG: false
```

After the first successful deploy, create your admin user in the Render Shell:

```bash
python manage.py createsuperuser
```

Existing data from an old SQLite `db.sqlite3` file is not automatically copied
to Postgres. Export/import it with Django fixtures if you need to keep it.

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
