from fastapi import FastAPI
import entities
from database import engine
import routes.oauth2.controller as authController
import routes.product.controller as productController
import routes.client.controller as orderClientController
import routes.order.controller as orderController
import routes.pawn.controller as pawncontroller
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Lab API",
    version="1.0.0",
    docs_url="/",
)

app.include_router(authController.router)
app.include_router(productController.router)
app.include_router(orderClientController.router)
app.include_router(orderController.router)
app.include_router(pawncontroller.router)

entities.Base.metadata.create_all(engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
