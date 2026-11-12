# Smart Waste Management System

A Flask-based waste management web application with AI-assisted image classification, disposal guidance, collection scheduling, and dashboards for users and administrators. The classifier recognizes plastic, paper, metal, glass, and organic waste when a trained model is installed.

## Features

- Account registration, login, and role-based access for users and administrators.
- Waste image upload, classification, confidence display, and disposal recommendations.
- User classification history and statistics.
- Waste collection requests, status history, and cancellation of pending requests.
- Admin tools for managing users and collection requests, viewing system statistics, and exporting CSV/Excel reports.
- SQLite for a simple local setup, with PostgreSQL support for Docker or other deployments.

## Technologies

- Python 3.10–3.12 and Flask
- Flask-SQLAlchemy, Flask-Migrate, SQLite, and PostgreSQL
- HTML, CSS, JavaScript, and Jinja templates
- TensorFlow/Keras with MobileNetV2 and OpenCV for optional AI classification
- Docker Compose, pytest, and openpyxl

## Project structure

```text
.
├── ai_model/                 # Dataset preparation, training, and inference code
│   ├── prepare_dataset.py
│   ├── train.py
│   └── README.md
├── backend/                  # Flask app, configuration, models, routes, and services
├── database/                 # Database initialization and PostgreSQL schema
├── frontend/
│   ├── static/                # CSS and JavaScript
│   └── templates/             # Jinja HTML pages
├── tests/                    # API and application tests
├── uploads/                  # Runtime image uploads (not committed)
├── instance/                 # Runtime SQLite database (not committed)
├── .env.example               # Safe configuration template
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── requirements-ai.txt
├── requirements-dev.txt
└── run.py
```

Downloaded training datasets, trained model files, local uploads, databases, virtual environments, and local environment files are excluded from Git. The trained model and dataset must be prepared separately if you want to use AI classification.

## Windows installation (PowerShell)

Run these commands from the project directory. Python 3.11 is recommended.

### 1. Create and activate a virtual environment

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell prevents activation, enable script execution for your Windows user and activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\venv\Scripts\Activate.ps1
```

### 2. Install application dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For running the test suite, install the development dependency:

```powershell
pip install -r requirements-dev.txt
```

### 3. Configure the environment

Create a local `.env` file from the template:

```powershell
Copy-Item .env.example .env
```

Edit `.env` before initializing the database:

- Generate a unique `SECRET_KEY` locally:

  ```powershell
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

- Replace `SECRET_KEY` with the generated value.
- Set `ADMIN_EMAIL` and `ADMIN_PASSWORD` to credentials you choose. Use a unique, strong password.
- The default `DATABASE_URL=sqlite:///swms.db` works for local development; Flask stores this database under `instance/`.
- Keep `FLASK_DEBUG=0` unless you are intentionally debugging locally. For production over HTTPS, set `SESSION_COOKIE_SECURE=1`.

Never commit `.env`. The checked-in `.env.example` contains placeholders and non-sensitive local defaults only.

### 4. Initialize the database

With the virtual environment active and `.env` configured:

```powershell
python database\init_db.py
```

This creates the tables and, when `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set, creates the initial administrator account. The local SQLite database is created in `instance/` and is ignored by Git.

### 5. Run the application

```powershell
python run.py
```

Open [http://localhost:5000](http://localhost:5000). Users can register at `/register`; sign in with the configured administrator account to use `/admin`.

## User and administrator functionality

**Users** can register and sign in, classify waste images, view their classification history and statistics, create collection requests, review request status history, and cancel requests that are still pending.

**Administrators** can review system statistics, manage users and their roles, process collection requests through the available statuses, and download CSV or Excel reports.

## AI waste classification

The web application runs without the optional AI packages, but classification requires both the AI dependencies and a trained model. Without a model, the classify API reports that classification is unavailable instead of returning a fabricated prediction.

1. Install the AI dependencies in the active virtual environment:

   ```powershell
   pip install -r requirements-ai.txt
   ```

2. Obtain a waste-image dataset and prepare it. For dataset format and supported category names, see [ai_model/README.md](ai_model/README.md).

   ```powershell
   python -m ai_model.prepare_dataset --src "C:\path\to\your\dataset"
   ```

3. Train the model:

   ```powershell
   python -m ai_model.train
   ```

Training writes `waste_model.keras`, `classes.json`, and `metrics.json` under `ai_model/model/`. These are generated files and are not committed. Restart the application after training. Classification quality depends on the dataset; consult `metrics.json` for measured test results.

## PostgreSQL and Docker

Docker Desktop is optional. To use the included PostgreSQL service:

1. Copy `.env.example` to `.env`.
2. Set a unique `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and strong `POSTGRES_PASSWORD` in `.env`.
3. Build and start the services:

   ```powershell
   docker compose up --build
   ```

The Compose setup initializes the database and administrator, then serves the application on [http://localhost:5000](http://localhost:5000). Set `INSTALL_AI=1` in `.env` to install the larger TensorFlow dependency in the image. A model trained locally can be mounted from `ai_model/model/`.

For PostgreSQL without Docker, create a database and configure `DATABASE_URL` with your own PostgreSQL connection details before running `python database\init_db.py`. Do not put real connection credentials in this README or `.env.example`.

## Tests

With development dependencies installed:

```powershell
pytest
```

The tests use in-memory SQLite and stub the classifier where appropriate; they test application behavior, not trained-model accuracy.

## Before publishing

- Review `git status` and confirm `.env`, local databases, uploads, downloaded datasets, and generated models are not staged.
- Keep `.env.example` as the safe template; never force-add ignored local secrets or data.
- If a real credential was ever committed or shared, rotate it before publishing.
- Review the actual GitHub changes before pushing. No GitHub push is performed by this project setup.
