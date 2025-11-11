from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Database connection
def get_connection():
    return psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        database=os.getenv("PGDATABASE")
    )

# Data model for POST
class Coordinates(BaseModel):
    lat: float
    lon: float

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
            ORDER BY id DESC;
        """
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
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
    return {"database": result[0], "schema": result[1]}
