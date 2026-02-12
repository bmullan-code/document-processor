# Stage 1: Build
FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Use nginx template for environment variable substitution
# This expects a BACKEND_URL environment variable
RUN mkdir -p /etc/nginx/templates
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
    location /api/ { \
        proxy_pass ${BACKEND_URL}/; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
}' > /etc/nginx/templates/default.conf.template

EXPOSE 80
# The default entrypoint for the nginx image will run envsubst on files in /etc/nginx/templates/
# and output them to /etc/nginx/conf.d/
CMD ["nginx", "-g", "daemon off;"]
