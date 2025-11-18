#!/bin/bash

# Oxla Suite - Quick Setup Script
# This script sets up the complete Oxla Suite without data loss

set -e

echo "🚀 Oxla Suite - Quick Setup Script"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the Oxla root directory"
    exit 1
fi

echo "📁 Step 1: Setting up environment..."
# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
DATABASE_URL="file:./db/custom.db"
NEXTAUTH_SECRET="your-super-secret-jwt-key-change-in-production"
NEXTAUTH_URL="http://localhost:3000"
JWT_SECRET="your-jwt-secret-change-in-production"
EOF
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

echo "📦 Step 2: Installing frontend dependencies..."
# Install Node.js dependencies
npm install
echo "✅ Frontend dependencies installed"

echo "🐍 Step 3: Setting up Python backend..."
# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
cd backend
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
pip install -r requirements.txt
cd ..
echo "✅ Python dependencies installed"

echo "🗄️ Step 4: Setting up database..."
# Generate Prisma client
npm run db:generate

# Push schema to database
npm run db:push
echo "✅ Database setup complete"

echo "🔧 Step 5: Starting services..."

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "Port $port is already in use"
        return 1
    else
        return 0
    fi
}

# Start backend in background
echo "Starting backend server..."
cd backend
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
python auth_server.py > ../backend_startup.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start. Check backend_startup.log for details."
    exit 1
fi

# Start frontend in background
echo "Starting frontend server..."
npm run dev > ../frontend_startup.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
echo "Waiting for frontend to start..."
sleep 10

# Check if frontend is running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Frontend failed to start. Check frontend_startup.log for details."
    exit 1
fi

echo ""
echo "🎉 Setup Complete!"
echo "==================="
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "💚 Health Check: http://localhost:8000/health"
echo ""
echo "📝 Process IDs:"
echo "Backend: $BACKEND_PID"
echo "Frontend: $FRONTEND_PID"
echo ""
echo "🛑 To stop services:"
echo "kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "📋 Next Steps:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Register a new account"
echo "3. Explore the email service and other features"
echo ""
echo "📄 Logs:"
echo "Backend: backend_startup.log"
echo "Frontend: frontend_startup.log"
echo ""
echo "Happy coding! 🚀"