# MC-LarenS ERP Stack Backup

Backup and documentation of the MC-LarenS ERP stack running on Docker.

## Stack Components

### 1. MC-LarenS ERP2 (Mundo Accesorios)
- **Backend**: Python FastAPI application on port 8001
  - Image: `mc-larenserp20-backend:updated-20260219`
  - Database: MongoDB (puerto 27017)
  - Main entrypoint: `uvicorn backend.server:app`

- **Frontend**: React/Nginx application on port 3000
  - Image: `mundo-frontend:updated-20260219`
  - Reverse proxy via Nginx

- **MongoDB**: Database service
  - Image: `mongo:7.0`
  - Database: `mc-larens2_mundo_accesorios_erp`

### 2. WhatsApp CRM
- **Service**: Node.js CRM application on port 3001
  - Image: `whatsapp-crm-mc-larens-crm`
  - Database: SQLite (`/app/data/crm.sqlite`)
  - Features: WhatsApp integration, AI analysis (Ollama), automated backups

## Quick Start

### Prerequisites
- Docker Engine (latest)
- Docker Compose v2.x
- 4GB+ RAM available

### Launch Stack
```bash
docker compose up -d
```

### Check Services
```bash
docker compose ps
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mc-larens-crm
```

## Services & Ports

| Service | URL | Port | Protocol |
|---------|-----|------|----------|
| Frontend | http://localhost:3000 | 3000 | HTTP |
| Backend API | http://localhost:8001 | 8001 | HTTP |
| CRM | http://localhost:3001 | 3001 | HTTP |
| MongoDB | localhost:27017 | 27017 | TCP |

## Environment Variables

Edit `docker-compose.yml` to modify:

### Backend
- `MONGO_URL`: MongoDB connection string
- `CORS_ORIGINS`: Allowed CORS origins
- `DEFAULT_PIN_USER_PIN`: Default PIN for users

### CRM
- `AUTH_SECRET`: Session secret (change in production!)
- `DEFAULT_ADMIN_PASSWORD`: Admin password (change in production!)
- `OLLAMA_BASE_URL`: AI model service URL
- `BACKUP_CRON`: Backup schedule (cron format)

## Volumes

- `mongodb_data`: MongoDB database storage
- `whatsapp_data`: CRM data
- `whatsapp_sessions`: WhatsApp sessions
- `whatsapp_logs`: Application logs
- `whatsapp_uploads`: User uploads
- `whatsapp_backups`: Database backups

## Backup & Recovery

### Export MongoDB
```bash
docker exec mclarens2-mongodb mongodump --out /backup
docker cp mclarens2-mongodb:/backup ./mongodb_backup
```

### Export CRM Data
```bash
docker cp mc-larens-crm:/app/data ./crm_data_backup
```

## Troubleshooting

### Container keeps restarting
```bash
docker compose logs mc-larens-crm
```

### MongoDB connection issues
```bash
docker exec mclarens2-mongodb mongosh
```

### Port already in use
Edit `docker-compose.yml` and change port mapping:
```yaml
ports:
  - "8080:8001"  # Change host port from 8001 to 8080
```

## Production Considerations

⚠️ **Security Issues to Address:**
- Change `DEFAULT_ADMIN_PASSWORD` to a strong password
- Change `AUTH_SECRET` to a random value
- Set `COOKIE_SECURE: "true"` in backend
- Use environment variables from `.env` file instead of hardcoding
- Set up SSL/TLS certificates
- Configure proper MongoDB authentication
- Limit CORS_ORIGINS to specific domains

## Support

For issues with specific services, check their respective logs:
```bash
docker compose logs backend --tail=100
docker compose logs frontend --tail=100
docker compose logs mc-larens-crm --tail=100
```
