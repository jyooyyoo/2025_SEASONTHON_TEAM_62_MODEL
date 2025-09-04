import folium

def create_visualization(api_response, output_html_file):
    """
    Creates an HTML file with a Folium map to visualize the paths.
    """
    # Get center from the first waypoint of the first route
    if not api_response.get('routes'):
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

    # Add start marker
    start_point = first_route['waypoints'][0]

    folium.Marker(
        start_point,
        tooltip="출발/도착",
        icon=folium.Icon(color='red', icon='play', prefix='fa')
    ).add_to(m)

    m.save(output_html_file)
    print(f"HTML map saved to {output_html_file}")
