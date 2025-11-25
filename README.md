# Personal Journal Web App

A beautiful, single-user personal journal web application with a soothing gradient background. Store your thoughts, memories, and reflections in a private digital diary.

## Features

- ✍️ **Add Journal Entries** - Create new entries with titles and content
- 📖 **View Entries** - Browse all your journal entries chronologically
- ✏️ **Edit Entries** - Update existing entries anytime
- 🗑️ **Delete Entries** - Remove entries with confirmation (type "DELETE" to confirm)
- 🎨 **Beautiful UI** - Soothing animated gradient background
- 💾 **PostgreSQL Storage** - All data persisted to PostgreSQL database

## Requirements

- Python 3.7+
- PostgreSQL running on localhost:5432
- pip (Python package manager)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up PostgreSQL Database

The app expects PostgreSQL to be running on `localhost:5432`. 

**Option A: Automatic Setup (Recommended)**
```bash
python setup_db.py
```

**Option B: Manual Setup**
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE journal_db;

# Exit psql
\q
```

**Note:** If your PostgreSQL uses different credentials, set environment variables:
```bash
export DB_USER=your_username
export DB_PASSWORD=your_password
```

### 3. Run the Application

```bash
python app.py
```

The app will be available at: **http://localhost:5000**

The database schema will be automatically initialized when you first run the app.

## Usage

1. **Create an Entry**: Fill in the title and content fields, then click "Save Entry"
2. **View Entries**: All your entries are displayed below the form, sorted by most recent first
3. **Edit an Entry**: Click the "Edit" button on any entry to modify it
4. **Delete an Entry**: Click the "Delete" button, then type "DELETE" in the confirmation dialog to permanently remove an entry

## Database Schema

The app uses a single table `journal_entries` with the following structure:

- `id` - Primary key (auto-increment)
- `title` - Entry title (VARCHAR 255)
- `content` - Entry content (TEXT)
- `created_at` - Timestamp of creation
- `updated_at` - Timestamp of last update

## Configuration

Default database connection settings:
- Host: `localhost`
- Port: `5432`
- Database: `journal_db`
- User: `postgres` (or `DB_USER` env variable)
- Password: `postgres` (or `DB_PASSWORD` env variable)

## Troubleshooting

**Database Connection Error:**
- Ensure PostgreSQL is running: `sudo systemctl status postgresql` (Linux) or check your PostgreSQL service
- Verify connection details match your PostgreSQL setup
- Check if PostgreSQL is listening on port 5432: `netstat -an | grep 5432`

**Port Already in Use:**
- Change the port in `app.py` (last line): `app.run(debug=True, host='0.0.0.0', port=5001)`

## License

Personal use - This is a single-user application for personal journaling.
