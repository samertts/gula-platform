#!/bin/bash

echo "Starting GULA production architecture upgrade..."

# إنشاء هيكل مشروع احترافي
mkdir -p backend
mkdir -p backend/api
mkdir -p backend/services
mkdir -p backend/models
mkdir -p frontend/assets
mkdir -p docker
mkdir -p scripts
mkdir -p docs
mkdir -p nginx

echo "Project structure created"

# إنشاء .gitignore احترافي
cat > .gitignore << 'EOF'
venv/
__pycache__/
*.pyc
.env
node_modules/
dist/
build/
*.log
EOF

echo "gitignore configured"

# تنظيف cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

echo "Cache cleaned"

# إنشاء API backend خفيف باستخدام FastAPI
cat > backend/app.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="GULA Health Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/api/version")
def version():
    return {"version":"1.0"}
EOF

echo "FastAPI backend created"

# إنشاء requirements
cat > requirements.txt << 'EOF'
fastapi
uvicorn
redis
python-multipart
EOF

echo "requirements.txt created"

# إعداد Docker
cat > docker/Dockerfile << 'EOF'
FROM python:3.10

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["uvicorn","backend.app:app","--host","0.0.0.0","--port","8000"]
EOF

echo "Dockerfile created"

# docker-compose
cat > docker/docker-compose.yml << 'EOF'
version: "3"

services:

  gula-backend:
    build: ..
    container_name: gula-backend
    ports:
      - "8000:8000"

  redis:
    image: redis
    container_name: gula-redis
    ports:
      - "6379:6379"

  nginx:
    image: nginx
    container_name: gula-nginx
    ports:
      - "80:80"
    volumes:
      - ../nginx/nginx.conf:/etc/nginx/nginx.conf
EOF

echo "Docker compose created"

# nginx gateway
cat > nginx/nginx.conf << 'EOF'
events {}

http {

server {

listen 80;

location /api/ {
proxy_pass http://gula-backend:8000/;
}

location / {
root /usr/share/nginx/html;
}

}

}
EOF

echo "Nginx gateway created"

# CDN للواجهة
mkdir -p frontend/cdn

cat > frontend/cdn/libraries.html << 'EOF'
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">

<script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
EOF

echo "Frontend CDN layer added"

# سكريبت تشغيل
cat > scripts/start_platform.sh << 'EOF'
#!/bin/bash
docker compose -f docker/docker-compose.yml up -d
EOF

chmod +x scripts/start_platform.sh

echo "Startup script created"

# إضافة التعديلات إلى Git
git add .

git commit -m "Upgrade GULA platform to production architecture"

git push origin main

echo "Upgrade completed successfully"
