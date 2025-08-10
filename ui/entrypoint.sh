#!/bin/sh
set -e

if [ "$USE_HTTPS" = "true" ]; then
    echo "Using HTTPS configuration"
    cp /etc/nginx/conf.d/nginx.https.conf /etc/nginx/conf.d/default.conf
else
    echo "Using HTTP configuration"
    cp /etc/nginx/conf.d/nginx.http.conf /etc/nginx/conf.d/default.conf
fi

# Start Nginx
exec nginx -g 'daemon off;'
