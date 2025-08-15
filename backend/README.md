# Oxlas Suite Backend

A complete backend foundation for Oxlas Suite - an all-in-one workspace platform competing with Google Workspace and Microsoft 365.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Python 3.11+ (for local development)

### Running with Docker (Recommended)

1. **Clone and navigate to the project:**
   ```bash
   cd backend
   ```

2. **Copy environment variables:**
   ```bash
   cp ../.env.example .env
   ```

3. **Start the services:**
   ```bash
   docker-compose up -d --build
   ```

4. **Access the application:**
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp ../.env.example .env
   ```

3. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

4. **Start the development server:**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 📋 Features

### Authentication
- ✅ User registration and login
- ✅ JWT authentication with access and refresh tokens
- ✅ Password hashing with bcrypt
- ✅ Protected routes with middleware
- ✅ Email verification system
- ✅ Password reset functionality

### User Management
- ✅ User model with name, email, password hash, and plan
- ✅ Account activation/deactivation
- ✅ User profile management
- ✅ Email verification status

### Email Service
- ✅ Send mail via SMTP
- ✅ Receive mail (IMAP-like API)
- ✅ Smart aliases with `user+tag@domain.com` format
- ✅ Disposable aliases with expiration
- ✅ Email storage and attachments
- ✅ Basic spam filtering
- ✅ Inbox management (mark as read/spam)

### Subscription Plans
- ✅ **Free Plan**: 5GB storage, 50MB upload, 5 aliases, 3 projects
- ✅ **Pro Plan**: 50GB storage, 2GB upload, unlimited aliases, unlimited projects
- ✅ **Enterprise Plan**: Unlimited storage, unlimited upload, custom policies

### Plan Enforcement
- ✅ Middleware for plan-based access control
- ✅ Feature-based access control
- ✅ Storage and upload size limits
- ✅ Team member limits
- ✅ Alias limits (Free: 5, Pro: Unlimited, Enterprise: Unlimited)

### Database
- ✅ PostgreSQL with SQLAlchemy ORM
- ✅ Database migrations with Alembic
- ✅ Proper indexing and constraints
- ✅ Email and attachment storage

### Logging & Monitoring
- ✅ Centralized logging with loguru
- ✅ Structured logging to files
- ✅ Error tracking and debugging
- ✅ Request/response logging

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `DB_USER` | Database username | `oxlas_user` |
| `DB_PASS` | Database password | `oxlas_password` |
| `DB_NAME` | Database name | `oxlas_suite` |
| `JWT_SECRET` | JWT secret key | `your-super-secret-jwt-key-change-in-production` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration | `7` |
| `DEBUG` | Debug mode | `false` |
| `SMTP_HOST` | SMTP server host | `localhost` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | SMTP username | `` |
| `SMTP_PASSWORD` | SMTP password | `` |
| `SMTP_USE_TLS` | Use TLS for SMTP | `true` |
| `IMAP_HOST` | IMAP server host | `localhost` |
| `IMAP_PORT` | IMAP server port | `993` |
| `IMAP_USE_SSL` | Use SSL for IMAP | `true` |

## 📚 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user info
- `POST /auth/refresh` - Refresh access token
- `POST /auth/verify-email` - Verify email address
- `POST /auth/request-reset` - Request password reset
- `POST /auth/reset-password` - Reset password

### Email Service
- `POST /mail/send` - Send email
- `POST /mail/send-with-attachments` - Send email with attachments
- `GET /mail/inbox` - List inbox emails
- `POST /mail/alias` - Create email alias
- `GET /mail/aliases` - List user aliases
- `DELETE /mail/alias/{alias_id}` - Delete email alias
- `GET /mail/unread-count` - Get unread email count
- `POST /mail/mark-read/{email_id}` - Mark email as read
- `POST /mail/mark-spam/{email_id}` - Mark email as spam

### Protected Routes
- `GET /api/protected` - Example protected route
- `GET /api/pro-feature` - Example Pro-only feature

## 🏗️ Architecture

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── api/                 # API routes
│   │   ├── auth.py          # Authentication endpoints
│   │   └── mail.py          # Email service endpoints
│   ├── models/             # Database models
│   │   └── database.py     # SQLAlchemy models and DB setup
│   ├── services/           # Business logic
│   │   └── mail/           # Email service
│   │       └── email_service.py # Core email functionality
│   ├── utils/              # Utility functions
│   │   ├── auth.py         # Authentication utilities
│   │   └── logger.py       # Logging configuration
│   ├── middleware/         # Custom middleware
│   │   └── plan_middleware.py # Plan enforcement middleware
│   ├── config.py           # Configuration management
│   └── plans.py            # Subscription plan definitions
├── alembic/               # Database migrations
├── tests/                 # Automated tests
├── storage/               # Email attachments storage
├── logs/                  # Application logs
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
└── README.md            # This file
```

## 🧪 Testing

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app

# Run tests with verbose output
pytest -v
```

### Test Coverage
- **Authentication Tests**: User registration, login, token refresh, email verification, password reset
- **Plan Management Tests**: Feature access, storage limits, alias limits, upload size limits
- **Email Service Tests**: Send email, receive email, alias management, inbox operations
- **API Integration Tests**: Protected routes, plan enforcement, error handling

### Test Structure
```
tests/
├── conftest.py           # Test configuration and fixtures
├── test_auth.py          # Authentication tests
├── test_plans.py         # Plan management tests
└── test_mail.py          # Email service tests
```

## 🔒 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Plan-based access control
- CORS middleware
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy

## 🚀 Deployment

### Docker Deployment
```bash
docker-compose up -d --build
```

### Manual Deployment
1. Set up PostgreSQL database
2. Configure environment variables
3. Run migrations: `alembic upgrade head`
4. Start application: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## 📊 Database Schema

### Users Table
- `id` (Primary Key)
- `name` (String, required)
- `email` (String, unique, required)
- `password_hash` (String, required)
- `plan` (Enum: free, pro, enterprise)
- `is_active` (Boolean, default true)
- `created_at` (DateTime)
- `updated_at` (DateTime)

## 🔧 Development

### Adding New Features
1. Create new API routes in `app/api/`
2. Add business logic in `app/services/`
3. Update database models in `app/models/`
4. Create database migrations with Alembic
5. Add plan restrictions in `app/plans.py`

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## 📝 License

This project is part of Oxlas Suite and is proprietary software.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 🆘 Support

For support and questions, please contact the development team.