# SSL Certificate Directory

# ==========================

#

# Development:

# Run ./generate_dev_certs.sh to create self-signed certs.

#

# Production (Let's Encrypt):

# 1. Install certbot on your server:

# sudo apt install certbot python3-certbot-nginx

#

# 2. Obtain certificates:

# sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

#

# 3. Certificates are saved to /etc/letsencrypt/live/yourdomain.com/

# - fullchain.pem (certificate + intermediate chain)

# - privkey.pem (private key)

#

# 4. Mount into Docker:

# volumes:

# - /etc/letsencrypt/live/yourdomain.com/fullchain.pem:/etc/nginx/ssl/fullchain.pem:ro

# - /etc/letsencrypt/live/yourdomain.com/privkey.pem:/etc/nginx/ssl/privkey.pem:ro

#

# 5. Auto-renewal (cron):

# 0 3 \* \* \* certbot renew --quiet --deploy-hook "docker compose -f /path/to/docker-compose.prod.yml restart nginx"

#

# Files in this directory are gitignored (except this README and the generator script).
