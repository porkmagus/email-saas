# Frontend Dockerfile — Build React app and serve with Nginx
# Node 24.15.0 LTS for build, Nginx 1.31.1 for serving

# Build stage
FROM node:24.15.0-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# Runtime stage
FROM nginx:1.31.1-alpine-slim AS runtime

# Security headers and compression
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=5 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1/ || exit 1
