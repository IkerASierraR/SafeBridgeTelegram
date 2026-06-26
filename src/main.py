from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1.backup import router as backup_router
from src.api.v1.verify import router as verify_router
from src.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API REST para generar y verificar backups de bases de datos para consumo desde un bot de Telegram."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(backup_router, prefix=f"{settings.API_V1_STR}", tags=["backup"])
app.include_router(verify_router, prefix=f"{settings.API_V1_STR}", tags=["verify"])

@app.get("/")
def root():
    return {"message": "SafeBridge API Backend Running"}
