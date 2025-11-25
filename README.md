# Personal Journal Web App

A beautiful, single-user personal journal web application with a soothing gradient background. Store your thoughts, memories, and reflections in a private digital diary.

## Features

- ✍️ **Add Journal Entries** - Create new entries with titles and content
- 📖 **View Entries** - Browse all your journal entries chronologically
- ✏️ **Edit Entries** - Update existing entries anytime
- 🗑️ **Delete Entries** - Remove entries with confirmation (type "DELETE" to confirm)
- 🎨 **Beautiful UI** - Soothing animated gradient background
- 💾 **YugabyteDB Storage** - All data persisted to YugabyteDB cluster

## Requirements

- Python 3.7+
- YugabyteDB cluster running with YSQL API enabled (default port: 5433)
- pip (Python package manager)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up YugabyteDB Database

The app expects YugabyteDB to be running with YSQL API accessible on `localhost:5433` (default port). 

**Option A: Automatic Setup (Recommended)**
```bash
python setup_db.py
```

**Option B: Manual Setup**
```bash
# Connect to YugabyteDB using ysqlsh
ysqlsh -U yugabyte -h localhost -p 5433

# Create database
CREATE DATABASE journal_db;

# Exit ysqlsh
\q
```

**Note:** If your YugabyteDB uses different credentials or port, set environment variables:
```bash
export DB_USER=your_username
export DB_PASSWORD=your_password
export DB_PORT=your_port  # Default is 5433
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
- Port: `5433` (YugabyteDB YSQL default port, or `DB_PORT` env variable)
- Database: `journal_db`
- User: `yugabyte` (or `DB_USER` env variable)
- Password: `yugabyte` (or `DB_PASSWORD` env variable)

## Troubleshooting

**Database Connection Error:**
- Ensure YugabyteDB cluster is running and YSQL API is enabled
- Verify connection details match your YugabyteDB setup
- Check if YugabyteDB YSQL is listening on port 5433: `netstat -an | grep 5433` or `ss -tlnp | grep 5433`
- Verify you can connect using ysqlsh: `ysqlsh -U yugabyte -h localhost -p 5433`

**Port Already in Use:**
- Change the port in `app.py` (last line): `app.run(debug=True, host='0.0.0.0', port=5001)`

## License

Personal use - This is a single-user application for personal journaling.
