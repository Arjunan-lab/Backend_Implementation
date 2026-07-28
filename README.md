# User Authentication API

A production-ready, modular, and secure user authentication backend built with **FastAPI**, **PostgreSQL**, **SQLAlchemy ORM**, **Alembic** (for migrations), **Pydantic V2**, and standard JWT authorization best-practices.

---

## Technical Stack

- **Python 3.12**
- **FastAPI** (Web framework)
- **PostgreSQL** (Database)
- **SQLAlchemy ORM** (Database access and object mapping)
- **Alembic** (Database schema migrations)
- **Pydantic V2** (Data parsing and validation)
- **Passlib [bcrypt]** (Secure password hashing)
- **python-jose [cryptography]** (JWT encoding/decoding)
- **Uvicorn** (ASGI server)
- **python-dotenv** (Environment variable loader)

---

## Directory Structure

```
user-auth-api/
│
├── requirements.txt      # Project library dependencies
├── README.md             # Setup and developer documentation
├── .env.example          # Template environment configurations
├── .env                  # Secrets and local configurations (Not committed)
├── alembic.ini           # Alembic migration configuration
│
├── app/
│   ├── __init__.py
│   ├── main.py           # Application entry point and router attachments
│   ├── database.py       # Engine creation, base classes, and sessions
│   ├── config.py         # App configuration schema (Pydantic Settings)
│   ├── models.py         # SQLAlchemy database models
│   ├── schemas.py        # Pydantic validation schemas
│   ├── auth.py           # Isolation logic layer for auth services
│   ├── security.py       # Password validation and hashing logic
│   ├── dependencies.py   # DB injections and Bearer token validations
│   ├── utils.py          # JWT payload constructors and parsers
│   └── routes/
│       ├── __init__.py
│       └── auth_routes.py# Route mappings for /register, /login, /me
│
└── alembic/              # Database migration definitions
    ├── env.py            # Migration runtime execution settings
    ├── script.py.mako    # Migration file templates
    └── versions/         # Schema migration history files
```

---

## Setup Instructions

Follow these steps to run the application locally:

### 1. Clone & Navigate to Project Directory
Navigate to the directory:
```bash
cd C:\Users\bysan\.gemini\antigravity-ide\scratch\user-auth-api
```
*(We recommend opening this folder as your active IDE workspace.)*

### 2. Create Virtual Environment
Create a clean Python 3.12 environment:
```bash
python -m venv venv
```

### 3. Activate Virtual Environment
- **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (CMD)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```
- **macOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

### 4. Install Dependencies
Install all package requirements:
```bash
pip install -r requirements.txt
```

### 5. Create Local Database (Using Docker or Local PostgreSQL)

**Option A: Using Docker (Recommended)**
Start the PostgreSQL container and Adminer database management web GUI using Docker Compose:
```bash
docker compose up -d
```
*Database name `user_auth_db`, user `postgres`, and password `postgres` are automatically initialized.*

**Option B: Using Native PostgreSQL / pgAdmin**
Create a PostgreSQL database named `user_auth_db` using `createdb` or PostgreSQL admin tools:
```sql
CREATE DATABASE user_auth_db;
```

### 6. Environment Configurations
Copy `.env.example` to `.env` (if not already created):
```bash
copy .env.example .env
```
Verify `DATABASE_URL` in `.env`:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/user_auth_db
```

### 7. Run Database Migrations
We use Alembic for tracking schemas. To run migrations and update your database to the latest schema:
```bash
alembic upgrade head
```

If you make modifications to `app/models.py`, you can generate and run a new migration automatically:
```bash
alembic revision --autogenerate -m "describe_changes_here"
alembic upgrade head
```

### 8. Run the Application
Start the ASGI web server:
```bash
uvicorn app.main:app --reload
```
The server will start on: **http://127.0.0.1:8000**

---

## API Documentation and Testing

- **Postman**: Import the pre-configured [postman_collection.json](file:///C:/Users/bysan/.gemini/antigravity-ide/scratch/user-auth-api/postman_collection.json) file located at the root of the project and test all APIs end-to-end.
- **API schema reference**: The service exposes its OpenAPI schema for reference, but all functional verification should be completed in Postman.

---

## Authentication Notes

- Login uses only the user's email and password.
- Email addresses must be unique during registration.
- The username field is no longer used.
- On successful login, the API returns an access token, refresh token, and a Bearer token type.
- `last_login_at` is updated whenever a user logs in successfully; `last_logout_at` will be updated through the logout endpoint when that endpoint is implemented.

---

## Database Design

- A new `languages` table is introduced to store predefined language values such as English, Telugu, Hindi, and Tamil.
- The `users` table no longer stores `preferred_language` directly; instead, it uses `language_id`.
- `users.language_id` is a foreign key that references `languages.id`.
- The `users` table also stores `last_login_at` and `last_logout_at` as datetime fields for login/logout tracking.

---

## Endpoints

| Endpoint | Method | Security | Description |
| :--- | :--- | :--- | :--- |
| `/register` | `POST` | Public | Register a new user with email, password, and language selection. Email must be unique. |
| `/login` | `POST` | Public | Authenticate a user using email and password only. Returns access and refresh tokens with the Bearer token type. |
| `/me` | `GET` | Bearer Token | Retrieves current logged-in user details. |

### Register Request Schema
```json
{
  "email": "test@example.com",
  "password": "SecurePassword123!",
  "confirm_password": "SecurePassword123!",
  "language_id": 1
}
```
*Language values are stored in the `languages` table and can include `English`, `Hindi`, `Telugu`, `Tamil`, and other predefined entries. The `users` table references these values through the normalized `language_id` foreign key.*

### Login Request Schema
```json
{
  "email": "test@example.com",
  "password": "SecurePassword123!"
}
```

### Login Response Schema
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "Bearer"
}
```

---

## Verification Plan

- All APIs should be tested using Postman.
- Verify successful registration, email-only login, JWT token issuance, and access to the protected `/me` endpoint.
- Confirm that `last_login_at` is updated on successful login and that `last_logout_at` is reserved for the logout endpoint when it is implemented.

---

## Deliverables

- Updated authentication documentation for email-only login and unique email registration.
- Normalized language storage using the `languages` table and `users.language_id`.
- JWT response documentation covering access token, refresh token, and Bearer token type.
- Postman-based verification guidance for all APIs.
