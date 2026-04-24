#!/bin/bash

set -euo pipefail

DOMAIN="www.URL.com" # Enter your URL here... 
EMAIL="xyz@protonmail.com" # Enter your email here...

CERTBOT_CONF="./data/certbot/conf"
CERTBOT_WWW="./data/certbot/www"

echo "==> STEP 0: Preparing local folders for persistent certs..."
mkdir -p "$CERTBOT_CONF" "$CERTBOT_WWW"

# Test if bind mount is working by creating a temp file???
echo "bindtest" > "$CERTBOT_CONF/bindtest.txt"

docker run --rm -v "$(pwd)/data/certbot/conf:/etc/letsencrypt" alpine \
  sh -c "if [ ! -f /etc/letsencrypt/bindtest.txt ]; then echo '❌ ERROR: Bind mount not working!'; exit 1; fi"

echo "Host bind mount confirmed"

echo "==> STEP 1: Starting Nginx with HTTP config..."
NGINX_CONFIG_FILE=nginx.conf docker compose up -d --build nginx

echo "==> STEP 2: Waiting for Nginx to become ready..."
sleep 10

echo "==> STEP 3: Testing challenge endpoint..."
CHALLENGE_PATH="$CERTBOT_WWW/.well-known/acme-challenge"
mkdir -p "$CHALLENGE_PATH"
echo "test" > "$CHALLENGE_PATH/test.txt"

if curl -s http://localhost/.well-known/acme-challenge/test.txt | grep -q "test"; then
    echo "Challenge endpoint works"
else
    echo "Challenge endpoint NOT working"
    docker logs nginx
    exit 1
fi

echo "==> STEP 4: Running Certbot to issue certificate..."
docker compose run --rm --entrypoint "" certbot certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  -d "$DOMAIN" --verbose

echo "==> STEP 5: Checking if certs were generated..."
CERT_PATH="$CERTBOT_CONF/live/$DOMAIN/fullchain.pem"
if [ -f "$CERT_PATH" ]; then
    echo "Certificates successfully issued and saved to host filesystem"
else
    echo "Failed to generate certificates or not saved to host filesystem"
    exit 1
fi

echo "==> STEP 6: Restarting Nginx with SSL config..."
NGINX_CONFIG_FILE=nginx-ssl.conf docker compose up -d --build nginx

echo "==> STEP 7: Reloading Nginx..."
docker compose exec nginx nginx -s reload || docker compose restart nginx

echo "HTTPS is now enabled for $DOMAIN"