# Pawn Shop Backend API

<p align="center">
  <a href="https://fastapi.tiangolo.com/" target="_blank">
    <img src="https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png" width="200" alt="FastAPI Logo" />
  </a>
</p>

<p align="center">
  A modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints.
</p>

<p align="center">
  <a href="https://hub.docker.com/" target="_blank"><img src="https://img.shields.io/badge/Docker-ready-blue" alt="Docker Ready" /></a>
  <a href="https://fastapi.tiangolo.com/" target="_blank"><img src="https://img.shields.io/badge/FastAPI-Docs-brightgreen" alt="FastAPI Docs" /></a>
  <a href="https://pypi.org/project/fastapi/" target="_blank"><img src="https://img.shields.io/badge/PyPI-Version-brightgreen" alt="PyPI Version" /></a>
  <a href="https://github.com/tiangolo/fastapi" target="_blank"><img src="https://img.shields.io/github/stars/tiangolo/fastapi?style=social" alt="GitHub Stars" /></a>
</p>

---

## 📦 Description

This is a robust backend API for a pawn shop management system built with FastAPI. The system provides comprehensive functionality for managing pawn shop operations, including client management, order processing, product inventory, and user authentication.

## 🚀 Features

- **Authentication & Authorization**
  - OAuth2 implementation for secure access
  - User management and role-based access control

- **Client Management**
  - Client registration and profile management
  - Client history tracking
  - Client relationship management

- **Pawn Operations**
  - Pawn item registration
  - Valuation management
  - Contract generation and management
  - Interest calculation

- **Order Processing**
  - Order creation and management
  - Transaction history
  - Payment processing

- **Product Management**
  - Inventory management
  - Product categorization
  - Product status tracking

## 🛠️ Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL (via SQLAlchemy)
- **Authentication:** OAuth2
- **Containerization:** Docker
- **API Documentation:** Swagger/OpenAPI

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- Docker (recommended)
- pip (Python package manager)

### Local Development

1. Create Virtual Environment
- For Windows
```bash
# Create environment
python -m venv env

# Activate environment
env\Scripts\activate
```
- For Mac/Linux
```bash
# Create environment
python3 -m venv venv

# Activate environment
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (create `.env` file):
```env
DATABASE_URL=postgresql://username:password@localhost:5432/pawnshop
SECRET_KEY=your-super-secret-key-here
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000
ALLOWED_HOSTS=localhost,127.0.0.1
```

4. Run the application:
```bash
uvicorn main:app --reload
```

### Docker Deployment (Recommended)

#### Development
```bash
# 1. Create .env file with your configuration
# 2. Build and start containers
docker compose up --build
```

#### Production
```bash
# 1. Set environment variables
export SECRET_KEY="your-super-secret-production-key"
export POSTGRES_PASSWORD="strong-production-password"
export ALLOWED_ORIGINS="https://yourdomain.com"

# 2. Build and start in production mode
docker compose up --build -d
```

## 🔐 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `SECRET_KEY` | Secret key for JWT tokens | Yes | - |
| `ENVIRONMENT` | Environment (development/production) | No | development |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | No | http://localhost:3000 |
| `ALLOWED_HOSTS` | Trusted hosts (comma-separated) | No | localhost,127.0.0.1 |
| `POSTGRES_USER` | PostgreSQL username | No | pawnshop |
| `POSTGRES_PASSWORD` | PostgreSQL password | No | pawnshop123 |
| `POSTGRES_DB` | PostgreSQL database name | No | pawnshop |

## 📚 API Documentation

Once the application is running, you can access:

- Swagger UI documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

## 🚀 Production Deployment Checklist

- [ ] Set strong `SECRET_KEY` for production
- [ ] Configure proper `ALLOWED_ORIGINS` for your frontend domain
- [ ] Set up proper `ALLOWED_HOSTS` for your domain
- [ ] Use strong database passwords
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure SSL/TLS certificates
- [ ] Set up database backups
- [ ] Configure monitoring and logging
- [ ] Set up proper firewall rules
- [ ] Consider using a reverse proxy (nginx)

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Error**: Ensure PostgreSQL is running and `DATABASE_URL` is correct
2. **CORS Errors**: Check `ALLOWED_ORIGINS` configuration
3. **Authentication Issues**: Verify `SECRET_KEY` is set correctly

### Health Check

The application includes a health check endpoint at `/health` that returns:
```json
{
  "status": "healthy",
  "environment": "production",
  "version": "1.0.0"
}
```
