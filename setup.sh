#!/bin/bash
# Quick setup script for development environment

set -e

echo "🚀 TaskFlow Development Setup"
echo "=============================="

# Check prerequisites
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Prerequisites check passed"

# Create virtual environment
echo -e "\n📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null
pip install -r requirements-dev.txt > /dev/null

# Create .env file
echo "📝 Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Created .env - please update with your credentials"
fi

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.local.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Initialize database
echo "🗄️  Initializing database..."
python scripts/init_db.py

echo ""
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Run API server:    python run.py"
echo "2. Run worker:        python -m src.core.worker"
echo "3. Run tests:         pytest tests/"
echo ""
