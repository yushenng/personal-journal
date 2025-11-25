from flask import Flask, render_template, request, jsonify
from datetime import datetime
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os
from contextlib import contextmanager

app = Flask(__name__)

# Database configuration for YugabyteDB
DB_CONFIG = {
    'host': 'localhost',
    'port': int(os.getenv('DB_PORT', '5433')),  # YugabyteDB default YSQL port is 5433
    'database': 'journal_db',
    'user': os.getenv('DB_USER', 'yugabyte'),
    'password': os.getenv('DB_PASSWORD', 'yugabyte')
}

# Connection pool for better performance
connection_pool = None

def init_connection_pool():
    """Initialize the database connection pool"""
    global connection_pool
    try:
        connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            **DB_CONFIG
        )
        print("Connection pool initialized successfully")
    except psycopg2.Error as e:
        print(f"Error creating connection pool: {e}")
        raise

@contextmanager
def get_db_connection():
    """Get a database connection from the pool"""
    conn = None
    try:
        if connection_pool:
            conn = connection_pool.getconn()
        else:
            conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        if conn:
            if connection_pool:
                connection_pool.putconn(conn)
            else:
                conn.close()

def init_db():
    """Initialize the database schema and indexes"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Create journal_entries table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better query performance
        # Index on created_at for ORDER BY queries (most common operation)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_journal_entries_created_at 
            ON journal_entries(created_at DESC)
        """)
        
        # Index on updated_at for potential future queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_journal_entries_updated_at 
            ON journal_entries(updated_at DESC)
        """)
        
        # Index on id is already created by PRIMARY KEY, but explicit index for WHERE clauses
        # (though PRIMARY KEY already provides this, it's good practice)
        
        conn.commit()
        cur.close()
        print("Database initialized successfully with indexes")

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/entries', methods=['GET'])
def get_entries():
    """Get all journal entries, ordered by most recent first"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Optimized query: uses index on created_at DESC
            # Only select needed columns
            cur.execute("""
                SELECT id, title, content, created_at, updated_at
                FROM journal_entries
                ORDER BY created_at DESC
            """)
            
            entries = cur.fetchall()
            
            # Convert datetime objects to strings
            for entry in entries:
                entry['created_at'] = entry['created_at'].isoformat()
                entry['updated_at'] = entry['updated_at'].isoformat()
            
            cur.close()
        
        return jsonify({'success': True, 'entries': entries})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/entries', methods=['POST'])
def create_entry():
    """Create a new journal entry"""
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        
        if not title or not content:
            return jsonify({'success': False, 'error': 'Title and content are required'}), 400
        
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Optimized: Use DEFAULT for timestamps (more efficient than CURRENT_TIMESTAMP)
            # Single RETURNING clause gets all needed data in one query
            cur.execute("""
                INSERT INTO journal_entries (title, content)
                VALUES (%s, %s)
                RETURNING id, title, content, created_at, updated_at
            """, (title, content))
            
            entry = cur.fetchone()
            entry['created_at'] = entry['created_at'].isoformat()
            entry['updated_at'] = entry['updated_at'].isoformat()
            
            conn.commit()
            cur.close()
        
        return jsonify({'success': True, 'entry': entry}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/entries/<int:entry_id>', methods=['PUT'])
def update_entry(entry_id):
    """Update an existing journal entry"""
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        
        if not title or not content:
            return jsonify({'success': False, 'error': 'Title and content are required'}), 400
        
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Optimized: Uses PRIMARY KEY index on id for fast lookup
            # Only updates updated_at if values actually changed (could add this check)
            cur.execute("""
                UPDATE journal_entries
                SET title = %s, content = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, title, content, created_at, updated_at
            """, (title, content, entry_id))
            
            entry = cur.fetchone()
            
            if not entry:
                cur.close()
                return jsonify({'success': False, 'error': 'Entry not found'}), 404
            
            entry['created_at'] = entry['created_at'].isoformat()
            entry['updated_at'] = entry['updated_at'].isoformat()
            
            conn.commit()
            cur.close()
        
        return jsonify({'success': True, 'entry': entry})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/entries/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    """Delete a journal entry"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Optimized: Uses PRIMARY KEY index on id for fast lookup
            cur.execute("DELETE FROM journal_entries WHERE id = %s RETURNING id", (entry_id,))
            deleted = cur.fetchone()
            
            if not deleted:
                cur.close()
                return jsonify({'success': False, 'error': 'Entry not found'}), 404
            
            conn.commit()
            cur.close()
        
        return jsonify({'success': True, 'message': 'Entry deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize connection pool
    try:
        init_connection_pool()
    except Exception as e:
        print(f"Warning: Could not initialize connection pool: {e}")
        print("Falling back to individual connections")
    
    # Initialize database on startup
    init_db()
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5001)
