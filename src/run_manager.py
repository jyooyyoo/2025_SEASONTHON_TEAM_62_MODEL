import uuid
from datetime import datetime

# In a real application, these would interact with a database
favorites_db = {}
running_sessions_db = {}

def add_favorite_route(route_info, name):
    favorite_id = str(uuid.uuid4())
    favorite_info = {
        "favorite_id": favorite_id,
        "route_id": route_info["route_id"],
        "name": name,
        "distance_km": route_info["distance_km"],
        "category": route_info["category"],
        "safety_score": route_info["safety_score"],
        "estimated_time_min": route_info["estimated_time_min"],
        "pace_min_per_km": route_info["pace_min_per_km"]
    }
    favorites_db[favorite_id] = favorite_info
    return favorite_info

def start_running_session(route_id, planned_pace_min_per_km):
    session_id = str(uuid.uuid4())
    session_info = {
        "session_id": session_id,
        "route_id": route_id,
        "status": "started",
        "planned_pace_min_per_km": planned_pace_min_per_km,
        "start_time": datetime.utcnow().isoformat() + "Z"
    }
    running_sessions_db[session_id] = session_info
    return session_info

def update_running_session(session_id, data):
    # This is a dummy function. In a real app, it would update live metrics.
    if session_id not in running_sessions_db:
        raise ValueError("Session not found")

    # Update logic here...

    return {"status": "updated"}

def finish_running_session(session_id):
    if session_id not in running_sessions_db:
        raise ValueError("Session not found")

    session_info = running_sessions_db[session_id]

    # Calculate final metrics. This is dummy data.
    end_time = datetime.utcnow()
    start_time = datetime.fromisoformat(session_info['start_time'].replace('Z', '+00:00'))
    total_time = (end_time - start_time).total_seconds() / 60

    result_info = {
        "session_id": session_id,
        "total_time_min": round(total_time, 2),
        "average_pace_min_per_km": 6.5,
        "actual_distance_km": 5.2,
        "safety_score": 88
    }

    # Clear session from "active" sessions.
    del running_sessions_db[session_id]

    return result_info
