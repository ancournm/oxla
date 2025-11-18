# Oxla Suite - Complete Setup Guide

## 🚀 Quick Start (No Data Loss)

### Prerequisites
- Node.js 18+ 
- Python 3.11+
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/ancourn/Oxla.git
cd Oxla
git checkout backend-foundation-complete
```

### Step 2: Set Up Environment Variables
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Required .env variables:**
```env
DATABASE_URL="file:./db/custom.db"
NEXTAUTH_SECRET="your-super-secret-jwt-key-change-in-production"
NEXTAUTH_URL="http://localhost:3000"
JWT_SECRET="your-jwt-secret-change-in-production"
```

### Step 3: Install Dependencies

**Frontend (Next.js):**
```bash
# Install Node.js dependencies
npm install
```

**Backend (Python):**
```bash
# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt
```

### Step 4: Database Setup

**SQLite Database:**
```bash
# Generate Prisma client
npm run db:generate

# Push schema to database
npm run db:push
```

**For PostgreSQL (Production):**
```bash
# Update .env with PostgreSQL settings
DATABASE_URL="postgresql://username:password@localhost:5432/oxlas_suite"
```

### Step 5: Start Services

**Option A: Using Docker (Recommended)**
```bash
# Start all services
docker-compose up -d --build

# Verify services
curl http://localhost:8000/health
curl http://localhost:3000
```

**Option B: Manual Setup (Development)**

**Start Backend:**
```bash
# Activate Python virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start backend server
cd backend
python auth_server.py
```

**Start Frontend:**
```bash
# Start Next.js development server
npm run dev
```

### Step 6: Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## 📁 Project Structure

```
Oxla/
├── backend/                 # Python FastAPI backend
│   ├── app/                # Application code
│   ├── alembic/            # Database migrations
│   ├── requirements.txt      # Python dependencies
│   └── auth_server.py     # Backend server
├── src/                    # Next.js frontend
│   ├── app/               # Next.js app routes
│   ├── components/         # React components
│   └── contexts/          # React contexts
├── prisma/                 # Database schema
├── docker-compose.yml       # Docker configuration
└── .env.example           # Environment template
```

## 🔧 Configuration Details

### Frontend Configuration
- **Framework:** Next.js 15 with App Router
- **Styling:** Tailwind CSS with shadcn/ui
- **Authentication:** JWT-based with NextAuth.js
- **State Management:** React Context + Zustand
- **TypeScript:** Full type safety

### Backend Configuration
- **Framework:** FastAPI with Python 3.11+
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Authentication:** JWT with access/refresh tokens
- **ORM:** SQLAlchemy with Alembic migrations
- **API Documentation:** Auto-generated OpenAPI/Swagger

## 🚨 Important Notes

### Data Persistence
- **SQLite Database:** All data stored in `./db/custom.db`
- **User Sessions:** JWT tokens stored in localStorage
- **File Storage:** Local file system (configurable path)
- **Email Queue:** Redis-based (when using Docker)

### Security Considerations
- Change all default secrets in production
- Use HTTPS in production environments
- Configure proper CORS origins
- Set up database backups

### Development Tips
1. **Hot Reload:** Both frontend and backend support hot reload
2. **API Testing:** Use built-in Swagger UI at `/docs`
3. **Database:** Use Prisma Studio for database management
4. **Logs:** Check `backend/logs/` for application logs

## 🐛 Common Issues & Solutions

### Port Conflicts
```bash
# Check what's using port 3000
lsof -i :3000

# Kill process if needed
kill -9 <PID>
```

### Permission Issues
```bash
# Fix file permissions on Unix/Linux
chmod +x backend/venv/bin/activate
```

### Dependency Issues
```bash
# Clear npm cache
npm cache clean --force

# Clear Python cache
pip cache purge
```

### Database Issues
```bash
# Reset database (will lose data)
rm db/custom.db
npm run db:push
```

## 🔄 Migration Guide

### From Previous Version
```bash
# Backup existing data
cp db/custom.db db/custom.db.backup

# Pull latest changes
git pull origin main

# Update dependencies
npm install
pip install -r backend/requirements.txt

# Run migrations
npm run db:migrate

# Restart services
```

## 📱 Access Points

### Web Application
- **Main App:** http://localhost:3000
- **Email Service:** http://localhost:3000/email
- **Dashboard:** http://localhost:3000 (after login)

### API Endpoints
- **Health:** http://localhost:8000/health
- **API Root:** http://localhost:8000/
- **Documentation:** http://localhost:8000/docs
- **Auth:** http://localhost:8000/auth/*
- **Email:** http://localhost:8000/mail/*
- **Files:** http://localhost:8000/drive/*

## 🎯 Next Steps

1. **Explore Features:** Test email sending, file storage, and user management
2. **Customize:** Modify themes, layouts, and components
3. **Deploy:** Configure for production with Docker
4. **Extend:** Add new features and integrations

## 🆘 Support

For issues and questions:
1. Check the logs in `backend/logs/`
2. Review the documentation at `/docs`
3. Check GitHub issues for common problems
4. Review the code comments for implementation details

---

**Built with ❤️ using Next.js, FastAPI, and modern web technologies**