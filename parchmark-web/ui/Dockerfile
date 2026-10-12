# === Build Stage ===
FROM node:24-alpine AS builder

ARG GIT_SHA=dev
ARG BUILD_DATE=unknown
ARG APP_VERSION=dev

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ENV GIT_SHA=$GIT_SHA
ENV BUILD_DATE=$BUILD_DATE
ENV APP_VERSION=$APP_VERSION

RUN npm run build

# === Production Stage ===
FROM nginx:1.28-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.http.conf /etc/nginx/conf.d/nginx.http.conf
COPY nginx.https.conf /etc/nginx/conf.d/nginx.https.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

CMD ["/entrypoint.sh"]
