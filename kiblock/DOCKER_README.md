# KiBlock - Docker Deployment Guide

## Quick Start

### 1. Prerequisites
- Install Docker: https://docs.docker.com/get-docker/
- Install Docker Compose: https://docs.docker.com/compose/install/

### 2. Configuration (Optional)

Copy the example environment file and customize if needed:
```bash
cp .env.example .env
```

Edit `.env` to change:
- `PORT` - Application port (default: 9025)
- `DEBUG` - Debug mode (default: False)
- `ALLOWED_HOSTS` - Comma-separated list of allowed domains

### 3. Build and Run

Build the Docker image and start the container:
```bash
docker-compose up -d
```

The application will be available at: `http://localhost:9025`

### 4. Create Admin User

Create a superuser to access the admin panel:
```bash
docker-compose exec web python manage.py createsuperuser
```

Access admin at: `http://localhost:9025/admin`

## Common Commands

### Start the application
```bash
docker-compose up -d
```

### Stop the application
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f
```

### Restart the application
```bash
docker-compose restart
```

### Run Django commands
```bash
docker-compose exec web python manage.py <command>
```

### Access the container shell
```bash
docker-compose exec web bash
```

## Data Persistence

All data is stored in the `./data` directory:
- `data/db.sqlite3` - Your database with all users, blocks, and cart items

**Important**: Back up the `data/` directory regularly to preserve your data!

## Production Deployment

### On Your Server

1. Clone or copy the project to your server
2. Configure your domain in `.env`:
   ```
   PORT=9025
   DEBUG=False
   ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com,192.168.1.100
   ```
   **Note**: Add only hostnames/domains to ALLOWED_HOSTS (no ports or protocols)

3. Start the application:
   ```bash
   docker-compose up -d
   ```

4. Set up a reverse proxy (Nginx/Apache) to forward traffic from port 80/443 to 9025

### Example Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:9025;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### CSRF Verification Failed
If you see "CSRF verification failed" errors:
1. Make sure your domain is in `ALLOWED_HOSTS` in `.env` (without port numbers)
2. Restart the container: `docker-compose restart`
3. Clear your browser cookies and try again
4. If using a custom port, make sure it's set correctly in `.env`

### Port already in use
Change the port in `.env` or stop the conflicting service:
```bash
sudo lsof -i :9025
```

### Permission issues
Ensure the data directory is writable:
```bash
chmod -R 755 ./data
```

### Reset database
To start fresh, remove the database:
```bash
docker-compose down
rm -rf ./data/db.sqlite3
docker-compose up -d
```

## Security Notes

- Change `DEBUG=False` in production
- Add your domain to `ALLOWED_HOSTS`
- Keep the `data/` directory backed up
- Use a reverse proxy with HTTPS for production access
