# 🚀 Oxla Suite - Complete Workspace Platform

A comprehensive all-in-one workspace platform competing with Google Workspace and Microsoft 365. Built with Next.js, FastAPI, and modern web technologies.

## ✨ Features

### 🔐 Authentication System
- **User Registration & Login**: Secure JWT-based authentication
- **Email Verification**: Account verification via email tokens
- **Password Reset**: Secure password recovery system
- **Session Management**: Persistent user sessions with auto-refresh
- **Plan-based Access**: Free, Pro, and Enterprise tiers

### 📧 Email Service
- **Email Composition**: Rich text email composer with attachments
- **Smart Aliases**: Create disposable and permanent email aliases
- **Inbox Management**: Full inbox with read/unread status tracking
- **Spam Protection**: Mark emails as spam with filtering
- **Real-time Updates**: Live email status and notifications

### 💾 File Storage (Drive)
- **File Management**: Upload, organize, and manage files
- **Folder Structure**: Hierarchical folder organization
- **Secure Sharing**: Time-limited share links with permissions
- **Virus Scanning**: Automatic virus scanning for uploads
- **Quota Management**: Plan-based storage limits

### 📊 User Management
- **Profile Management**: Complete user profile system
- **Usage Tracking**: Real-time usage statistics and limits
- **Plan Features**: Tiered feature access (Free/Pro/Enterprise)
- **Analytics Dashboard**: Comprehensive usage and performance metrics

## 🛠️ Technology Stack

### Frontend
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 4 with shadcn/ui components
- **State Management**: React Context + Zustand
- **Authentication**: NextAuth.js v4
- **UI Components**: Complete shadcn/ui component library
- **Icons**: Lucide React Icons

### Backend
- **Framework**: FastAPI with Python 3.11+
- **Database**: SQLite (dev) / PostgreSQL (prod) with Prisma ORM
- **Authentication**: JWT with access/refresh tokens
- **API Documentation**: Auto-generated OpenAPI/Swagger
- **Task Queue**: Redis-based background job processing
- **Monitoring**: Prometheus metrics and health checks

### Infrastructure
- **Containerization**: Docker and Docker Compose
- **Database**: PostgreSQL with Alembic migrations
- **Caching**: Redis for session and background jobs
- **Monitoring**: Prometheus + Grafana stack
- **File Storage**: Local storage with cloud sync capabilities

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- Python 3.11+
- Git

### Option 1: Automated Setup (Recommended)

#### Linux/macOS
```bash
git clone https://github.com/ancournm/oxla.git
cd oxla
git checkout backend-foundation-complete
chmod +x setup.sh
./setup.sh
```

#### Windows
```cmd
git clone https://github.com/ancournm/oxla.git
cd oxla
git checkout backend-foundation-complete
setup.bat
```

### Option 2: Manual Setup

#### 1. Clone Repository
```bash
git clone https://github.com/ancournm/oxla.git
cd oxla
git checkout backend-foundation-complete
```

#### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

#### 3. Install Dependencies

**Frontend (Next.js):**
```bash
npm install
```

**Backend (Python):**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 4. Database Setup
```bash
# Generate Prisma client
npm run db:generate

# Push schema to database
npm run db:push
```

#### 5. Start Services

**Using Docker (Recommended):**
```bash
docker-compose up -d --build
```

**Manual Setup:**
```bash
# Start backend
cd backend
source venv/bin/activate
python auth_server.py

# Start frontend (new terminal)
npm run dev
```

## 🌐 Access Points

### Web Application
- **Main App**: http://localhost:3000
- **Email Service**: http://localhost:3000/email
- **User Dashboard**: http://localhost:3000 (after login)

### API Endpoints
- **API Root**: http://localhost:8000/
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Authentication**: http://localhost:8000/auth/*
- **Email Service**: http://localhost:8000/mail/*
- **File Storage**: http://localhost:8000/drive/*

### Monitoring
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)
- **Flower (Celery)**: http://localhost:5555

## 📋 Plan Features

| Feature | Free | Pro | Enterprise |
|---------|------|------------|
| **Email Limits** | 500/month | 10,000/month | Unlimited |
| **Email Rate Limit** | 5/minute | 20/minute | 100/minute |
| **Storage** | 5 GB total | 50 GB total | Unlimited |
| **Max File Size** | 50 MB | 2 GB | Unlimited |
| **File Upload Rate** | 10/minute | 50/minute | 200/minute |
| **File Download Rate** | 50/minute | 200/minute | 1000/minute |
| **Email Aliases** | 5 | Unlimited | Unlimited |
| **API Access** | Basic | Advanced | Full |

## 🏗️ Project Structure

```
oxla/
├── backend/                 # Python FastAPI backend
│   ├── app/                # Application code
│   │   ├── api/           # API routes
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   ├── utils/          # Utility functions
│   │   └── middleware/     # Custom middleware
│   ├── alembic/            # Database migrations
│   ├── requirements.txt     # Python dependencies
│   └── auth_server.py     # Backend server
├── src/                    # Next.js frontend
│   ├── app/               # Next.js app routes
│   │   ├── api/           # API routes
│   │   ├── email/         # Email page
│   │   └── globals.css    # Global styles
│   ├── components/         # React components
│   │   ├── auth/           # Auth components
│   │   ├── dashboard/      # Dashboard components
│   │   ├── email/          # Email components
│   │   └── ui/             # UI components
│   ├── contexts/           # React contexts
│   └── lib/               # Utility libraries
├── prisma/                 # Database schema
├── public/                 # Static assets
├── docker-compose.yml       # Docker configuration
├── setup.sh               # Unix setup script
├── setup.bat              # Windows setup script
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables

#### Frontend (.env)
```env
DATABASE_URL="file:./db/custom.db"
NEXTAUTH_SECRET="your-super-secret-jwt-key-change-in-production"
NEXTAUTH_URL="http://localhost:3000"
JWT_SECRET="your-jwt-secret-change-in-production"
```

#### Backend (.env)
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=oxlas_user
DB_PASS=oxlas_password
DB_NAME=oxlas_suite
JWT_SECRET="your-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DEBUG=false
```

### Database Configuration

#### SQLite (Development)
```env
DATABASE_URL="file:./db/custom.db"
```

#### PostgreSQL (Production)
```env
DATABASE_URL="postgresql://username:password@localhost:5432/oxlas_suite"
```

## 🚀 Deployment

### Development
```bash
# Start all services
docker-compose up -d --build

# Or manual setup
./setup.sh  # Unix/Linux
setup.bat     # Windows
```

### Production

#### Using Docker
```bash
# Build and run production containers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### Manual Deployment
```bash
# Build Next.js application
npm run build

# Start production server
npm start

# Start backend with production settings
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🧪 Development

### Running Tests
```bash
# Frontend tests
npm test

# Backend tests
cd backend
python -m pytest
```

### Code Quality
```bash
# Run linting
npm run lint

# Format code
npm run format
```

### Database Migrations
```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## 🔒 Security Features

### Authentication
- JWT-based authentication with access/refresh tokens
- Password hashing with bcrypt
- Email verification system
- Rate limiting and plan enforcement
- CORS middleware configuration

### Data Protection
- Encrypted sensitive data storage
- SQL injection prevention with ORM
- XSS protection with React
- File upload validation and virus scanning
- Audit logging for all operations

### API Security
- Input validation with Pydantic
- Rate limiting per user and plan
- HTTPS enforcement in production
- API key authentication for external access
- Request/response logging

## 📊 Monitoring

### Metrics
- Application performance metrics
- User activity and usage tracking
- Email service statistics
- File storage analytics
- System health monitoring

### Logging
- Structured logging with loguru
- Request/response logging
- Error tracking and debugging
- Log rotation and archiving

## 🤝 Contributing

1. Fork repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow TypeScript best practices
- Write comprehensive tests
- Update documentation
- Use conventional commit messages
- Ensure code passes linting and formatting checks

## 📄 License

This project is licensed under MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the code comments
- Contact the development team

---

**Built with ❤️ using Next.js, FastAPI, and modern web technologies**