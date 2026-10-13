# Medical Case Management App

A small web application for tracking medical implant cases from draft to completion. Authorized users log in, create cases, update their status, and view them on a dashboard. A Sanctum-secured REST API exposes the same functionality.

> Built as a Software Developer Intern practical assignment for Jajal Medical.
> **All data is dummy data. No real patient information is used or stored.**

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Laravel (PHP 8.2+) |
| Database | MySQL |
| Frontend | Blade + Tailwind CSS (Vite) |
| Web auth | Laravel Breeze |
| API auth | Laravel Sanctum (token based) |
| Authorization | Laravel Policy (`MedicalCasePolicy`) |
| Validation | Form Request classes |
| Testing | PHPUnit (Laravel feature tests) |
| Version control | Git / GitHub |

---

## Features

- Login / Logout with clear error messages for wrong credentials
- Role-based access: **Admin** (full access) and **Viewer** (read-only)
- Dashboard with counts: Total, Planning, In Review, Approved, Completed
- Case list with pagination (10 per page), search (Case Number / Surgeon Name) and Status filter
- Single form reused for Create and Edit, with field-level validation errors
- Case details page (includes who created the case and when)
- Server-side authorization: a Viewer is blocked from delete even if the button is bypassed
- REST API with Sanctum tokens and a consistent JSON response shape
- Seeder and factory creating 2 users and 25 dummy cases

---

## Setup

### Prerequisites

- PHP 8.2 or higher
- Composer
- MySQL 8 (or compatible)
- Node.js and npm
- Git

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/medical-case-app.git
cd medical-case-app

# 2. Install PHP dependencies
composer install

# 3. Create the environment file and generate the app key
cp .env.example .env
php artisan key:generate
```

4. Create an empty MySQL database (for example `medical_cases`), then open `.env` and set:

```env
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=medical_cases
DB_USERNAME=your_mysql_user
DB_PASSWORD=your_mysql_password
```

```bash
# 5. Run migrations and seed dummy data
php artisan migrate --seed

# 6. Install and build frontend assets
npm install
npm run build

# 7. Start the development server
php artisan serve
```

The app is now available at **http://127.0.0.1:8000**.

> To reset the database at any time: `php artisan migrate:fresh --seed`

---

## Test Login Credentials (dummy)

| Role | Email | Password |
|---|---|---|
| Admin | `admin@example.com` | `Admin@12345` |
| Viewer | `viewer@example.com` | `Viewer@12345` |

These are dummy credentials created by the seeder for review purposes only.

### Role permissions

| Role | View cases | Create / Edit cases | Change status | Delete cases |
|---|---|---|---|---|
| Admin | Yes | Yes | Yes | Yes |
| Viewer | Yes | No | No | No |

---

## Running Tests

```bash
php artisan test
```

The test suite uses `RefreshDatabase`, so it does not touch your development data. It covers:

1. Valid login succeeds
2. Invalid login is rejected
3. A guest cannot open case pages or APIs (redirect / 401)
4. Admin can create a case
5. Creating a case with a duplicate Case Number fails (422)
6. Viewer cannot delete a case (403)

---

## API Documentation

Base URL: `http://127.0.0.1:8000/api`

Send these headers on every request:

```
Accept: application/json
Content-Type: application/json
Authorization: Bearer <token>      # for all endpoints except /login
```

### Endpoints

| Method | Endpoint | Purpose | Who can call |
|---|---|---|---|
| POST | `/api/login` | Get an API token | Anyone |
| POST | `/api/logout` | Revoke the current token | Logged-in users |
| GET | `/api/cases` | List cases (paginated, 10 per page) | Admin, Viewer |
| POST | `/api/cases` | Create a case | Admin |
| GET | `/api/cases/{id}` | Get one case | Admin, Viewer |
| PUT | `/api/cases/{id}` | Update a case | Admin |
| DELETE | `/api/cases/{id}` | Delete a case | Admin |

`GET /api/cases` also accepts optional query parameters: `search` (Case Number or Surgeon Name), `status`, and `page`.

### Response format

Every response uses the same JSON shape:

```json
{
  "success": true,
  "data": {},
  "message": "Human readable message"
}
```

### Status codes

| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 401 | Not logged in / invalid token |
| 403 | Logged in but not allowed |
| 404 | Resource not found |
| 422 | Validation error (field-level messages in `data`) |

### Example: login

```bash
curl -X POST http://127.0.0.1:8000/api/login \
  -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Admin@12345"}'
```

```json
{
  "success": true,
  "data": { "token": "1|abcdef..." },
  "message": "Login successful"
}
```

### Example: create a case

```bash
curl -X POST http://127.0.0.1:8000/api/cases \
  -H "Accept: application/json" -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "case_number": "CASE-1001",
    "patient_reference": "PT-1001",
    "surgeon_name": "Dr. Sample",
    "implant_type": "Knee",
    "status": "Draft",
    "priority": "Medium",
    "surgery_date": "2026-12-01"
  }'
```

### Example: validation error (422)

```json
{
  "success": false,
  "data": {
    "case_number": ["The case number has already been taken."]
  },
  "message": "Validation failed"
}
```

A Postman / Thunder Client collection is included at `docs/postman_collection.json`.

---

## Data Model (summary)

**cases**: `id`, `case_number` (unique), `patient_reference`, `surgeon_name`, `implant_type`, `status` (indexed), `priority`, `surgery_date` (nullable), `created_by` (FK to `users.id`), `created_at`, `updated_at`

- **Status values:** Draft, Planning, In Review, Approved, Completed, Cancelled
- **Priority values:** Low, Medium, High

Full details are in [`docs/database.md`](docs/database.md).

---

## Project Structure (key files)

```
app/
├── Enums/                      CaseStatus, CasePriority
├── Http/
│   ├── Controllers/
│   │   ├── CaseController.php          Web CRUD
│   │   ├── DashboardController.php     Dashboard counts
│   │   └── Api/                        AuthController, CaseApiController
│   └── Requests/                       StoreCaseRequest, UpdateCaseRequest
├── Models/                     User, MedicalCase
└── Policies/                   MedicalCasePolicy
database/
├── factories/                  UserFactory, MedicalCaseFactory
├── migrations/                 users (role column), cases
└── seeders/                    DatabaseSeeder
docs/                           database.md, traceability.md, postman_collection.json
routes/                         web.php, api.php
tests/Feature/                  AuthTest, CaseTest
```

---

## Security Notes

- Role checks use a Laravel **Policy** (`MedicalCasePolicy`), enforced on the server for both web and API requests
- Validation lives in **Form Request** classes, not in controllers
- Database access uses **Eloquent / query builder** only, with no raw SQL built from user input
- **Mass assignment** is protected with `$fillable`
- **CSRF** protection is enabled on all web forms
- `.env`, passwords and keys are **not committed**; `.env.example` is provided instead
- Passwords are hashed; API tokens are issued and revoked via Sanctum

---

## Documentation

- [`docs/database.md`](docs/database.md): tables, columns and relationships
- [`docs/traceability.md`](docs/traceability.md): requirement to implementation to test mapping

---

## Assumptions

- Only two roles are required (Admin and Viewer); the role is stored as a string column on `users`
- The model is named `MedicalCase` (the table is `cases`) because `Case` is a reserved word in PHP
- Case Numbers follow the format `CASE-0001` but the format is not strictly enforced by validation; only uniqueness is
- "Change status" is done by editing the case, and is Admin-only
- The API list endpoint returns 10 cases per page, matching the web list
- All patient references are dummy codes, not real names

## Known Limitations

- No self-registration or user management screen; users are created by the seeder only
- Status transitions are not restricted (any status can be set to any other)
- No audit log of who changed a case's status or fields
- No rate limiting configured on the login endpoints
- Basic UI only; no advanced accessibility review was done
- Not deployed to a hosting environment

## What I Would Do Next

- Add an Engineer role (create / edit / change status, but no delete) by extending the policy
- Add Priority filtering and sortable columns on the case list
- Enforce valid status transitions (e.g. Draft to Planning to In Review to Approved to Completed)
- Add an audit trail table recording changes to cases
- Add rate limiting to login and write endpoints
- Write `docs/deployment.md` and deploy (EC2 + RDS + S3 behind HTTPS)
- Add more tests (update validation with the unique-ignore rule, API pagination, search and filter)

---

## Author

**Monika**
GitHub: [@monikanimmana](https://github.com/monikanimmana)
