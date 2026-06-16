#!/bin/bash
# Restore script for MC-LarenS ERP Stack

echo "Loading Docker images..."
docker load -i backend-image.tar
docker load -i frontend-image.tar
docker load -i mongo-image.tar

echo "Starting services..."
docker compose up -d

echo "Waiting for MongoDB to be ready..."
sleep 10

echo "Restoring MongoDB database..."
docker cp mongodb-backup/. mclarens2-mongodb:/restore-backup
docker exec mclarens2-mongodb mongorestore /restore-backup

echo "Cleanup..."
docker exec mclarens2-mongodb rm -rf /restore-backup

echo "Restore complete!"
docker compose ps
