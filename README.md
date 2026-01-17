# EduAI Django Backend

Django REST Framework backend for the EduAI learning platform, replacing the original Node.js/MongoDB backend with PostgreSQL.

## Tech Stack

- **Django 4.2** - Web framework
- **Django REST Framework** - API development
- **PostgreSQL** - Database
- **Celery + Redis** - Background tasks
- **django-allauth** - Social authentication (Google, GitHub)
- **djangorestframework-simplejwt** - JWT authentication
- **Cloudinary** - Media storage (optional)

## Project Structure

```
backend_django/
├── config/                 # Django settings and configuration
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── apps/
│   ├── users/             # User model, auth, profiles
│   ├── courses/           # Courses, modules, enrollments
│   ├── assessments/       # Skill assessments, quizzes
│   ├── gamification/      # XP, levels, achievements, streaks
│   ├── certificates/      # Course completion certificates
│   ├── recommendations/   # AI-powered course recommendations
│   └── roadmaps/          # Custom learning paths
├── requirements.txt
├── manage.py
├── Procfile              # For Render deployment
└── build.sh              # Build script for deployment
```

## Local Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis (for Celery)

### 1. Create Virtual Environment

```bash
cd backend_django
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Create PostgreSQL Database

```bash
createdb eduai
# Or using psql:
psql -U postgres -c "CREATE DATABASE eduai;"
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Seed Initial Data

```bash
python manage.py seed_achievements
```

### 8. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

### 9. Run Celery (Optional, for background tasks)

```bash
# In a separate terminal
celery -A config worker --loglevel=info

# For scheduled tasks
celery -A config beat --loglevel=info
```

## API Endpoints

### Authentication (`/api/auth/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register/` | Register new user |
| POST | `/login/` | Login with email/password |
| POST | `/logout/` | Logout (blacklist token) |
| POST | `/token/refresh/` | Refresh JWT token |
| GET/PUT | `/profile/` | Get/update user profile |
| POST | `/profile/password/` | Change password |
| PUT | `/profile/skills/` | Update user skills |
| GET | `/instructors/` | List all instructors |

### Courses (`/api/courses/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all courses |
| POST | `/` | Create course (instructors) |
| GET | `/{slug}/` | Get course details |
| POST | `/{slug}/enroll/` | Enroll in course |
| POST | `/{slug}/publish/` | Publish course |
| GET/POST | `/{slug}/ratings/` | Get/add course ratings |
| GET | `/dashboard/` | User dashboard data |
| GET | `/enrollments/` | User's enrollments |
| POST | `/{slug}/progress/` | Update course progress |
| GET | `/categories/` | List categories |

### Assessments (`/api/assessments/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List assessments |
| POST | `/` | Create assessment |
| GET | `/{id}/` | Get assessment details |
| POST | `/{id}/start/` | Start assessment attempt |
| POST | `/{id}/submit/` | Submit answers |
| GET | `/attempts/` | User's attempts |
| GET | `/skills/analysis/` | Skill analysis |

### Gamification (`/api/gamification/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/badges/` | List all badges |
| GET | `/achievements/` | List all achievements |
| GET | `/leaderboard/` | Get leaderboard |
| GET | `/me/` | User's gamification stats |
| POST | `/me/streak/` | Update streak |
| POST | `/me/xp/` | Add XP |
| GET | `/me/achievements/` | User's achievements |
| GET | `/me/badges/` | User's badges |

### Certificates (`/api/certificates/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | User's certificates |
| GET | `/{uuid}/` | Certificate details |
| GET | `/verify/{uuid}/` | Verify certificate |
| POST | `/generate/{course_id}/` | Generate certificate |

### Recommendations (`/api/recommendations/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Personalized recommendations |
| GET | `/trending/` | Trending courses |
| GET | `/similar/{course_id}/` | Similar courses |

### Roadmaps (`/api/roadmaps/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | User's roadmaps |
| POST | `/` | Create roadmap |
| GET | `/{id}/` | Roadmap details |
| POST | `/{id}/add_step/` | Add step to roadmap |
| POST | `/{id}/reorder_steps/` | Reorder steps |
| GET | `/{id}/progress/` | Roadmap progress |
| PATCH | `/steps/{id}/` | Update step status |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health/` | API health check |

## Deployment to Render

### 1. Create Services on Render

1. **Web Service**
   - Build Command: `./build.sh`
   - Start Command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

2. **Background Worker** (for Celery)
   - Start Command: `celery -A config worker --loglevel=info`

3. **PostgreSQL Database**

4. **Redis Instance**

### 2. Environment Variables

Set these in Render dashboard:

```
SECRET_KEY=<generate-secure-key>
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com
DATABASE_URL=<auto-set-by-render>
REDIS_URL=<your-redis-url>
CELERY_BROKER_URL=<your-redis-url>
CORS_ALLOWED_ORIGINS=https://your-frontend.com

# Optional: Social Auth
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
GITHUB_CLIENT_ID=<your-github-client-id>
GITHUB_CLIENT_SECRET=<your-github-client-secret>

# Optional: Cloudinary
CLOUDINARY_CLOUD_NAME=<your-cloud-name>
CLOUDINARY_API_KEY=<your-api-key>
CLOUDINARY_API_SECRET=<your-api-secret>
```

## Frontend Integration

Update the React frontend to point to the new Django API:

```javascript
// Frontend/.env
VITE_API_URL=http://localhost:8000/api
```

The API endpoints are designed to be compatible with the original Node.js API structure, minimizing frontend changes needed.

## Key Differences from Node.js Backend

| Feature | Node.js (Original) | Django (New) |
|---------|-------------------|--------------|
| Database | MongoDB | PostgreSQL |
| Auth | Firebase + JWT | django-allauth + JWT |
| ORM | Mongoose | Django ORM |
| API | Express.js | Django REST Framework |
| Background Tasks | - | Celery |
| Admin Panel | - | Django Admin |

## Admin Panel

Access the Django admin at `/admin/` to manage:
- Users and profiles
- Courses and modules
- Assessments and questions
- Achievements and badges
- Certificates
- Roadmaps

## License

ISC License
