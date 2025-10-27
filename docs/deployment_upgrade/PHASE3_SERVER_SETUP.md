# Phase 3: Server Setup Guide

This guide walks you through setting up your production server for automated deployments.

**Server**: `notes.engen.tech` (also `assets-api.engen.tech`)
**Time Required**: ~15-20 minutes
**Prerequisites**: SSH access to your production server

---

## Step 1: Create Deploy User

SSH to your production server and create a dedicated deploy user:

```bash
# SSH to production server
ssh your-current-user@notes.engen.tech

# Create dedicated deploy user
sudo useradd -m -s /bin/bash deploy

# Add to docker group (required for docker commands)
sudo usermod -aG docker deploy

# Create SSH directory with proper permissions
sudo -u deploy mkdir -p /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
```

**Verify**:
```bash
# Check user was created
id deploy
# Should show: uid=... gid=... groups=...,docker

# Check docker group membership
groups deploy
# Should include 'docker'
```

---

## Step 2: Generate SSH Key Pair

**⚠️ Run this on YOUR LOCAL MACHINE, not the server!**

```bash
# Generate ED25519 key (modern, secure standard)
ssh-keygen -t ed25519 -C "github-actions-parchmark" -f ~/.ssh/parchmark_deploy

# This creates two files:
# - ~/.ssh/parchmark_deploy (private key) - for GitHub Secrets
# - ~/.ssh/parchmark_deploy.pub (public key) - for server
```

**Security Notes**:
- ED25519 is the modern standard (more secure than RSA)
- Private key stays on your local machine (will be copied to GitHub Secrets)
- Public key goes on the server

---

## Step 3: Install Public Key on Server

**On your local machine**, display the public key:

```bash
# Display the public key
cat ~/.ssh/parchmark_deploy.pub

# Copy the entire output (starts with 'ssh-ed25519...')
```

**On the production server**, add it to authorized_keys:

```bash
# SSH to production server (if not already connected)
ssh your-current-user@notes.engen.tech

# Edit authorized_keys for deploy user
sudo -u deploy nano /home/deploy/.ssh/authorized_keys

# Paste the public key (one line)
# Save and exit (Ctrl+X, Y, Enter)

# Set proper permissions (IMPORTANT!)
sudo chmod 600 /home/deploy/.ssh/authorized_keys
sudo chown deploy:deploy /home/deploy/.ssh/authorized_keys
```

**Verify permissions**:
```bash
ls -la /home/deploy/.ssh/
# Should show:
# drwx------ 2 deploy deploy ... .
# -rw------- 1 deploy deploy ... authorized_keys
```

---

## Step 4: Test SSH Connection

**⚠️ Do NOT proceed until this works!**

**On your local machine**:

```bash
# Test SSH connection with the new key
ssh -i ~/.ssh/parchmark_deploy deploy@notes.engen.tech

# Should connect without password prompt!

# Once connected, test Docker access:
docker ps
# Should list running containers (or empty list if none running)

# Test Docker Compose:
docker compose version
# Should show version v2.20+ or higher

# Exit the SSH session
exit
```

**Troubleshooting**:
- **"Permission denied"**: Check authorized_keys permissions (600)
- **"Connection refused"**: Check server SSH config allows key auth
- **"docker: permission denied"**: User not in docker group, run `sudo usermod -aG docker deploy` and logout/login

---

## Step 5: Directory Setup

**SSH as the deploy user**:

```bash
ssh -i ~/.ssh/parchmark_deploy deploy@notes.engen.tech

# Create project directory
mkdir -p /home/deploy/parchmark
cd /home/deploy/parchmark

# Clone repository (will get latest code)
git clone https://github.com/TejGandham/parchmark.git .

# Verify files are present
ls -la
# Should show: backend/, ui/, docker-compose.prod.yml, etc.

# Create directories for environment files
mkdir -p backend
mkdir -p ui
```

**Alternative** (if you prefer manual file transfer):
```bash
# On local machine, copy files to server
scp -i ~/.ssh/parchmark_deploy docker-compose.prod.yml deploy@notes.engen.tech:/home/deploy/parchmark/
```

---

## Step 6: Create Production Environment Files

### Backend Environment File

**On the production server** (as deploy user):

```bash
cd /home/deploy/parchmark/backend
nano .env.production
```

**Contents**:
```env
# Database Configuration
DATABASE_URL=postgresql://parchmark_user:parchmark_password@postgres:5432/parchmark_db

# JWT Configuration - GENERATE NEW SECRET!
# Run this command to generate: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=YOUR_GENERATED_SECRET_KEY_HERE
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS - Update with your actual domains
ALLOWED_ORIGINS=https://notes.engen.tech,https://assets-api.engen.tech

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
```

**Generate a secure SECRET_KEY**:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output and paste it as SECRET_KEY value
```

### Frontend Environment File

```bash
cd /home/deploy/parchmark/ui
nano .env.production
```

**Contents**:
```env
# API URL (proxied by Nginx)
VITE_API_URL=/api

# Token warning (optional, defaults to 60 seconds)
VITE_TOKEN_WARNING_SECONDS=60
```

### Database Environment File

```bash
cd /home/deploy/parchmark
nano .env.db
```

**Contents**:
```env
# PostgreSQL Database Configuration
# CHANGE THESE VALUES FOR PRODUCTION!
POSTGRES_USER=parchmark_user
POSTGRES_PASSWORD=GENERATE_STRONG_PASSWORD_HERE
POSTGRES_DB=parchmark_db
```

**Generate a strong password**:
```bash
# Generate a 32-character password
openssl rand -base64 32
# Or use: pwgen -s 32 1
```

---

## Step 7: Verify Setup

**On production server**:

```bash
cd /home/deploy/parchmark

# Verify all required files exist
ls -la backend/.env.production
ls -la ui/.env.production
ls -la .env.db
ls -la docker-compose.prod.yml

# Verify Docker Compose syntax
docker compose -f docker-compose.prod.yml config > /dev/null && echo "✓ Configuration valid"

# Check network exists (required for Nginx Proxy Manager)
docker network inspect proxiable
# Should show network details (not "network not found")
```

---

## Step 8: Initial Manual Deployment (Optional Test)

**⚠️ Only if you want to test before setting up CI/CD**

```bash
cd /home/deploy/parchmark

# Note: Images won't exist in GHCR yet, so this will fail
# This is expected - we'll build images in Phase 5
# For now, you can test with local builds if needed:

# Temporarily change docker-compose.prod.yml to use build instead of image
# OR wait until Phase 5 to build images in GitHub Actions
```

---

## Phase 3 Checklist

- [x] Deploy user created with docker group access
- [x] SSH key pair generated (ED25519)
- [x] Public key installed on server
- [x] SSH connection tested and working
- [x] Project directory created at `/home/deploy/parchmark`
- [x] Repository cloned or files transferred
- [x] Backend `.env.production` created with generated SECRET_KEY
- [x] Frontend `.env.production` created
- [x] Database `.env.db` created with strong password
- [x] Docker Compose configuration validated
- [x] `proxiable` network exists (for Nginx Proxy Manager)

---

## Security Reminders

1. **Never commit** `.env.production` or `.env.db` files
2. **Use strong passwords** for POSTGRES_PASSWORD (32+ characters)
3. **Generate unique SECRET_KEY** (never reuse from examples)
4. **Keep private key secure** (`~/.ssh/parchmark_deploy`)
5. **Rotate keys quarterly** as per security best practices

---

## Next Steps

Once Phase 3 is complete:
- **Phase 4**: Configure GitHub Secrets (add SSH key and server info)
- **Phase 5**: Create GitHub Actions workflow (automated deployment)
- **Phase 6**: Add Makefile integration (convenience commands)

---

## Troubleshooting

### Docker Permission Denied
```bash
# Add deploy user to docker group
sudo usermod -aG docker deploy

# Logout and login again for changes to take effect
exit
ssh -i ~/.ssh/parchmark_deploy deploy@notes.engen.tech
```

### Network "proxiable" Not Found
```bash
# Create the network if it doesn't exist
docker network create proxiable
```

### SSH Connection Issues
```bash
# Check SSH config on server
sudo nano /etc/ssh/sshd_config
# Ensure these are set:
# PubkeyAuthentication yes
# PasswordAuthentication no (for security)

# Restart SSH service
sudo systemctl restart sshd
```

---

**Phase 3 Complete!** 🎉

Your server is now ready for automated deployments via GitHub Actions.
