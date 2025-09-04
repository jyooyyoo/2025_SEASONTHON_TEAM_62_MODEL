import pandas as pd
import networkx as nx
import json
import math
import random
import folium

def create_pathfinding_model(graphml_file, nodes_csv_file):
    """
    Load graph and node data, and add safety scores to the graph.
    Returns a graph with safety scores and length as node and edge attributes.
    """
    try:
        G = nx.read_graphml(graphml_file)
        # GraphML 파일을 불러올 때 'multigraph' 속성을 확인하여, 다중 그래프가 아니면 엣지 접근 방식을 변경합니다.
        is_multigraph = G.is_multigraph()

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

        # Add safety scores and coordinates to the graph nodes
        for node in G.nodes():
            if node in df_nodes.index:
                G.nodes[node]['safety_score'] = df_nodes.loc[node, 'safety_score_100']
                G.nodes[node]['lat'] = df_nodes.loc[node, 'y']
                G.nodes[node]['lon'] = df_nodes.loc[node, 'x']
            else:
                G.nodes[node]['safety_score'] = 0
                G.nodes[node]['lat'] = None
                G.nodes[node]['lon'] = None

        # Add 'length' attribute to edges if not present (assuming it's in meters)
        for u, v, data in G.edges(data=True):
            if 'length' not in data:
                data['length'] = 1 # Default length if not available

        G.is_multigraph = lambda: is_multigraph

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        return None
    except Exception as e:
        print(f"An error occurred during model setup: {e}")
        return None

    return G

def find_closest_node(G, lat, lon):
    """
    Find the closest node in the graph to the given latitude and longitude.
    """
    nodes = nx.get_node_attributes(G, 'lat')
    min_dist = float('inf')
    closest_node = None
    for node_id, node_lat in nodes.items():
        node_lon = G.nodes[node_id]['lon']
        if node_lat is not None and node_lon is not None:
            dist = math.sqrt((node_lat - lat)**2 + (node_lon - lon)**2)
            if dist < min_dist:
                min_dist = dist
                closest_node = node_id
    return closest_node

def find_paths_circular(G, start_node, desired_distance_km, max_attempts=1000):
    """
    Find three distinct circular paths (safe, shortest, balanced) of a specific length.
    """
    if start_node not in G:
        print("Error: Start node not in graph.")
        return {}

    paths = {}

    target_path_length_m = desired_distance_km * 1000

    found_paths = {
        'safe': None,
        'shortest': None,
        'balanced': None
    }

    def get_edge_data(u, v):
        if G.is_multigraph():
            return G.get_edge_data(u, v)[0]
        else:
            return G.get_edge_data(u, v)

    # Try to find a path within a certain distance tolerance
    for attempt in range(max_attempts):
        end_node = random.choice(list(G.nodes()))

        # Safe Path
        if not found_paths['safe']:
            for u, v in G.edges():
                edge_data = get_edge_data(u, v)
                edge_data['safe_cost'] = 101 - G.nodes[v]['safety_score']
            try:
                path = nx.shortest_path(G, source=start_node, target=end_node, weight='safe_cost')
                path_length_m = sum(get_edge_data(u, v)['length'] for u, v in zip(path[:-1], path[1:]))
                if abs(path_length_m - target_path_length_m) < target_path_length_m * 0.2:
                    found_paths['safe'] = path + path[::-1][1:] # Make it circular
            except nx.NetworkXNoPath:
                pass

        # Shortest Path
        if not found_paths['shortest']:
            try:
                path = nx.shortest_path(G, source=start_node, target=end_node, weight='length')
                path_length_m = sum(get_edge_data(u, v)['length'] for u, v in zip(path[:-1], path[1:]))
                if abs(path_length_m - target_path_length_m) < target_path_length_m * 0.2:
                    circular_path = path + path[::-1][1:]
                    if not found_paths['safe'] or circular_path != found_paths['safe']:
                        found_paths['shortest'] = circular_path
            except nx.NetworkXNoPath:
                pass

        # Balanced Path
        if not found_paths['balanced']:
            for u, v in G.edges():
                edge_data = get_edge_data(u, v)
                safe_cost = 101 - G.nodes[v]['safety_score']
                shortest_cost = edge_data.get('length', 1)
                edge_data['balanced_cost'] = 0.5 * safe_cost + 0.5 * shortest_cost
            try:
                path = nx.shortest_path(G, source=start_node, target=end_node, weight='balanced_cost')
                path_length_m = sum(get_edge_data(u, v)['length'] for u, v in zip(path[:-1], path[1:]))
                if abs(path_length_m - target_path_length_m) < target_path_length_m * 0.2:
                    circular_path = path + path[::-1][1:]
                    if (not found_paths['safe'] or circular_path != found_paths['safe']) and \
                            (not found_paths['shortest'] or circular_path != found_paths['shortest']):
                        found_paths['balanced'] = circular_path
            except nx.NetworkXNoPath:
                pass

        if all(found_paths.values()):
            break

    # Format the found paths for the API response
    api_response = {"routes": []}
    for path_type, path in found_paths.items():
        if path:
            distance_m = sum(get_edge_data(u, v)['length'] for u, v in zip(path[:-1], path[1:]))
            avg_safety_score = sum(G.nodes[node]['safety_score'] for node in path) / len(path)

            # Calculate estimated time based on pace
            estimated_time_min = (distance_m / 1000) * 6

            waypoints = [[G.nodes[node]['lat'], G.nodes[node]['lon']] for node in path]

            api_response['routes'].append({
                "type": path_type,
                "distance_km": round(distance_m / 1000, 2),
                "safety_score": round(avg_safety_score, 2),
                "estimated_time_min": round(estimated_time_min, 2),
                "waypoints": waypoints
            })

    return api_response

def create_visualization(api_response, output_html_file):
    """
    Creates an HTML file with a Folium map to visualize the paths.
    """
    # Get center from the first waypoint of the first route
    if not api_response['routes']:
        print("No routes to visualize.")
        return

    first_route = api_response['routes'][0]
    start_lat, start_lon = first_route['waypoints'][0]

    m = folium.Map(location=[start_lat, start_lon], zoom_start=13)

    colors = {
        'safe': 'green',
        'shortest': 'blue',
        'balanced': 'orange'
    }

    # Plot each path
    for route in api_response['routes']:
        path_type = route['type']
        waypoints = route['waypoints']

        folium.PolyLine(
            waypoints,
            color=colors.get(path_type, 'gray'),
            weight=5,
            opacity=0.8,
            tooltip=f"{path_type.capitalize()} 경로"
        ).add_to(m)

    # Add start and end markers
    start_point = first_route['waypoints'][0]

    folium.Marker(
        start_point,
        tooltip="출발/도착",
        icon=folium.Icon(color='red', icon='play', prefix='fa')
    ).add_to(m)

    m.save(output_html_file)
    print(f"HTML map saved to {output_html_file}")

# --- Main execution block for API endpoint simulation and visualization ---
if __name__ == "__main__":
    GRAPHML_FILE = 'dalseo_real_graph.graphml'
    NODES_CSV_FILE = 'nodes_final_with_safety_score.csv'

    # Load the graph with safety scores
    G_with_scores = create_pathfinding_model(GRAPHML_FILE, NODES_CSV_FILE)

    if G_with_scores:
        # Choose a random start node in Dalseo-gu for demonstration
        # A good demonstration node is one that has multiple paths branching out
        start_node_id = '365208094' # This node is in Dalseo-gu

        desired_distance_km = 5

        # Find the three paths
        print(f"달서구 내에서 {desired_distance_km}km 거리의 경로를 찾고 있습니다...")
        path_results = find_paths_circular(G_with_scores, start_node_id, desired_distance_km)

        # Print the final API response
        print("\nAPI Response Simulation (JSON):")
        print(json.dumps(path_results, indent=2, ensure_ascii=False))

        # Generate and save the HTML file
        create_visualization(path_results, "path_visualization.html")
