# RoadSafe AI
Frontend: open `frontend/index.html` in a browser (no build step). Works fully in demo mode.

Backend (optional, live alerts):
    cd backend && pip install -r requirements.txt
    python train_model.py            # trains on SYNTHETIC data
    uvicorn main:app --reload        # http://localhost:8000/docs

Then in Police Dashboard click "Connect live feed" and enter:
    ws://localhost:8000/ws/alerts?token=demo-token

Set POLICE_TOKEN to change the token; DEMO_FEED=0 disables fictional alerts.
Notes: the demo sign-in (officer / demo) is client-side only; use real SSO + HTTPS in production.
Alerts reach police only with driver consent. No fines, no owner lookup.
