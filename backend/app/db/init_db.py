import sys
import os

# Ensure the 'app' module can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.database import engine, Base
from app.db import models

def init_db():
    print("Creating database tables based on SQLAlchemy models...")
    try:
        # Create all tables in the database.
        # This is equivalent to "CREATE TABLE" statements in raw SQL.
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    init_db()
