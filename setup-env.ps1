# PowerShell script to set up environment variables for Pawn Shop Backend
# Run this script before starting Docker Compose

Write-Host "Setting up environment variables for Pawn Shop Backend..." -ForegroundColor Green

# Set environment variables
$env:DATABASE_URL = "postgresql://pawnshop:pawnshop123@db:5432/pawnshop"
$env:SECRET_KEY = "your-super-secret-production-key-change-this"
$env:ALGORITHM = "HS256"
$env:ACCESS_TOKEN_EXPIRE_MINUTES = "30"
$env:REFRESH_TOKEN_EXPIRE_DAYS = "7"
$env:ENVIRONMENT = "production"
$env:ALLOWED_ORIGINS = "http://localhost:3000"
$env:ALLOWED_HOSTS = "localhost,127.0.0.1"
$env:POSTGRES_USER = "pawnshop"
$env:POSTGRES_PASSWORD = "pawnshop123"
$env:POSTGRES_DB = "pawnshop"

Write-Host "Environment variables set successfully!" -ForegroundColor Green
Write-Host "You can now run: docker compose up --build" -ForegroundColor Yellow

# Optional: Create .env file
$envContent = @"
# Database Configuration
DATABASE_URL=$env:DATABASE_URL

# Security
SECRET_KEY=$env:SECRET_KEY

# Environment
ENVIRONMENT=$env:ENVIRONMENT

# CORS Configuration
ALLOWED_ORIGINS=$env:ALLOWED_ORIGINS
ALLOWED_HOSTS=$env:ALLOWED_HOSTS

# PostgreSQL Configuration
POSTGRES_USER=$env:POSTGRES_USER
POSTGRES_PASSWORD=$env:POSTGRES_PASSWORD
POSTGRES_DB=$env:POSTGRES_DB

# OAuth2 Configuration
ALGORITHM=$env:ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES=$env:ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS=$env:REFRESH_TOKEN_EXPIRE_DAYS
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8
Write-Host ".env file created successfully!" -ForegroundColor Green 