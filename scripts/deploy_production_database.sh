#!/bin/bash
# Deploy Production PostgreSQL Database
# Run this after you've created a PostgreSQL database on Railway/Render

set -e  # Exit on error

echo "🚀 EAGLE CARRIER CHATBOT - DATABASE DEPLOYMENT"
echo "================================================"
echo ""

# Check for DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable not set"
    echo ""
    echo "Set it with:"
    echo "  export DATABASE_URL='postgresql://user:password@host:port/database'"
    echo ""
    exit 1
fi

echo "✅ DATABASE_URL found"
echo ""

# Install PostgreSQL adapter if needed
echo "📦 Installing PostgreSQL adapter..."
python3 -m pip install psycopg2-binary --quiet || {
    echo "⚠️  Could not install psycopg2-binary, trying psycopg2..."
    python3 -m pip install psycopg2 --quiet
}
echo "✅ PostgreSQL adapter installed"
echo ""

# Run migration script
echo "🔄 Running database migration..."
python3 scripts/migrate_to_postgres.py

echo ""
echo "================================================"
echo "✅ DATABASE DEPLOYMENT COMPLETE"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Import FMCSA data: python3 scripts/import_fmcsa_carriers.py"
echo "2. Import Aljex loads: python3 scripts/sync_aljex_loads.py"
echo "3. Deploy app: git push railway main"
echo ""
