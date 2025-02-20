from fastapi import FastAPI
import entities
from database import engine
import routes.oauth2.controller as authController
import routes.user.controller as userController
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Lab API",
    version="1.0.0",
    docs_url="/",
)

app.include_router(authController.router)
app.include_router(userController.router)

entities.Base.metadata.create_all(engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)