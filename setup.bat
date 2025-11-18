@echo off
REM Oxla Suite - Quick Setup Script for Windows
REM This script sets up the complete Oxla Suite without data loss

echo 🚀 Oxla Suite - Quick Setup Script
echo ==================================

REM Check if we're in the right directory
if not exist "package.json" (
    echo ❌ Error: Please run this script from the Oxla root directory
    pause
    exit /b 1
)

echo 📁 Step 1: Setting up environment...
REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file...
    (
        echo DATABASE_URL="file:./db/custom.db"
        echo NEXTAUTH_SECRET="your-super-secret-jwt-key-change-in-production"
        echo NEXTAUTH_URL="http://localhost:3000"
        echo JWT_SECRET="your-jwt-secret-change-in-production"
    ) > .env
    echo ✅ .env file created
) else (
    echo ✅ .env file already exists
)

echo 📦 Step 2: Installing frontend dependencies...
REM Install Node.js dependencies
call npm install
echo ✅ Frontend dependencies installed

echo 🐍 Step 3: Setting up Python backend...
REM Check if virtual environment exists
if not exist "backend\venv" (
    echo Creating Python virtual environment...
    cd backend
    python -m venv venv
    cd ..
)

REM Activate virtual environment and install dependencies
echo Installing Python dependencies...
cd backend
call venv\Scripts\activate
pip install -r requirements.txt
cd ..
echo ✅ Python dependencies installed

echo 🗄️ Step 4: Setting up database...
REM Generate Prisma client
call npm run db:generate

REM Push schema to database
call npm run db:push
echo ✅ Database setup complete

echo 🔧 Step 5: Starting services...

REM Start backend in background
echo Starting backend server...
cd backend
call venv\Scripts\activate
start /B python auth_server.py ..\backend_startup.log
cd ..
echo ✅ Backend starting...

REM Wait for backend to start
timeout /t 10 > nul
echo.

REM Start frontend in background
echo Starting frontend server...
start /B npm run dev ..\frontend_startup.log
echo ✅ Frontend starting...

REM Wait for frontend to start
timeout /t 15 > nul
echo.

echo.
echo 🎉 Setup Complete!
echo ===================
echo 🌐 Frontend: http://localhost:3000
echo 🔧 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo 💚 Health Check: http://localhost:8000/health
echo.
echo 📋 Next Steps:
echo 1. Open http://localhost:3000 in your browser
echo 2. Register a new account
echo 3. Explore the email service and other features
echo.
echo 📄 Logs:
echo Backend: backend_startup.log
echo Frontend: frontend_startup.log
echo.
echo Happy coding! 🚀
echo.
pause