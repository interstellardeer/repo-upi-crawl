# Comprehensive Deployment Guide: UPI Repository Scraper API

This document provides step-by-step instructions for deploying the UPI Repository Scraper API (built with FastAPI and SQLite) to various environments, including VPS, Cloudflare, and Platform-as-a-Service (PaaS) providers.

Since this application inherently relies on a local SQLite database and file-based data (`data/db.sqlite`), stateful deployments (like a VPS or Render with persistent disks) are strongly recommended over purely serverless options (like Cloudflare Workers/Pages or Vercel).

---

## 1. VPS Deployment (Recommended)
Deploying to a Virtual Private Server (VPS) like DigitalOcean, Linode, AWS EC2, or Hetzner is the most robust way to host this API, ensuring the SQLite database persists properly.

### Prerequisites
- A Linux VPS (Ubuntu 22.04+ recommended)
- SSH access
- Domain name pointed to the VPS IP (optional but recommended)

### Option 1.A: Deployment via Docker (Easiest)
We highly recommend Dockerizing the application so it is portable.

**1. Create a `Dockerfile` in your project root:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Start the API server
CMD ["python", "-m", "app.cli", "serve", "--host", "0.0.0.0", "--port", "8000"]
```

**2. Create a `compose.yaml` (or `docker-compose.yml`):**
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env
    restart: always
```

**3. Run on the Server:**
```bash
# Clone the repository on your VPS
git clone https://github.com/YOUR_USERNAME/repo-upi-crawl.git
cd repo-upi-crawl

# Set up environment variables
cp .env.example .env

# Build and run the container in the background
docker compose up -d
```
Your API is now running on `http://SERVER_IP:8000`.

### Option 1.B: Native Deployment with systemd & Nginx
If you prefer not to use Docker, you can run it natively using `systemd` to keep it alive and Nginx as a reverse proxy.

**1. Set up the environment:**
```bash
sudo apt update && sudo apt install python3-pip python3-venv nginx -y
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/repo-upi-crawl.git
sudo chown -R $USER:$USER repo-upi-crawl/
cd repo-upi-crawl

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

**2. Create a systemd service (`/etc/systemd/system/upicrawl.service`):**
```ini
[Unit]
Description=UPI Crawl API using FastAPI
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/opt/repo-upi-crawl
Environment="PATH=/opt/repo-upi-crawl/venv/bin"
ExecStart=/opt/repo-upi-crawl/venv/bin/python -m app.cli serve --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**3. Start the service:**
```bash
sudo systemctl daemon-reload
sudo systemctl start upicrawl
sudo systemctl enable upicrawl
```

**4. Set up Nginx Reverse Proxy (`/etc/nginx/sites-available/upicrawl`):**
```nginx
server {
    listen 80;
    server_name api.yourdomain.com; # Replace with your domain or IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_addrs;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**5. Enable Nginx and restart:**
```bash
sudo ln -s /etc/nginx/sites-available/upicrawl /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 2. Cloudflare Integration

Because this app utilizes an SQLite database, hosting it natively on Cloudflare Workers/Pages requires rewriting the database layer to use Cloudflare D1. Instead, the best practice is to **host the API on a VPS or local machine and expose it securely via Cloudflare Tunnels.**

### Cloudflare Tunnels (Zero Trust)
This allows you to securely expose your locally hosted API to the internet without opening firewall ports, assigning a public IP, or dealing with Nginx.

**1. Install `cloudflared` on your VPS or Local Machine:**
```bash
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
```

**2. Authenticate with Cloudflare:**
```bash
cloudflared tunnel login
```
*(This will provide a URL to authenticate via your browser)*

**3. Create a Tunnel:**
```bash
cloudflared tunnel create upi-api
```

**4. Configure the Tunnel:**
Create a configuration file at `~/.cloudflared/config.yml`:
```yaml
tunnel: <TUNNEL_ID> # See output of above command
credentials-file: /home/user/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: api.yourdomain.com # Must be managed in Cloudflare
    service: http://localhost:8000
  - service: http_status:404
```

**5. Route DNS to Tunnel:**
```bash
cloudflared tunnel route dns upi-api api.yourdomain.com
```

**6. Run the Tunnel as a Service:**
```bash
sudo cloudflared service install     # Installs it system-wide
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```
Your API is now accessible securely via Cloudflare edge nodes at `https://api.yourdomain.com`.

---

## 3. PaaS Deployment (Render / Railway)

Platform-as-a-Service environments like Render and Railway are great alternatives to a traditional VPS, but you **must attach a Persistent Volume** to ensure your SQLite DB won't be deleted on every redeploy.

### Render.com
1. Go to your Render Dashboard and create a **New Web Service**.
2. Connect your GitHub repository.
3. Configure settings:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m app.cli serve --host 0.0.0.0 --port $PORT`
4. Expand **Advanced Options** -> Add a **Disk**:
   - Name: `data_storage`
   - Mount Path: `/opt/render/project/src/data`
   - Size: `1 GB` (or more depending on DB size)
5. Add Environment Variables:
   - `PYTHON_VERSION`: `3.11.0` (ensure Python 3.11 is used)
6. Click **Create Web Service**.

### Railway.app
1. Go to Railway Dashboard and click **New Project** -> **Deploy from GitHub repo**.
2. Railway detects your `requirements.txt` and automatically figures out it is a Python app. Wait for initial deployment (it will likely fail or lose DB data).
3. Under **Settings** -> **Deploy**:
   - **Custom Start Command:** `python -m app.cli serve --host 0.0.0.0 --port $PORT`
4. Under **Volumes**:
   - Add a volume and mount it to `/app/data`
5. Ensure your application logic points the SQLite connection string to that volume (the current default `./data/db.sqlite` should resolve to `/app/data` if Railway working directory is `/app`, else map accordingly).

---

## 4. Securing & Maintaining the API

### Scheduling the Crawler
Since you want your API data to stay fresh, set up a cron job on your deployment environment.

**On Linux/VPS (Cron):**
```bash
crontab -e
```
Add a line to run the crawler daily at 2:00 AM incrementally:
```cron
0 2 * * * cd /opt/repo-upi-crawl && /opt/repo-upi-crawl/venv/bin/python -m app.cli crawl --incremental >> /var/log/upi-crawler.log 2>&1
```

### Adding API Key Authentication
If you wish to protect your API (e.g., specific endpoints or the `/crawl/trigger` action), make sure to configure your `.env` appropriately if required by the App Configuration, or place it behind Cloudflare Access or an Nginx Basic Auth if you want to block all public traffic.

## Summary Checklist
- [ ] Determine if you want a **VPS (best control)** or **PaaS (easiest logic but needs persistent disks)**.
- [ ] Make sure directory `data/` is persisted across deployments.
- [ ] Deploy via Docker or Systemd.
- [ ] Add a custom domain and SSL (via Nginx or Cloudflare Tunnel).
- [ ] Set up a Cron job for `--incremental` crawling to keep the API up-to-date.
