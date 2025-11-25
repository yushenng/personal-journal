#!/usr/bin/env python3
"""
Database setup script for the Personal Journal app.
This script creates the database and initializes the schema for YugabyteDB.
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import sys

# Database configuration for YugabyteDB
DB_CONFIG = {
    'host': 'localhost',
    'port': int(os.getenv('DB_PORT', '5433')),  # YugabyteDB default YSQL port is 5433
    'user': os.getenv('DB_USER', 'yugabyte'),
    'password': os.getenv('DB_PASSWORD', 'yugabyte')
}

DB_NAME = 'journal_db'

def create_database():
    """Create the journal database if it doesn't exist"""
    try:
        # Connect to YugabyteDB server (connect to default 'yugabyte' database to create new database)
        default_db_config = DB_CONFIG.copy()
        default_db_config['database'] = 'yugabyte'  # Connect to default database first
        conn = psycopg2.connect(**default_db_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        exists = cur.fetchone()
        
        if not exists:
            # Create database
            cur.execute(f'CREATE DATABASE {DB_NAME}')
            print(f"✓ Database '{DB_NAME}' created successfully")
        else:
            print(f"✓ Database '{DB_NAME}' already exists")
        
        cur.close()
        conn.close()
        
        # Now connect to the new database and create tables
        conn = psycopg2.connect(**DB_CONFIG, database=DB_NAME)
        cur = conn.cursor()
        
        # Create journal_entries table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✓ Schema initialized successfully")
        print("\nDatabase setup complete! You can now run the Flask app.")
        
    except psycopg2.OperationalError as e:
        print(f"✗ Error connecting to YugabyteDB: {e}")
        print("\nPlease ensure:")
        print("1. YugabyteDB cluster is running and accessible")
        print("2. YSQL API is enabled on localhost:5433 (default port)")
        print("3. Database credentials are correct")
        print("4. You can set DB_USER, DB_PASSWORD, and DB_PORT environment variables if needed")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error setting up database: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("Setting up Personal Journal database on YugabyteDB...")
    create_database()
