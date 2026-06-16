#!/bin/bash
# Backup script for MC-LarenS ERP Stack

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

echo "Starting ERP Stack backup at $TIMESTAMP..."

# Backup MongoDB
echo "Backing up MongoDB..."
docker exec mclarens2-mongodb mongodump --out /backup
docker cp mclarens2-mongodb:/backup $BACKUP_DIR/mongodb_$TIMESTAMP
docker exec mclarens2-mongodb rm -rf /backup

# Backup CRM data
echo "Backing up CRM data..."
docker cp mc-larens-crm:/app/data $BACKUP_DIR/crm_data_$TIMESTAMP
docker cp mc-larens-crm:/app/logs $BACKUP_DIR/crm_logs_$TIMESTAMP

# Create archive
echo "Creating archive..."
tar -czf $BACKUP_DIR/erp_backup_$TIMESTAMP.tar.gz $BACKUP_DIR/mongodb_$TIMESTAMP $BACKUP_DIR/crm_data_$TIMESTAMP $BACKUP_DIR/crm_logs_$TIMESTAMP

# Cleanup temp files
rm -rf $BACKUP_DIR/mongodb_$TIMESTAMP $BACKUP_DIR/crm_data_$TIMESTAMP $BACKUP_DIR/crm_logs_$TIMESTAMP

echo "Backup completed: $BACKUP_DIR/erp_backup_$TIMESTAMP.tar.gz"
