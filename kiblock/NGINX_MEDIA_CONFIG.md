# Nginx Configuration for Media Files

## Problem
Media files at `/media/blocks/` are not being served because the reverse proxy is not configured to handle them.

## Solution
The nginx configuration on your server needs to be updated to serve media files.

### Option 1: Nginx serves media files directly (Recommended)
Add this location block to your nginx site configuration (usually in `/etc/nginx/sites-available/kiblock` or similar):

```nginx
location /media/ {
    alias /path/to/erasmus/kiblock/media/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

Replace `/path/to/erasmus/kiblock/media/` with the actual path on your server where the media files are located.

### Option 2: Pass media requests to Django
If you prefer Django to handle media files, ensure your nginx configuration passes `/media/` requests to the Django container:

```nginx
location /media/ {
    proxy_pass http://127.0.0.1:9025/media/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Full Example Nginx Configuration

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name kiblock.erasmus2026.infotech.edu.pl;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name kiblock.erasmus2026.infotech.edu.pl;

    # SSL configuration (adjust paths to your certificates)
    ssl_certificate /etc/letsencrypt/live/kiblock.erasmus2026.infotech.edu.pl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kiblock.erasmus2026.infotech.edu.pl/privkey.pem;

    # Media files - served by nginx directly
    location /media/ {
        alias /path/to/erasmus/kiblock/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Static files - served by nginx directly
    location /static/ {
        alias /path/to/erasmus/kiblock/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # All other requests go to Django
    location / {
        proxy_pass http://127.0.0.1:9025;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

## After Configuration
1. Test the nginx configuration:
   ```bash
   sudo nginx -t
   ```

2. Reload nginx:
   ```bash
   sudo systemctl reload nginx
   ```

## Verify Media Files Path
Make sure the media files are accessible to nginx:
```bash
ls -la /path/to/erasmus/kiblock/media/blocks/
```

Files should exist and be readable by the nginx user (usually `www-data` or `nginx`).
