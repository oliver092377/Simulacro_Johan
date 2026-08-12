# AGENTS.md — VILLTECC / Simulacro UNSA

## Project Overview

Django 5.2.1 web app ("VILLTECC") for virtual exam simulations for UNSA admissions. Main app is `simulacro`; project config lives in `config/`.

## Setup

- Virtual environment: `env/` (Python 3.11, created via `python -m venv`)
- Activate: `env\Scripts\activate` (Windows PowerShell)
- Install deps: `pip install -r requirements.txt`
- Settings module: `config.settings` (set via `manage.py` default)

## Running the Project

```bash
python manage.py runserver
```

- DB auto-detects: MySQL if current directory path contains `VILLTEC`, otherwise SQLite (`db.sqlite3`).
- Media files served at `/media/` only when `DEBUG=True` (configured in `config/urls.py`).
- Static files collected under root `static/` (includes Django admin + django-ckeditor-5 + project images).

## Key Directories

| Path | Purpose |
|---|---|
| `config/` | Django project package (settings, urls, wsgi, asgi) |
| `simulacro/` | Main app — models, views, forms, utils, templates |
| `static/` | Collected static files (admin, ckeditor5, images) |
| `media/` | User uploads (question images) + generated PDF reports |
| `clase/` | Placeholder (contains empty `ejercicio.py`) |
| `env/` | Python virtual environment |

## Architecture Notes

- **Exam flow**: `realizar_examen` view renders a timed exam (150 min), scores answers using `MatrizPeso` weights, applies penalty (0.102 per wrong answer, 0 for `EXT` area), and stores results in `Intento` + `RespuestaDetalle`.
- **PDF reports**: Generated via ReportLab (`utils.py:generar_pdf_diagnostico`), cached on the `Intento.reporte_pdf` field, served via `FileResponse`.
- **Payment system**: Three tiers (Nivel 0/1/2) controlled via `Intento.nivel_acceso` and `Intento.pagado_reporte`. QR codes link to WhatsApp for payment.
- **Admin customization**: `admin.py` overrides `UserAdmin` to inline `PerfilEstudiante`, adds custom actions for activating Nivel 1/2, and provides inline answer review.
- **CKEditor 5**: Used for question text (`texto_pregunta`) and solution text (`solucion_texto`) fields. Config in `config/settings.py` under `CKEDITOR_5_CONFIGS`.

## Testing & Quality

- **No test infrastructure**: `simulacro/tests.py` is empty (default stub). No pytest, tox, or CI config exists.
- **No linter/formatter config**: No `.flake8`, `.pylintrc`, `pyproject.toml`, or `Makefile`.
- **No CI/CD**: No `.github/` workflows, no pre-commit hooks.

## Important Constraints

- `requirements.txt` has some unpinned packages (asgiref, contourpy, cycler, fonttools, kiwisolver, matplotlib, numpy, packaging, pillow, pyparsing, python-dateutil, qrcode, reportlab, six, sqlparse, tzdata). Pin versions for reproducibility.
- `config/settings.py` contains hardcoded DB credentials for the production MySQL backend (inside the `VILLTEC` cwd check). Do not commit real credentials.
- `static/xd.html` is 0 bytes — not a real template.
- `clase/ejercicio.py` is empty — placeholder, not functional code.
- The `static/` directory at root contains collected static files (admin, ckeditor5), not source files. Do not edit these directly.

## Commands

```bash
# Start dev server
python manage.py runserver

# Create migrations
python manage.py makemigrations simulacro

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run tests (no test infrastructure yet)
python manage.py test
```