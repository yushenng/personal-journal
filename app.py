from flask import Flask, render_template, request, jsonify
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)

# Database configuration for YugabyteDB
DB_CONFIG = {
    'host': 'localhost',
    'port': int(os.getenv('DB_PORT', '5433')),  # YugabyteDB default YSQL port is 5433
    'database': 'journal_db',
    'user': os.getenv('DB_USER', 'yugabyte'),
    'password': os.getenv('DB_PASSWORD', 'yugabyte')
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        raise

def init_db():
    """Initialize the database schema"""
    conn = get_db_connection()
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
    
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized successfully")

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/entries', methods=['GET'])
def get_entries():
    """Get all journal entries, ordered by most recent first"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id, title, content, 
                   created_at, updated_at
            FROM journal_entries
            ORDER BY created_at DESC
        """)
        
        entries = cur.fetchall()
        
        # Convert datetime objects to strings
        for entry in entries:
            entry['created_at'] = entry['created_at'].isoformat()
            entry['updated_at'] = entry['updated_at'].isoformat()
        
        cur.close()
        conn.close()
        
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
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            INSERT INTO journal_entries (title, content, created_at, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id, title, content, created_at, updated_at
        """, (title, content))
        
        entry = cur.fetchone()
        entry['created_at'] = entry['created_at'].isoformat()
        entry['updated_at'] = entry['updated_at'].isoformat()
        
        conn.commit()
        cur.close()
        conn.close()
        
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
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            UPDATE journal_entries
            SET title = %s, content = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, title, content, created_at, updated_at
        """, (title, content, entry_id))
        
        entry = cur.fetchone()
        
        if not entry:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Entry not found'}), 404
        
        entry['created_at'] = entry['created_at'].isoformat()
        entry['updated_at'] = entry['updated_at'].isoformat()
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'entry': entry})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/entries/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    """Delete a journal entry"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM journal_entries WHERE id = %s RETURNING id", (entry_id,))
        deleted = cur.fetchone()
        
        if not deleted:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Entry not found'}), 404
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Entry deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5001)
