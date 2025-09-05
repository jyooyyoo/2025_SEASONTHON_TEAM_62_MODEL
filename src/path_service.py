import pandas as pd
import networkx as nx
import os
import random
import math

# Define constants for pathfinding weights
SAFE_WEIGHT = 'safety_cost'
SHORTEST_WEIGHT = 'length'
BALANCED_WEIGHT = 'hybrid_weight'

# Load the graph and add safety scores
def create_pathfinding_model(graphml_file, nodes_csv_file):
    """
    Load graph and node data, and add safety scores to the graph.
    Returns a graph with safety scores as node attributes.
    """
    try:
        # Load the graph and node data
        G = nx.read_graphml(graphml_file)
        df_nodes = pd.read_csv(nodes_csv_file)

        # Normalize the safety score to a 100-point scale
        max_safety_score = df_nodes['safety_score'].max()
        if max_safety_score > 0:
            df_nodes['safety_score_100'] = (df_nodes['safety_score'] / max_safety_score) * 100
        else:
            df_nodes['safety_score_100'] = 0

        # Set 'osmid' as index for easy lookup
        df_nodes['osmid_str'] = df_nodes['osmid'].astype(str)
        df_nodes.set_index('osmid_str', inplace=True)

        # Add safety scores, coordinates, and other attributes to the graph nodes
        for node_id, data in G.nodes(data=True):
            if node_id in df_nodes.index:
                G.nodes[node_id]['safety_score'] = df_nodes.loc[node_id, 'safety_score_100']
                G.nodes[node_id]['lat'] = df_nodes.loc[node_id, 'y']
                G.nodes[node_id]['lon'] = df_nodes.loc[node_id, 'x']
            else:
                # Assign a default safety score for nodes not in the CSV
                G.nodes[node_id]['safety_score'] = 0
                G.nodes[node_id]['lat'] = None
                G.nodes[node_id]['lon'] = None

        # Add weights to edges
        for u, v, data in G.edges(data=True):
            v_safety_score = G.nodes[v]['safety_score']

            # --- WEIGHT CALCULATION ---
            # Safe Path Weight: A very aggressive penalty for lower scores
            # Using 1 / (score + small_epsilon) to heavily favor high-score nodes
            data['safe_only_weight'] = 1 / (v_safety_score + 1e-6)

            # Shortest Path Weight: Purely based on length
            data['shortest_only_weight'] = data.get('length', 1)

            # Balanced Path Weight:
            # 안전 점수(safe_only_weight)와 길이를 1:9 비율로 섞어 안전 점수가 낮도록 유도
            data[BALANCED_WEIGHT] = (data['safe_only_weight'] * 0.1) + (data['shortest_only_weight'] * 0.9)

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        return None
    except Exception as e:
        print(f"An error occurred during model setup: {e}")
        return None

    return G

def find_closest_node(G, lat, lon):
    """
    Finds the node in the graph closest to the given coordinates.
    """
    closest_node = None
    min_dist = float('inf')

    for node_id, data in G.nodes(data=True):
        if 'lat' in data and 'lon' in data:
            dist = math.sqrt((data['lat'] - lat)**2 + (data['lon'] - lon)**2)
            if dist < min_dist:
                min_dist = dist
                closest_node = node_id
    return closest_node

def find_paths_circular(G, start_node_id, desired_distance_km):
    """
    Finds three distinct circular paths (safe, shortest, balanced) of a given distance.
    Returns a dictionary with formatted path data.
    """
    if start_node_id not in G:
        raise ValueError("Start node not found in the graph.")

    desired_distance_m = desired_distance_km * 1000

    # Define weight functions for A* algorithm
    def safe_weight(u, v, data):
        return data.get('safe_only_weight', float('inf'))

    def shortest_weight(u, v, data):
        return data.get('shortest_only_weight', float('inf'))

    def balanced_weight(u, v, data):
        return data.get(BALANCED_WEIGHT, float('inf'))

    weights = {
        'safe': safe_weight,
        'shortest': shortest_weight,
        'balanced': balanced_weight
    }

    found_paths = {}
    path_types = ['safe', 'shortest', 'balanced']

    # Keep track of found paths to ensure they are unique
    unique_paths = set()

    # Find three paths
    for path_type in path_types:
        path = None
        attempts = 0
        while path is None and attempts < 10:
            # Find a random intermediate node to form a circular path
            candidate_nodes = list(G.nodes)
            random.shuffle(candidate_nodes)

            for intermediate_node in candidate_nodes:
                if intermediate_node == start_node_id:
                    continue

                try:
                    # Find path from start to intermediate
                    path1 = nx.astar_path(G, source=start_node_id, target=intermediate_node, weight=weights[path_type])

                    # Find path from intermediate back to start
                    path2 = nx.astar_path(G, source=intermediate_node, target=start_node_id, weight=weights[path_type])

                    full_path = path1 + path2[1:]

                    # Check if the path is a duplicate
                    if tuple(full_path) in unique_paths:
                        continue

                    # Calculate total path length
                    path_length_m = sum(G.get_edge_data(u, v)['length'] for u, v in zip(full_path[:-1], full_path[1:]))

                    # Check if the distance is within an acceptable range (e.g., +/- 15%)
                    if desired_distance_m * 0.85 <= path_length_m <= desired_distance_m * 1.15:
                        path = full_path
                        break

                except nx.NetworkXNoPath:
                    continue

            attempts += 1
            if path:
                unique_paths.add(tuple(path))
                found_paths[path_type] = path
                break

    return format_route_data(G, found_paths)

def format_route_data(G, paths):
    """
    Formats the found paths into a list of dictionaries suitable for the API response.
    """
    routes = []

    for path_type, path in paths.items():
        if path:
            distance_m = sum(G.get_edge_data(u, v)['length'] for u, v in zip(path[:-1], path[1:]))
            distance_km = round(distance_m / 1000, 2)

            # Calculate average safety score for the path
            safety_scores = [G.nodes[node]['safety_score'] for node in path if 'safety_score' in G.nodes[node]]
            avg_safety_score = round(sum(safety_scores) / len(safety_scores), 2) if safety_scores else 0

            # Extract waypoints
            waypoints = []
            for node_id in path:
                node_data = G.nodes[node_id]
                waypoints.append([node_data['lat'], node_data['lon']])

            routes.append({
                "type": path_type,
                "distance_km": distance_km,
                "safety_score": avg_safety_score,
                "estimated_time_min": 0, # To be calculated in app.py
                "waypoints": waypoints
            })

    return {"routes": routes}
