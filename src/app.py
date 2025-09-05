import pandas as pd
import networkx as nx
from flask import Flask, request, jsonify
from path_service import create_pathfinding_model, find_closest_node, find_paths_circular
from visualization import create_visualization
import os
import json

app = Flask(__name__)

# Load the graph and safety score data once when the server starts
DATA_DIR = 'data'
GRAPHML_FILE = os.path.join(DATA_DIR, 'dalseo_real_graph.graphml')
NODES_CSV_FILE = os.path.join(DATA_DIR, 'nodes_final_with_safety_score.csv')

G_with_scores = create_pathfinding_model(GRAPHML_FILE, NODES_CSV_FILE)

if G_with_scores:
    print("Graph and safety data loaded successfully.")
else:
    print("Failed to load graph and safety data. Exiting.")
    exit()

@app.route('/api/routes/recommend', methods=['POST'])
def recommend_routes():
    """
    API endpoint to recommend three circular paths based on user input.
    """
    data = request.get_json(silent=True)

    if not data or not isinstance(data, dict):
        return jsonify({"error": "Request body must be a valid JSON object"}), 400

    start_point = data.get('start_point')
    distance_km = data.get('distance_km')
    pace_min_per_km = data.get('pace_min_per_km')

    if not all([start_point, distance_km, pace_min_per_km]):
        return jsonify({"error": "Missing required parameters"}), 400

    start_lat, start_lon = start_point
    start_node_id = find_closest_node(G_with_scores, start_lat, start_lon)

    if not start_node_id:
        return jsonify({"error": "Could not find a starting node close to the provided coordinates"}), 404

    try:
        paths_data = find_paths_circular(G_with_scores, start_node_id, distance_km)

        # Calculate estimated time and pace for each route
        for route in paths_data.get("routes", []):
            route_distance = route['distance_km']
            estimated_time_min = round(route_distance * pace_min_per_km, 2)
            route['estimated_time_min'] = estimated_time_min
            route['pace_min_per_km'] = pace_min_per_km

        # Generate HTML visualization file
        output_html_file = 'path_visualization.html'
        create_visualization(paths_data, output_html_file)

        return jsonify(paths_data), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except nx.NetworkXNoPath:
        return jsonify({"error": "No path could be found with the given criteria."}), 404
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

if __name__ == '__main__':
    # Make sure data directory exists
    if not os.path.exists('data'):
        print("Error: 'data' directory not found. Please create it and place your data files inside.")
        exit()

    app.run(debug=True)
