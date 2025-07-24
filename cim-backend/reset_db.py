# reset_db.py
import os
from dotenv import load_dotenv

# --- Step 1: Load Environment Variables ---
print("Attempting to load .env file...")
if load_dotenv():
    print(".env file loaded successfully.")
else:
    print("Warning: .env file not found. Relying on system environment variables.")

# --- Step 2: Check for Database URL ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("\nFATAL ERROR: DATABASE_URL environment variable is not set.")
    print("Please ensure it is defined in your .env file or system environment.")
    exit() # Exit the script if the URL is missing

print(f"Database URL found, ending in: ...{DATABASE_URL[-15:]}")

# We define the imports *after* checking the URL to fail faster.
from database import engine, Base
# Import the specific model classes that define the schema
from models import Deal, Feedback

def reset_database():
    """
    Drops all tables and recreates them based on the current models.
    WARNING: This will delete all data in the tables.
    """
    print("\nConnecting to the database...")
    try:
        connection = engine.connect()
        print("Connection successful.")
        connection.close()
    except Exception as e:
        print(f"\nFATAL ERROR: Could not connect to the database.")
        print(f"DETAILS: {e}")
        print("\nPlease check that your DATABASE_URL is correct and the database server is running.")
        return

    print("\nThis script will drop all tables and delete all data.")
    confirm = input("Are you sure you want to proceed? (y/n): ")
    if confirm.lower() != 'y':
        print("Operation cancelled by user.")
        return

    try:
        print("\nDropping all tables...")
        # The Base object knows about all tables that inherit from it (Deal, Feedback)
        Base.metadata.drop_all(bind=engine)
        print("All tables dropped successfully.")

        print("\nCreating all tables from current models...")
        Base.metadata.create_all(bind=engine)
        print("All tables created successfully.")

        print("\n✅ Database has been reset. You can now start your main application.")

    except Exception as e:
        print(f"\nAn error occurred during the database reset process: {e}")
        print("Please check the error message and your database connection details.")

if __name__ == "__main__":
    reset_database()
