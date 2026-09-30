# Full Stack Python Job Portal

A full-stack **Job Portal / Recruitment Management System** built with **Python, Django, Django REST Framework, MySQL, HTML, CSS, JavaScript and Bootstrap**.

The project provides separate workflows for **Candidates, Recruiters and Admins**, including job management, applications, saved jobs, profiles, recruiter/company management, REST APIs and analytics.

## Features

### Candidate
- Candidate registration and login
- Candidate profile management
- Skills and education information
- Resume upload
- Profile picture upload
- Browse and search jobs
- Job details page
- Save/unsave jobs
- Apply for jobs
- Cover letter support
- Application history
- Application status tracking

### Recruiter
- Recruiter registration and login
- Company profile management
- Company logo upload
- Create jobs
- Edit jobs
- Delete jobs
- View own posted jobs
- View applicants for a job
- Download/view applicant resumes
- Update application status
- Email notification when application status changes

### Admin
- Admin dashboard
- User management
- Job management
- Application management
- Reports
- Analytics dashboard
- Candidate/recruiter statistics
- Job and application statistics

## REST API

The project includes Django REST Framework APIs for jobs and applications.

Example endpoints:

```text
/api/jobs/
/api/jobs/2/
/api/applications/
/api/applications/2/
/accounts/api/analytics/dashboard/
```

API functionality includes:
- CRUD operations
- Search
- Filtering
- Pagination
- Sorting
- Role-based permissions
- Application validation

## Technology Stack

| Layer | Technology |
|---|---|
| Programming Language | Python |
| Backend | Django |
| REST API | Django REST Framework |
| Database | MySQL |
| Frontend | HTML5, CSS3, JavaScript |
| UI Framework | Bootstrap |
| Authentication | Django Authentication |
| Image/File Handling | Pillow |
| Email | Gmail SMTP |
| Version Control | Git & GitHub |

## Project Structure

```text
job-portal-django/
│
├── accounts/
│   ├── models.py
│   ├── views.py
│   ├── analytics_views.py
│   ├── urls.py
│   ├── templates/
│   └── management/
│
├── applications/
│   ├── models.py
│   ├── views.py
│   ├── api_views.py
│   ├── serializers.py
│   ├── permissions.py
│   └── templates/
│
├── jobs/
│   ├── models.py
│   ├── views.py
│   ├── api_views.py
│   ├── serializers.py
│   ├── urls.py
│   └── templates/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── templates/
├── manage.py
├── requirements.txt
└── .gitignore
```

## Database

The application uses **MySQL**.

Main data areas include:
- Users
- Company profiles
- Jobs
- Saved jobs
- Applications

The project uses Django migrations for database schema management.

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Shaikh-Nisar/job-portal-django-.git
cd job-portal-django-
```

### 2. Create and activate a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root.

Example:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=job_portal_db
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306

EMAIL_HOST_USER=your_email
EMAIL_HOST_PASSWORD=your_email_app_password
```

**Never commit `.env` to GitHub.**

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create an admin user

```bash
python manage.py createsuperuser
```

### 7. Start the development server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Important URLs

### Admin
```text
http://127.0.0.1:8000/admin/
```

### Candidate Dashboard
```text
http://127.0.0.1:8000/accounts/candidate/dashboard/
```

### Recruiter Dashboard
```text
http://127.0.0.1:8000/accounts/recruiter/dashboard/
```

### Admin Dashboard
```text
http://127.0.0.1:8000/accounts/admin-dashboard/
```

### Admin Analytics
```text
http://127.0.0.1:8000/accounts/admin-analytics/
```

### Jobs
```text
http://127.0.0.1:8000/jobs/
```

### My Jobs
```text
http://127.0.0.1:8000/jobs/my-jobs/
```

### Create Job
```text
http://127.0.0.1:8000/jobs/create/
```

## Security

Sensitive configuration is stored using environment variables.

The repository intentionally excludes:

```text
.env
venv/
media/
staticfiles/
db.sqlite3
__pycache__/
```

Production deployment should additionally configure:
- `DEBUG=False`
- Production `ALLOWED_HOSTS`
- HTTPS
- Secure cookies
- HSTS
- Production database credentials
- Static and media file hosting

## Validation

The project has been checked with Django's system checks:

```bash
python manage.py check
```

The local project is configured to use MySQL and environment-based secrets.

## Future Deployment

Planned production steps include:

- Deploy Django application
- Configure production MySQL database
- Configure static files
- Configure media/resume storage
- Configure HTTPS
- Configure production email
- Set production security settings
- Test candidate, recruiter and admin workflows on the live site

## Author

**Shaikh Nisar**

GitHub:

https://github.com/Shaikh-Nisar

## Repository

https://github.com/Shaikh-Nisar/job-portal-django-
