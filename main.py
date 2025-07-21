import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

import entities
from database import engine, SessionLocal
import routes.oauth2.controller as authController
import routes.product.controller as productController
import routes.client.controller as orderClientController
import routes.order.controller as orderController
import routes.pawn.controller as pawncontroller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

def create_default_admin_user():
    """Create a default admin user if no admin users exist"""
    try:
        logger.info("🔍 Checking for existing admin users...")
        db = SessionLocal()
        
        # Check if any admin user exists
        from entities import Account
        admin_exists = db.query(Account).filter(Account.role == "admin").first()
        
        if admin_exists:
            logger.info(f"✅ Admin user already exists: {admin_exists.phone_number}")
            logger.info("Skipping default user creation")
        else:
            logger.info("❌ No admin user found, creating default admin...")
            # Create default admin user
            from routes.oauth2.repository import create_user
            
            default_admin_name = os.getenv("DEFAULT_ADMIN_NAME")
            default_admin_phone = os.getenv("DEFAULT_ADMIN_PHONE")
            default_admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
            
            # Check if all required environment variables are set
            if not all([default_admin_name, default_admin_phone, default_admin_password]):
                logger.error("❌ Missing required admin user environment variables!")
                logger.error("Please set DEFAULT_ADMIN_NAME, DEFAULT_ADMIN_PHONE, and DEFAULT_ADMIN_PASSWORD in your .env file")
                return
            
            logger.info(f"📝 Creating admin user with:")
            logger.info(f"   Name: {default_admin_name}")
            logger.info(f"   Phone: {default_admin_phone}")
            logger.info(f"   Password: {default_admin_password}")
            
            create_user(
                db=db,
                cus_name=default_admin_name,
                phone_number=default_admin_phone,
                password=default_admin_password
            )
            
            logger.info(f"✅ Default admin user created successfully!")
            logger.info(f"📧 Phone: {default_admin_phone}")
            logger.info(f"🔑 Password: {default_admin_password}")
            logger.info(f"⚠️  Please change the default password after first login!")
            
    except Exception as e:
        logger.error(f"❌ Failed to create default admin user: {e}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Lab API...")
    
    # Create database tables (consider using Alembic migrations in production)
    try:
        entities.Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    # Create default admin user
    create_default_admin_user()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Lab API...")

app = FastAPI(
    title="Pawn Shop Backend API",
    version="1.0.0",
    docs_url="/docs",  # Always enable Swagger docs
    redoc_url="/redoc",  # Always enable ReDoc
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=ALLOWED_HOSTS
)

# CORS middleware with environment-specific configuration
if ENVIRONMENT == "development":
    # Development: Allow localhost origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )
else:
    # Production: Strict CORS policy
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,  # Should be specific domains
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
        expose_headers=["X-Total-Count"],
    )

# Health check endpoint for Docker health checks and load balancers
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring and load balancers"""
    try:
        # You can add database connectivity check here
        # db_status = check_database_connection()
        return {
            "status": "healthy",
            "environment": ENVIRONMENT,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Pawn Shop Backend API",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_check": "/health"
    }

# Include routers with prefixes for better organization
app.include_router(authController.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(productController.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(orderClientController.router, prefix="/api/v1/clients", tags=["Clients"])
app.include_router(orderController.router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(pawncontroller.router, prefix="/api/v1/pawn", tags=["Pawn"])

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Use PORT from env, default to 8000
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=ENVIRONMENT == "development",
        log_level="debug" if ENVIRONMENT == "development" else "info"
    )