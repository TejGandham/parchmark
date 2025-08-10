
# === Build Stage ===
FROM node:23-alpine AS builder

WORKDIR /app

# Copy dependency files from repo root
COPY package.json package-lock.json ./

RUN npm ci

# Copy all app source and config (from repo root, NOT from infra/)
COPY . .

RUN npm run build

# === Production Stage ===
FROM nginx:1.28-alpine

# Copy the built app
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configs and entrypoint
COPY nginx.http.conf /etc/nginx/conf.d/nginx.http.conf
COPY nginx.https.conf /etc/nginx/conf.d/nginx.https.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

# Run the entrypoint script
CMD ["/entrypoint.sh"]