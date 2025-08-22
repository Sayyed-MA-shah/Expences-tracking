# WINSIDE Expense Tracking System (Django)

Modular Django starter for an online expense and employee payment tracker.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Open http://127.0.0.1:8000/

## Apps
- accounts (login/logout)
- dashboard (KPI cards)
- payments (pay-ins & pay-outs)
- expenses (material, rent/bill/guest, setup)
- employees (fixed, contractual, temporary)

Each feature has separate: `models.py`, `forms.py`, `views.py`, `urls.py`, `templates/<app>/*`.
