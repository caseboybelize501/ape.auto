"""
APE Database Initialization

Run this script to initialize the database.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.database.config import engine, Base, init_db
from server.database.models import *  # Import all models to register them


def main():
    """Initialize database."""
    print("Initializing APE database...")
    
    try:
        # Create all tables
        init_db()
        print("✓ Database tables created successfully")
        
        # Verify tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\nCreated {len(tables)} tables:")
        for table in sorted(tables):
            print(f"  - {table}")
        
        print("\n✓ Database initialization complete!")
        
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
