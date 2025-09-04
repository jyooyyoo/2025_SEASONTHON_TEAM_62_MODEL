import json
from flask import Flask, request, jsonify
from path_service import create_pathfinding_model, find_paths_circular, find_closest_node
from run_manager import add_favorite_route, start_running_session, update_running_session, finish_running_session
from visualization import create_visualization

app = Flask(__name__)

# Load the graph model once when the application starts
GRAPHML_FILE = 'dalseo_real_graph.graphml'
NODES_CSV_FILE = 'nodes_final_with_safety_score.csv'
G_with_scores = create_pathfinding_model(GRAPHML_FILE, NODES_CSV_FILE)

# --- 1. 경로 추천 API ---
@app.route('/api/routes/recommend', methods=['POST'])
def recommend_routes():
    data = request.get_json()
    start_point = data.get('start_point')
    distance_km = data.get('distance_km')
    pace_min_per_km = data.get('pace_min_per_km')

    if not all([start_point, distance_km, pace_min_per_km]):
        return jsonify({"error": "Missing required parameters"}), 400

    start_node = find_closest_node(G_with_scores, start_point[0], start_point[1])
    if not start_node:
        return jsonify({"error": "Start point is not on a known road"}), 404

    try:
        path_results = find_paths_circular(G_with_scores, start_node, distance_km)

        # Calculate estimated time based on pace
        for route in path_results['routes']:
            route['estimated_time_min'] = round(route['distance_km'] * pace_min_per_km, 2)

        return jsonify(path_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 2. 즐겨찾기 경로 API ---
@app.route('/api/favorites', methods=['POST'])
def add_favorite():
    data = request.get_json()
    route_id = data.get('route_id')
    name = data.get('name')

    if not all([route_id, name]):
        return jsonify({"error": "Missing required parameters"}), 400

    # In a real app, you would fetch route details from a database
    # Here, we'll use a dummy route for demonstration
    dummy_route_info = {
        "route_id": route_id,
        "distance_km": 5.0,
        "category": "safe",
        "safety_score": 92,
        "estimated_time_min": 30,
        "pace_min_per_km": 6
    }

    try:
        favorite_info = add_favorite_route(dummy_route_info, name)
        return jsonify(favorite_info), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 3. 러닝 세션 API ---
@app.route('/api/runs/start', methods=['POST'])
def start_run():
    data = request.get_json()
    route_id = data.get('route_id')
    planned_pace_min_per_km = data.get('planned_pace_min_per_km')

    if not all([route_id, planned_pace_min_per_km]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        session_info = start_running_session(route_id, planned_pace_min_per_km)
        return jsonify(session_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/runs/<session_id>/update', methods=['PATCH'])
def update_run(session_id):
    # This endpoint is for real-time updates.
    # In a full app, it would update live location, pace, etc.
    data = request.get_json()
    try:
        # Dummy response for demonstration
        status_info = update_running_session(session_id, data)
        return jsonify(status_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/runs/<session_id>/finish', methods=['POST'])
def finish_run(session_id):
    try:
        # Dummy response for demonstration
        result_info = finish_running_session(session_id)
        return jsonify(result_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 4. 단일 루트 선택 API (크루 모집용) ---
@app.route('/api/selected-route', methods=['POST'])
def select_route():
    data = request.get_json()
    route_id = data.get('route_id')
    crew_post_id = data.get('crew_post_id')

    if not all([route_id, crew_post_id]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        # Dummy route info for demonstration
        dummy_route_info = {
            "route_id": route_id,
            "crew_post_id": crew_post_id,
            "distance_km": 5.0,
            "pace_min_per_km": 6,
            "safety_score": 92
        }
        return jsonify(dummy_route_info), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
