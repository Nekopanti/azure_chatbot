#!/bin/sh
set -e

echo "Substituting environment variables starts..."
echo "Current VITE_API_BASE_URL: ${VITE_API_BASE_URL}"
echo "Current VITE_AZURE_TENANT_ID: ${VITE_AZURE_TENANT_ID}"
echo "Current VITE_AZURE_CLIENT_ID: ${VITE_AZURE_CLIENT_ID}"
echo "Current VITE_REDIRECT_URI: ${VITE_REDIRECT_URI}"
echo "Current VITE_HOME_URI: ${VITE_HOME_URI}"

# Use temporary file replacement to avoid permission issues
ENV_VARS='$VITE_AZURE_TENANT_ID $VITE_AZURE_CLIENT_ID $VITE_REDIRECT_URI $VITE_HOME_URI $VITE_API_BASE_URL'

envsubst "$ENV_VARS" < /usr/share/nginx/html/index.html > /tmp/index.html
mv /tmp/index.html /usr/share/nginx/html/index.html

# Optional: Output the replaced content for debugging
cat /usr/share/nginx/html/index.html | grep VITE_API_BASE_URL

echo "Environment variable replacement completed"

# Execute the original command to start nginx
exec "$@"