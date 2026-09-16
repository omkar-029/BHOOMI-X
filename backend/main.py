from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="BHOOMI-X API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "project": "BHOOMI-X",
        "total_parcels": 500,
        "officer_reviews": 8,
        "auto_cleared": 492,
        "owner_conflicts": 3,
        "area_conflicts": 4,
        "geometry_conflicts": 1
    }


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/stats")
def stats():
    return {
        "total_parcels": 500,
        "officer_reviews": 8,
        "auto_cleared": 492,
        "owner_conflicts": 3,
"area_conflicts": 4,
"geometry_conflicts": 1
    }
