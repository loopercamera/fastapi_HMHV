from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

# Database connection
# Database connection using DATABASE_URL
def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


# Data model for POST
class Coordinates(BaseModel):
    lat: float
    lon: float
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify list like ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/coordinates")
def add_coordinates(coords: Coordinates):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            INSERT INTO user_positions (geom, created_at)
            VALUES (ST_SetSRID(ST_MakePoint(%s, %s), 4326), NOW())
            RETURNING id;
        """
        cur.execute(query, (coords.lon, coords.lat))
        new_id = cur.fetchone()["id"]
        conn.commit()
        cur.close()
        conn.close()
        return {"success": True, "id": new_id}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/coordinates")
def get_coordinates():
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT id,
                   ST_Y(geom) AS lat,
                   ST_X(geom) AS lon,
                   created_at
            FROM user_positions
            ORDER BY created_at DESC
            LIMIT 1;
        """
        cur.execute(query)
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Database query error")


@app.get("/api/info/db")
def get_info():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {"status": "ok", "database_version": db_version}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Database connection failed")

@app.get("/api/info/api")
def get_info():
    try:
        return {"status": "ok", "api_version": "1.0.0"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="API information retrieval failed")
    


@app.get("/api/debug/db")
def debug_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT current_database(), current_schema();")
    result = cur.fetchone()
    cur.close()
    conn.close()

    # Parse DATABASE_URL and mask password
    db_url = os.getenv("DATABASE_URL")
    parsed = urlparse(db_url)
    safe_url = f"{parsed.scheme}://{parsed.username}:***@{parsed.hostname}:{parsed.port}{parsed.path}"

    return {
        "database": result[0],
        "schema": result[1],
        "connection_url": safe_url
    }


@app.get("/api/coordinates/sara")
def get_coordinates():
    return {
        "id": 16,
        "lat": 47.46385684116505,
        "lon": 8.39244934396616,
        "created_at": "2025-11-08T10:08:44.306761"
    }


@app.post("/api/child/coordinates")
def add_coordinates(coords: Coordinates):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            INSERT INTO users (user_name, user_function, geom, created_at)
            VALUES (%s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), NOW())
            RETURNING id;
        """

        cur.execute(
            query,
            (
                coords.user_name,
                coords.user_function,
                coords.lon,
                coords.lat,
            ),
        )

        new_id = cur.fetchone()["id"]
        conn.commit()
        cur.close()
        conn.close()

        return {"success": True, "id": new_id}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/child/coordinates")
def get_coordinates():
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                id,
                user_name,
                user_function,
                ST_AsGeoJSON(geom) AS geom,
                created_at
            FROM users
            ORDER BY created_at DESC;
        """

        cur.execute(query)
        data = cur.fetchall()

        cur.close()
        conn.close()

        return {"success": True, "data": data}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
