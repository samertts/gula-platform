# syntax=docker/dockerfile:1.7

FROM node:22.13-alpine AS build
WORKDIR /app

# Install dependencies from the committed npm lockfile for reproducible builds.
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.28-alpine AS runtime

# Run the static server as the unprivileged nginx user where supported.
COPY --from=build /app/dist /usr/share/nginx/html

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=5s \
  CMD wget -q --spider http://127.0.0.1:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

