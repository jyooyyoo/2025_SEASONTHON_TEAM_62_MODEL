# This file handles in-memory data management for the API.
# In a real-world application, this data would be stored in a database (e.g., Firestore).

import uuid
import datetime

# In-memory storage for routes, favorites, and running sessions
# In a real application, you would use a database for persistent storage.
_STORE = {
    "routes": {},
    "favorites": {},
    "sessions": {},
    "selected_routes": {}
}

def store_routes(routes):
    """Stores the generated routes in memory and returns them with a unique ID."""
    route_ids = {}
    for route in routes:
        # Generate a unique ID for each route
        route_id = str(uuid.uuid4())
        _STORE["routes"][route_id] = route
        route_ids[route['type']] = route_id

    return route_ids

def get_route(route_id):
    """Retrieves a specific route by its ID."""
    return _STORE["routes"].get(route_id)

def add_favorite(route_id, name):
    """Adds a route to favorites."""
    route = get_route(route_id)
    if not route:
        return None

    favorite_id = str(uuid.uuid4())
    favorite_route = {
        "favorite_id": favorite_id,
        "route_id": route_id,
        "name": name,
        "distance_km": route['distance_km'],
        "category": route['type'],
        "safety_score": route['safety_score'],
        "estimated_time_min": route['estimated_time_min'],
        "pace_min_per_km": (route['estimated_time_min'] / route['distance_km']) if route['distance_km'] > 0 else 0
    }
    _STORE["favorites"][favorite_id] = favorite_route
    return favorite_route

def start_running_session(route_id, planned_pace_min_per_km):
    """Starts a new running session."""
    route = get_route(route_id)
    if not route:
        return None

    session_id = str(uuid.uuid4())
    session_data = {
        "session_id": session_id,
        "route_id": route_id,
        "status": "started",
        "planned_pace_min_per_km": planned_pace_min_per_km,
        "start_time": datetime.datetime.utcnow().isoformat() + 'Z',
        "current_location": route['waypoints'][0] # Start at the beginning
    }
    _STORE["sessions"][session_id] = session_data
    return session_data

def update_running_session(session_id, data):
    """Updates an existing running session."""
    session_data = _STORE["sessions"].get(session_id)
    if session_data:
        session_data.update(data)
    return session_data

def finish_running_session(session_id):
    """Finishes a running session and calculates final stats."""
    session_data = _STORE["sessions"].get(session_id)
    if not session_data:
        return None

    session_data["status"] = "finished"
    session_data["end_time"] = datetime.datetime.utcnow().isoformat() + 'Z'
    # In a real app, you would calculate total time, average pace, distance, etc.
    # For this simulation, we'll return a placeholder response.
    return {
        "session_id": session_id,
        "total_time_min": 40,
        "average_pace_min_per_km": 8.0,
        "actual_distance_km": 5.2,
        "safety_score": 88
    }

def select_route_for_crew(route_id, crew_post_id):
    """Selects a route for a crew post."""
    route = get_route(route_id)
    if not route:
        return None

    selected_id = str(uuid.uuid4())
    selected_route_data = {
        "selected_route_id": selected_id,
        "route_id": route_id,
        "crew_post_id": crew_post_id,
        "distance_km": route['distance_km'],
        "pace_min_per_km": (route['estimated_time_min'] / route['distance_km']) if route['distance_km'] > 0 else 0,
        "safety_score": route['safety_score']
    }
    _STORE["selected_routes"][selected_id] = selected_route_data
    return selected_route_data
