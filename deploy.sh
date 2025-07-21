#!/bin/bash

# ML Model API Deployment Script
set -e

echo "🚀 Starting ML Model API Deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if firebase_key.json exists
if [ ! -f "firebase_key.json" ]; then
    echo "❌ firebase_key.json not found. Please add your Firebase service account key."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before running again."
    exit 1
fi

# Build and start the services
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for service to be ready
echo "⏳ Waiting for service to be ready..."
sleep 10

# Health check
echo "🔍 Performing health check..."
if curl -f http://localhost:5001/health > /dev/null 2>&1; then
    echo "✅ ML Model API is running successfully!"
    echo "🌐 API available at: http://localhost:5001"
    echo "📊 Health check: http://localhost:5001/health"
else
    echo "❌ Health check failed. Check logs with: docker-compose logs"
    exit 1
fi

echo "🎉 Deployment completed successfully!"
