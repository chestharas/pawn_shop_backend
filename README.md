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
  <a href="https://pypi.org/project/fastapi/" target="_blank"><img src="https://img.shields.io/pypi/v/fastapi" alt="PyPI Version" /></a>
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
- **Database:** SQL Database (via SQLAlchemy)
- **Authentication:** OAuth2
- **Containerization:** Docker
- **API Documentation:** Swagger/OpenAPI

## 🏗️ Project Structure

```
pawn_shop_backend/
├── routes/
│   ├── client/         # Client management endpoints
│   ├── oauth2/         # Authentication endpoints
│   ├── order/          # Order processing endpoints
│   ├── pawn/           # Pawn operations endpoints
│   ├── product/        # Product management endpoints
│   └── user/           # User management endpoints
├── database.py         # Database configuration
├── entities.py         # Database entities
├── main.py            # Application entry point
├── response_model.py   # API response models
├── requirements.txt    # Project dependencies
└── docker-compose.yaml # Docker configuration
```

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- Docker (optional)
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd pawn_shop_backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn main:app --reload
```

### Docker Deployment

To run the application using Docker:

```bash
docker-compose up -d
```

## 📚 API Documentation

Once the application is running, you can access:

- Swagger UI documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

## 🔐 Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
```
