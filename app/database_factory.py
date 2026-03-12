"""
Database Factory - Auto-detect and return appropriate database
Implements systems engineering principle: Abstraction eliminates technical debt
"""
import os


def get_database():
    """
    Returns PostgreSQL database if DATABASE_URL exists,
    otherwise returns SQLite database for local development.

    This allows zero-code-change switching between:
    - Local development (SQLite)
    - Production deployment (PostgreSQL)
    - Future databases (MySQL, MongoDB, etc.)

    Returns:
        Database instance (PostgreSQL or SQLite)
    """
    database_url = os.getenv('DATABASE_URL')

    # Check if we have a PostgreSQL connection string
    if database_url and database_url.startswith('postgresql'):
        print("🐘 Using PostgreSQL database (Production)")
        from app.database_postgres import PostgresCarrierDatabase
        return PostgresCarrierDatabase(database_url)
    else:
        print("💾 Using SQLite database (Local Development)")
        from app.database import ComprehensiveCarrierDatabase
        return ComprehensiveCarrierDatabase('data/carriers.db')


# For backward compatibility with existing imports
# Old code: from app.database import Database
# New code: from app.database_factory import Database
Database = get_database
