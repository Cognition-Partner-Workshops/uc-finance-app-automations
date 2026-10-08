#!/bin/bash
# deploy.sh - Manual deployment script for TraderX
# Usage: ./deploy.sh [environment]

ENVIRONMENT=${1:-production}
echo "Deploying TraderX to $ENVIRONMENT..."

# Install dependencies
pip install -r traderx-monolith/requirements.txt

# Run database migrations / seeding
cd traderx-monolith
python -c "from app.database import create_tables; create_tables(); from app.seed import seed_database; seed_database()"

# Start the application
python run.py &

# Start the frontend
cd ../web-front-end/react
npm install
npm run build
# Serve with a simple HTTP server
npx serve -s build -l 3000 &

echo "TraderX deployed. Backend: http://localhost:8000, Frontend: http://localhost:3000"
