import folium
import json

def create_visualization(api_response, output_html_file):
    """
    Creates an HTML file with a Folium map to visualize the paths based on API response data.
    """
    if not api_response.get('routes'):
        print("시각화할 경로가 없습니다.")
        return

    # Set map center based on the starting point of the first route
    first_route = api_response['routes'][0]
    start_point = first_route['waypoints'][0]

    # Create a Folium map with a darker base map for better visibility
    m = folium.Map(location=start_point, zoom_start=13, tiles="CartoDB dark_matter")

    colors = {
        'safe': 'green',
        'shortest': 'yellow',
        'balanced': 'orange'
    }

    # Plot each path with a tooltip
    for route in api_response['routes']:
        path_type = route['type']
        waypoints = route['waypoints']
        distance = route['distance_km']
        safety_score = route['safety_score']
        estimated_time = route['estimated_time_min']
        pace = route['pace_min_per_km']

        tooltip_html = f"""
        <b>경로 종류: {path_type.capitalize()}</b><br>
        거리: {distance} km<br>
        안전 점수: {safety_score}점<br>
        예상 시간: {estimated_time} 분<br>
        페이스: {pace} 분/km
        """

        folium.PolyLine(
            waypoints,
            color=colors.get(path_type, 'gray'),
            weight=6,
            opacity=0.8,
            tooltip=tooltip_html,
        ).add_to(m)

    # Add a marker for the start/end point
    folium.Marker(
        start_point,
        tooltip="출발/도착 지점",
        icon=folium.Icon(color='red', icon='play', prefix='fa')
    ).add_to(m)

    m.save(output_html_file)
    print(f"HTML 지도 파일 '{output_html_file}'이(가) 성공적으로 생성되었습니다.")
