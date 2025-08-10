
# === Build Stage ===
FROM node:23-alpine AS builder

WORKDIR /app

# Copy dependency files
COPY package.json package-lock.json ./

RUN npm ci

# Copy all app source and config files
COPY . .

RUN npm run build

# === Production Stage ===
FROM nginx:1.28-alpine

COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
