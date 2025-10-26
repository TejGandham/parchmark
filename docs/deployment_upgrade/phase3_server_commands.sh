#!/bin/bash
# Phase 3: Server Setup Commands
# This script contains all commands to run on the production server
#
# ⚠️ DO NOT run this script directly!
# Copy and paste commands one section at a time and verify each step.

# ==============================================================================
# SECTION 1: Create Deploy User (run as your regular user with sudo)
# ==============================================================================

echo "Creating deploy user..."
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG docker deploy
sudo -u deploy mkdir -p /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh

echo "Verifying deploy user..."
id deploy
groups deploy

# ==============================================================================
# SECTION 2: Install Public Key (run as your regular user with sudo)
# ==============================================================================

echo "Installing public key..."
echo "Paste your public key content here, then run:"
echo "sudo -u deploy nano /home/deploy/.ssh/authorized_keys"
echo "# Paste the public key content"
echo "# Save and exit (Ctrl+X, Y, Enter)"

# Set permissions
sudo chmod 600 /home/deploy/.ssh/authorized_keys
sudo chown deploy:deploy /home/deploy/.ssh/authorized_keys

echo "Verifying permissions..."
ls -la /home/deploy/.ssh/

# ==============================================================================
# SECTION 3: Directory Setup (run as deploy user after SSH)
# ==============================================================================

echo "Setting up project directory..."
mkdir -p /home/deploy/parchmark
cd /home/deploy/parchmark

# Clone repository
git clone https://github.com/TejGandham/parchmark.git .

# Create environment file directories
mkdir -p backend
mkdir -p ui

echo "Verifying files..."
ls -la

# ==============================================================================
# SECTION 4: Generate Secret Keys
# ==============================================================================

echo "Generating JWT secret key..."
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
echo "^ Copy this value for SECRET_KEY in backend/.env.production"

echo ""
echo "Generating database password..."
openssl rand -base64 32
echo "^ Copy this value for POSTGRES_PASSWORD in .env.db"

# ==============================================================================
# SECTION 5: Create Environment Files
# ==============================================================================

echo "Creating backend environment file..."
cat > backend/.env.production << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://parchmark_user:parchmark_password@postgres:5432/parchmark_db

# JWT Configuration - PASTE GENERATED SECRET_KEY HERE
SECRET_KEY=PASTE_GENERATED_SECRET_KEY_HERE
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Configuration
ALLOWED_ORIGINS=https://notes.engen.tech,https://assets-api.engen.tech

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
EOF

echo "Creating frontend environment file..."
cat > ui/.env.production << 'EOF'
# API URL (proxied by Nginx)
VITE_API_URL=/api

# Token warning
VITE_TOKEN_WARNING_SECONDS=60
EOF

echo "Creating database environment file..."
cat > .env.db << 'EOF'
# PostgreSQL Configuration - PASTE GENERATED PASSWORD HERE
POSTGRES_USER=parchmark_user
POSTGRES_PASSWORD=PASTE_GENERATED_PASSWORD_HERE
POSTGRES_DB=parchmark_db
EOF

echo "⚠️  IMPORTANT: Edit the files above to add your generated secrets!"
echo "nano backend/.env.production  # Update SECRET_KEY"
echo "nano .env.db                  # Update POSTGRES_PASSWORD"

# ==============================================================================
# SECTION 6: Verify Setup
# ==============================================================================

echo "Verifying configuration..."
docker compose -f docker-compose.prod.yml config > /dev/null && echo "✓ Docker Compose config valid"

echo "Checking proxiable network..."
docker network inspect proxiable || docker network create proxiable

echo ""
echo "✓ Phase 3 server setup complete!"
echo ""
echo "Next steps:"
echo "1. Verify all environment files have correct values"
echo "2. Move to Phase 4: Configure GitHub Secrets"
echo "3. Move to Phase 5: Create GitHub Actions workflow"
