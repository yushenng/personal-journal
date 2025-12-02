#!/bin/bash

###############################################################################
# Yugabyte Anywhere Backup and Restore Script
#
# This script backs up a database from one Yugabyte cluster and restores it
# to another cluster using Yugabyte Anywhere CLI.
#
# Usage:
#   ./backup_restore_yugabyte.sh
#
# Prerequisites:
#   - Yugabyte Anywhere CLI (yb_platform_cli) installed and configured
#   - API token or credentials set up for Yugabyte Anywhere
#   - Access to both source and destination clusters
###############################################################################

set -uo pipefail  # Exit on undefined vars, pipe failures (but not on command errors - we handle those)

# Configuration
SOURCE_CLUSTER_IP="127.1.1.1"
DEST_CLUSTER_IP="127.2.2.2"
DATABASE_NAME="yugabyte"
CLUSTER_1_NAME="cluster1"
CLUSTER_2_NAME="cluster2"

# Yugabyte Anywhere Platform Configuration (if needed)
# Uncomment and set these if your CLI requires platform endpoint
# PLATFORM_URL="https://your-platform-url.com"
# API_TOKEN="${YUGABYTE_API_TOKEN:-}"

# Backup file location
BACKUP_DIR="${HOME}/yugabyte_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${DATABASE_NAME}_${TIMESTAMP}.tar.gz"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Yugabyte Anywhere CLI is available
check_cli() {
    if ! command -v yb_platform_cli &> /dev/null; then
        print_error "Yugabyte Anywhere CLI (yb_platform_cli) not found in PATH"
        print_info "Please install Yugabyte Anywhere CLI and ensure it's in your PATH"
        exit 1
    fi
    print_info "Yugabyte Anywhere CLI found"
}

# Function to create backup directory
setup_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        print_info "Created backup directory: $BACKUP_DIR"
    fi
}

# Function to backup database from cluster 1
backup_database() {
    print_info "Starting backup of database '$DATABASE_NAME' from cluster at $SOURCE_CLUSTER_IP"
    
    print_info "Creating backup..."
    
    # Build the backup command
    # Note: Yugabyte Anywhere CLI command structure may vary by version
    # Common patterns include:
    # 1. yb_platform_cli backup create --cluster-name <name> --keyspace <db> --storage-location <location>
    # 2. yb_platform_cli backup create --cluster-uuid <uuid> --keyspace <db> --storage-location <location>
    # 3. ybctl backup create --cluster <name> --database <db> --output <file>
    
    # Try common CLI command patterns
    BACKUP_SUCCESS=false
    LAST_ERROR=""
    
    # Pattern 1: Using cluster name with keyspace (common for YCQL)
    if yb_platform_cli backup create \
        --cluster-name "$CLUSTER_1_NAME" \
        --keyspace "$DATABASE_NAME" \
        --storage-location "$BACKUP_FILE" >/dev/null 2>&1; then
        BACKUP_SUCCESS=true
        print_info "Backup command succeeded using pattern 1 (keyspace)"
    else
        LAST_ERROR=$(yb_platform_cli backup create \
            --cluster-name "$CLUSTER_1_NAME" \
            --keyspace "$DATABASE_NAME" \
            --storage-location "$BACKUP_FILE" 2>&1 || true)
    fi
    
    # Pattern 2: Using cluster name with database (common for YSQL)
    if [ "$BACKUP_SUCCESS" = false ]; then
        if yb_platform_cli backup create \
            --cluster-name "$CLUSTER_1_NAME" \
            --database-name "$DATABASE_NAME" \
            --storage-location "$BACKUP_FILE" >/dev/null 2>&1; then
            BACKUP_SUCCESS=true
            print_info "Backup command succeeded using pattern 2 (database-name)"
        else
            LAST_ERROR=$(yb_platform_cli backup create \
                --cluster-name "$CLUSTER_1_NAME" \
                --database-name "$DATABASE_NAME" \
                --storage-location "$BACKUP_FILE" 2>&1 || true)
        fi
    fi
    
    # Pattern 3: Using cluster IP/host directly
    if [ "$BACKUP_SUCCESS" = false ]; then
        if yb_platform_cli backup create \
            --cluster-host "$SOURCE_CLUSTER_IP" \
            --database-name "$DATABASE_NAME" \
            --storage-location "$BACKUP_FILE" >/dev/null 2>&1; then
            BACKUP_SUCCESS=true
            print_info "Backup command succeeded using pattern 3 (cluster-host)"
        else
            LAST_ERROR=$(yb_platform_cli backup create \
                --cluster-host "$SOURCE_CLUSTER_IP" \
                --database-name "$DATABASE_NAME" \
                --storage-location "$BACKUP_FILE" 2>&1 || true)
        fi
    fi
    
    if [ "$BACKUP_SUCCESS" = false ]; then
        print_error "Backup failed. Please check:"
        print_error "  1. Cluster name/IP ($SOURCE_CLUSTER_IP) is correct"
        print_error "  2. Database name ($DATABASE_NAME) exists"
        print_error "  3. You have proper permissions"
        print_error "  4. Yugabyte Anywhere CLI is properly configured"
        print_error "  5. CLI command syntax matches your Yugabyte Anywhere version"
        if [ -n "$LAST_ERROR" ]; then
            print_error "Last error output:"
            echo "$LAST_ERROR" | sed 's/^/    /'
        fi
        print_warn "You may need to adjust the backup command in the script based on your CLI version"
        exit 1
    fi
    
    print_info "Backup completed successfully"
    
    # Verify backup file exists (if stored locally)
    if [ -f "$BACKUP_FILE" ]; then
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        print_info "Backup file size: $BACKUP_SIZE"
        print_info "Backup location: $BACKUP_FILE"
    else
        print_warn "Backup file not found locally at: $BACKUP_FILE"
        print_warn "Backup may be stored remotely (S3/GCS/etc.)"
        print_info "Backup location: $BACKUP_FILE"
    fi
}

# Function to wait for user input
wait_for_user() {
    echo ""
    print_warn "Backup completed. Ready to restore to destination cluster."
    print_info "Press ENTER to continue with restore, or Ctrl+C to cancel..."
    read -r
    print_info "Proceeding with restore..."
}

# Function to restore database to cluster 2
restore_database() {
    print_info "Starting restore of database '$DATABASE_NAME' to cluster at $DEST_CLUSTER_IP"
    
    print_info "Restoring backup..."
    
    # Build the restore command
    # Common patterns include:
    # 1. yb_platform_cli backup restore --cluster-name <name> --keyspace <db> --storage-location <location>
    # 2. yb_platform_cli backup restore --cluster-uuid <uuid> --keyspace <db> --storage-location <location>
    # 3. ybctl backup restore --cluster <name> --database <db> --input <file>
    
    RESTORE_SUCCESS=false
    LAST_ERROR=""
    
    # Pattern 1: Using cluster name with keyspace (common for YCQL)
    if yb_platform_cli backup restore \
        --cluster-name "$CLUSTER_2_NAME" \
        --keyspace "$DATABASE_NAME" \
        --storage-location "$BACKUP_FILE" >/dev/null 2>&1; then
        RESTORE_SUCCESS=true
        print_info "Restore command succeeded using pattern 1 (keyspace)"
    else
        LAST_ERROR=$(yb_platform_cli backup restore \
            --cluster-name "$CLUSTER_2_NAME" \
            --keyspace "$DATABASE_NAME" \
            --storage-location "$BACKUP_FILE" 2>&1 || true)
    fi
    
    # Pattern 2: Using cluster name with database (common for YSQL)
    if [ "$RESTORE_SUCCESS" = false ]; then
        if yb_platform_cli backup restore \
            --cluster-name "$CLUSTER_2_NAME" \
            --database-name "$DATABASE_NAME" \
            --storage-location "$BACKUP_FILE" >/dev/null 2>&1; then
            RESTORE_SUCCESS=true
            print_info "Restore command succeeded using pattern 2 (database-name)"
        else
            LAST_ERROR=$(yb_platform_cli backup restore \
                --cluster-name "$CLUSTER_2_NAME" \
                --database-name "$DATABASE_NAME" \
                --storage-location "$BACKUP_FILE" 2>&1 || true)
        fi
    fi
    
    # Pattern 3: Using cluster IP/host directly
    if [ "$RESTORE_SUCCESS" = false ]; then
        if yb_platform_cli backup restore \
            --cluster-host "$DEST_CLUSTER_IP" \
            --database-name "$DATABASE_NAME" \
            --storage-location "$BACKUP_FILE" >/dev/null 2>&1; then
            RESTORE_SUCCESS=true
            print_info "Restore command succeeded using pattern 3 (cluster-host)"
        else
            LAST_ERROR=$(yb_platform_cli backup restore \
                --cluster-host "$DEST_CLUSTER_IP" \
                --database-name "$DATABASE_NAME" \
                --storage-location "$BACKUP_FILE" 2>&1 || true)
        fi
    fi
    
    if [ "$RESTORE_SUCCESS" = false ]; then
        print_error "Restore failed. Please check:"
        print_error "  1. Destination cluster name/IP ($DEST_CLUSTER_IP) is correct"
        print_error "  2. Database name ($DATABASE_NAME) exists or can be created"
        print_error "  3. You have proper permissions"
        print_error "  4. Backup file ($BACKUP_FILE) is accessible"
        print_error "  5. CLI command syntax matches your Yugabyte Anywhere version"
        if [ -n "$LAST_ERROR" ]; then
            print_error "Last error output:"
            echo "$LAST_ERROR" | sed 's/^/    /'
        fi
        print_warn "You may need to adjust the restore command in the script based on your CLI version"
        exit 1
    fi
    
    print_info "Restore completed successfully"
}

# Main execution
main() {
    print_info "=== Yugabyte Database Backup and Restore Script ==="
    print_info "Source: $SOURCE_CLUSTER_IP (Cluster: $CLUSTER_1_NAME)"
    print_info "Destination: $DEST_CLUSTER_IP (Cluster: $CLUSTER_2_NAME)"
    print_info "Database: $DATABASE_NAME"
    echo ""
    
    check_cli
    setup_backup_dir
    backup_database
    wait_for_user
    restore_database
    
    print_info "=== Backup and Restore Process Completed ==="
    print_info "Backup file location: $BACKUP_FILE"
}

# Run main function
main
