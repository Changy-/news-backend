from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import api

app = FastAPI(title="News Assistant Backend")

# CORS - Allow requests from frontend
# In production, you should replace "*" with your public frontend URL
origins = [
    "https://news-frontend-997996759702.us-west1.run.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "News Assistant API is running"}
