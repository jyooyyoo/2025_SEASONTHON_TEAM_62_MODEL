import flask
from flask import Flask, request, jsonify
import json
import os
import sys

application = Flask(__name__)


# Add the parent directory to the system path to allow imports from `src`
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from path_service import create_pathfinding_model, find_closest_node, find_paths_circular
from visualization import create_visualization
from run_manager import store_routes, add_favorite, start_running_session, update_running_session, finish_running_session, select_route_for_crew, get_route

app = Flask(__name__)

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_ROOT, 'data')
GRAPHML_FILE = os.path.join(DATA_PATH, 'dalseo_real_graph.graphml')
NODES_CSV_FILE = os.path.join(DATA_PATH, 'nodes_final_with_safety_score.csv')
HTML_OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'path_visualization.html')

# Global variable to store the graph model
G = None

def load_model():
    """Loads the graph model and safety data into memory."""
    global G
    try:
        G = create_pathfinding_model(GRAPHML_FILE, NODES_CSV_FILE)
        if G:
            print("Graph and safety data loaded successfully.")
    except Exception as e:
        print(f"Failed to load graph and safety data. Error: {e}")
        # Exit if the model cannot be loaded, as the app is unusable without it
        sys.exit(1)

# Load the model when the application starts
with app.app_context():
    load_model()

@app.route("/")
def index():
    return "API Server is running. Use /api/routes/recommend to get a route."

@app.route("/api/routes/recommend", methods=["POST"])
def recommend_routes():
    """
    1. 경로 추천 API
    사용자가 원하는 km 수와 페이스를 입력하면 3가지 경로를 추천.
    """
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON or empty body"}), 400

    start_point = data.get("start_point")
    distance_km = data.get("distance_km")
    pace_min_per_km = data.get("pace_min_per_km")

    if not all([start_point, distance_km, pace_min_per_km]):
        return jsonify({"error": "Missing required parameters: start_point, distance_km, pace_min_per_km"}), 400

    start_lat, start_lon = start_point
    start_node_id = find_closest_node(G, start_lat, start_lon)

    if not start_node_id:
        return jsonify({"error": "Could not find a valid start node near the provided coordinates."}), 400

    try:
        # Find paths and format them
        formatted_paths_data = find_paths_circular(G, start_node_id, distance_km)

        # Calculate estimated time and add to each route
        for route in formatted_paths_data["routes"]:
            estimated_time_min = round(route["distance_km"] * pace_min_per_km)
            route["estimated_time_min"] = estimated_time_min

        # Store the generated routes in memory
        route_ids = store_routes(formatted_paths_data['routes'])

        # Add the generated IDs to the response
        for route in formatted_paths_data['routes']:
            route['route_id'] = route_ids.get(route['type'])

        # Create HTML visualization for debugging
        create_visualization(formatted_paths_data, HTML_OUTPUT_FILE)

        return jsonify({"routes": formatted_paths_data['routes']}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

@app.route("/api/favorites", methods=["POST"])
def add_to_favorites():
    """
    2. 즐겨찾기 경로 API
    추천된 경로 중 하나를 즐겨찾기에 추가.
    """
    data = request.get_json()
    if not data or 'route_id' not in data or 'name' not in data:
        return jsonify({"error": "Missing required parameters: route_id, name"}), 400

    favorite = add_favorite(data['route_id'], data['name'])
    if not favorite:
        return jsonify({"error": "Invalid route_id"}), 404

    return jsonify(favorite), 200

@app.route("/api/runs/start", methods=["POST"])
def start_run():
    """
    3. 러닝 세션 API
    즐겨찾기나 추천 경로 기반으로 실제 러닝 시작.
    """
    data = request.get_json()
    if not data or 'route_id' not in data or 'planned_pace_min_per_km' not in data:
        return jsonify({"error": "Missing required parameters: route_id, planned_pace_min_per_km"}), 400

    session = start_running_session(data['route_id'], data['planned_pace_min_per_km'])
    if not session:
        return jsonify({"error": "Invalid route_id"}), 404

    return jsonify(session), 200

@app.route("/api/runs/<session_id>/update", methods=["PATCH"])
def update_run(session_id):
    """
    3. 러닝 세션 API (PATCH)
    실시간 위치, 실제 페이스, 진행률 업데이트
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing request body"}), 400

    updated_session = update_running_session(session_id, data)
    if not updated_session:
        return jsonify({"error": "Session not found"}), 404

    return jsonify(updated_session), 200

@app.route("/api/runs/<session_id>/finish", methods=["POST"])
def finish_run(session_id):
    """
    3. 러닝 세션 API (POST)
    종료 후 총 소요 시간, 평균 페이스, 실제 km, 안전 점수 등 반환
    """
    finished_session = finish_running_session(session_id)
    if not finished_session:
        return jsonify({"error": "Session not found"}), 404

    return jsonify(finished_session), 200

@app.route("/api/selected-route", methods=["POST"])
def select_route_for_crew():
    """
    4. 단일 루트 선택 API (크루 모집용)
    크루 모집 시 특정 루트를 단일 선택해 게시글에 연결.
    """
    data = request.get_json()
    if not data or 'route_id' not in data or 'crew_post_id' not in data:
        return jsonify({"error": "Missing required parameters: route_id, crew_post_id"}), 400

    selected_route = select_route_for_crew(data['route_id'], data['crew_post_id'])
    if not selected_route:
        return jsonify({"error": "Invalid route_id"}), 404

    return jsonify(selected_route), 200
