"""RoadSafe AI backend: REST + WebSocket. Run: uvicorn main:app --reload"""
import asyncio, os, random, time
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

TOKEN = os.getenv("POLICE_TOKEN", "demo-token")      # CHANGE for any real use
DEMO_FEED = os.getenv("DEMO_FEED", "1") == "1"        # fictional alerts, clearly labelled
try:
    import joblib; MODEL = joblib.load("model.pkl")
except Exception:
    MODEL = None

app = FastAPI(title="RoadSafe AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
ALERTS: list[dict] = []
CLIENTS: set[WebSocket] = set()

class SpeedReport(BaseModel):
    vehicle: str = Field(min_length=3, max_length=32)   # anonymised ID, never owner data
    speed: float = Field(ge=0, le=400)
    limit: float = Field(gt=0, le=200)
    location: str = "Unknown"
    consent: bool = False                               # driver must consent to sharing
    braking_events: int = 0
    night: bool = False

def risk(over, brakes, night):
    if MODEL is not None:
        return int(MODEL.predict([[over, brakes, int(night)]])[0])
    s = over * 1.2 + brakes * 5 + (10 if night else 0)
    return 2 if s > 60 else 1 if s > 30 else 0

def auth(token: Optional[str]):
    if token != TOKEN:
        raise HTTPException(401, "Police authentication required")

async def broadcast(a):
    for c in list(CLIENTS):
        try: await c.send_json(a)
        except Exception: CLIENTS.discard(c)

@app.get("/api/health")
def health(): return {"ok": True, "model": MODEL is not None, "demo_feed": DEMO_FEED}

@app.post("/api/speed")
async def report(r: SpeedReport):
    """Driver app posts speed. Alerts reach police only if the driver consented."""
    over = r.speed - r.limit
    if over <= 0: return {"overspeed": False}
    a = {"id": int(time.time() * 1000), "veh": r.vehicle, "spd": round(r.speed), "lim": round(r.limit),
         "loc": r.location, "risk": risk(over, r.braking_events, r.night), "demo": False}
    if r.consent:
        ALERTS.append(a); await broadcast(a)
    return {"overspeed": True, "excess": round(over), "shared_with_police": r.consent}

@app.get("/api/alerts")
def alerts(x_police_token: Optional[str] = Header(None)):
    auth(x_police_token); return ALERTS[-200:]

@app.post("/api/alerts/{aid}/{action}")
def act(aid: int, action: str, x_police_token: Optional[str] = Header(None)):
    auth(x_police_token)
    if action not in ("ack", "resolve"): raise HTTPException(400, "bad action")
    for a in ALERTS:
        if a["id"] == aid: a["status"] = "Acknowledged" if action == "ack" else "Resolved"; return a
    raise HTTPException(404, "not found")

@app.websocket("/ws/alerts")
async def ws(sock: WebSocket, token: Optional[str] = Query(None)):
    if token != TOKEN: await sock.close(code=4401); return
    await sock.accept(); CLIENTS.add(sock)
    try:
        while True: await sock.receive_text()
    except WebSocketDisconnect:
        CLIENTS.discard(sock)

@app.on_event("startup")
async def demo():
    async def loop():
        while True:
            await asyncio.sleep(8)
            lim = random.choice([40, 50, 60, 80])
            a = {"id": int(time.time() * 1000), "veh": f"DEMO-{random.randint(1000, 9999)}",
                 "spd": lim + random.randint(5, 40), "lim": lim, "loc": "Demo location", "demo": True}
            ALERTS.append(a); await broadcast(a)
    if DEMO_FEED: asyncio.create_task(loop())
