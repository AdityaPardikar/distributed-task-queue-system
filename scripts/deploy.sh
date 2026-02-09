#!/bin/bash

# Deploy script for Distributed Task Queue System
# Usage: ./deploy.sh [environment] [version]

set -e

ENVIRONMENT=${1:-production}
VERSION=${2:-latest}
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( dirname "$SCRIPT_DIR" )"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

# Load environment configuration
load_environment() {
    ENV_FILE="$PROJECT_DIR/.env.$ENVIRONMENT"
    
    if [ ! -f "$ENV_FILE" ]; then
        print_error "Environment file not found: $ENV_FILE"
        exit 1
    fi
    
    export $(cat "$ENV_FILE" | grep -v '#' | xargs)
    print_status "Loaded environment: $ENVIRONMENT"
}

# Build images
build_images() {
    print_status "Building Docker images..."
    
    docker build -t dtqs-backend:${VERSION} -f "$PROJECT_DIR/Dockerfile.backend" "$PROJECT_DIR"
    docker build -t dtqs-frontend:${VERSION} -f "$PROJECT_DIR/Dockerfile.frontend" "$PROJECT_DIR"
    
    print_status "Docker images built successfully"
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" exec -T backend \
        python -m alembic upgrade head
    
    print_status "Database migrations completed"
}

# Start services
start_services() {
    print_status "Starting services..."
    
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" \
            -f "$PROJECT_DIR/docker-compose.override.yml" \
            up -d
    else
        docker-compose -f "$PROJECT_DIR/docker-compose.yml" up -d
    fi
    
    print_status "Services started successfully"
}

# Health checks
health_checks() {
    print_status "Performing health checks..."
    
    sleep 10
    
    # Check backend
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        print_status "Backend health check passed"
    else
        print_error "Backend health check failed"
        exit 1
    fi
    
    # Check frontend
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        print_status "Frontend health check passed"
    else
        print_error "Frontend health check failed"
        exit 1
    fi
}

# Cleanup old containers and images
cleanup() {
    print_status "Cleaning up old containers and images..."
    docker system prune -f --filter "until=72h"
    print_status "Cleanup completed"
}

# Main deployment flow
main() {
    print_status "Starting deployment to $ENVIRONMENT environment..."
    
    check_prerequisites
    load_environment
    build_images
    start_services
    run_migrations
    health_checks
    cleanup
    
    print_status "Deployment completed successfully!"
    echo ""
    echo "Services are running at:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend:  http://localhost:5000"
    echo "  Database: localhost:5432"
}

# Run main
main
