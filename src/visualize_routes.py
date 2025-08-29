import networkx as nx
import random
import folium

# --- 1. 2단계에서 생성한 최종 그래프 불러오기 ---
graph_filename = 'dalseo_real_graph.graphml'
try:
    G = nx.read_graphml(graph_filename)
    print(f"✅ '{graph_filename}' 그래프를 성공적으로 불러왔습니다.")
    # 노드 ID를 정수형으로 변환
    G = nx.relabel_nodes(G, {node: int(node) for node in G.nodes()})
except FileNotFoundError:
    print(f"오류: '{graph_filename}' 파일을 찾을 수 없습니다.")
    exit()

# --- 2. 3단계의 경로 탐색 함수들 (그대로 사용) ---

def find_shortest_path(graph, start_node, end_node):
    try:
        path = nx.dijkstra_path(graph, source=start_node, target=end_node, weight='length')
        return path
    except nx.NetworkXNoPath:
        return None

def find_safest_path(graph, start_node, end_node):
    try:
        path = nx.dijkstra_path(graph, source=start_node, target=end_node, weight='safety_cost')
        return path
    except nx.NetworkXNoPath:
        return None

def find_hybrid_path(graph, start_node, end_node):
    try:
        path = nx.dijkstra_path(graph, source=start_node, target=end_node, weight='hybrid_weight')
        return path
    except nx.NetworkXNoPath:
        return None

# --- 3. 경로 탐색 실행 ---

# 임의의 출발지/도착지 선택
node_list = list(G.nodes())
start_node = random.choice(node_list)
end_node = random.choice(node_list)

# 두 지점이 너무 가깝지 않도록 재선택
while start_node == end_node or nx.shortest_path_length(G, start_node, end_node) < 10:
    end_node = random.choice(node_list)

print("\n" + "="*50)
print(f"📍 출발지(Origin): {start_node}")
print(f"🏁 도착지(Destination): {end_node}")
print("="*50 + "\n")

# 3가지 경로 찾기
shortest_path = find_shortest_path(G, start_node, end_node)
safest_path = find_safest_path(G, start_node, end_node)
hybrid_path = find_hybrid_path(G, start_node, end_node)

# --- 4. Folium을 이용한 지도 시각화 ---

# 지도의 중심점을 출발지의 위도/경도로 설정
start_lat = G.nodes[start_node]['y']
start_lon = G.nodes[start_node]['x']
m = folium.Map(location=[start_lat, start_lon], zoom_start=14)

# 경로를 그리는 함수
def plot_path(graph, path, map_obj, color, weight, legend):
    if path:
        # 경로의 노드 ID 리스트로부터 (위도, 경도) 좌표 리스트를 생성
        path_coords = [(graph.nodes[node]['y'], graph.nodes[node]['x']) for node in path]
        # 지도에 PolyLine(선)으로 경로를 추가
        folium.PolyLine(
            locations=path_coords,
            color=color,
            weight=weight,
            opacity=0.8,
            tooltip=legend
        ).add_to(map_obj)
        print(f"✅ '{legend}' 경로를 지도에 그렸습니다.")
    else:
        print(f"❌ '{legend}' 경로를 찾지 못해 지도에 표시할 수 없습니다.")

# 3가지 경로를 각기 다른 색으로 그리기
plot_path(G, shortest_path, m, 'red', 5, '최단 경로')
plot_path(G, safest_path, m, 'blue', 5, '안전 경로')
plot_path(G, hybrid_path, m, 'green', 5, '하이브리드 경로')


# 출발지와 도착지에 마커 추가
folium.Marker(
    location=[G.nodes[start_node]['y'], G.nodes[start_node]['x']],
    popup='<strong>출발지</strong>',
    icon=folium.Icon(color='orange', icon='star')
).add_to(m)

folium.Marker(
    location=[G.nodes[end_node]['y'], G.nodes[end_node]['x']],
    popup='<strong>도착지</strong>',
    icon=folium.Icon(color='purple', icon='flag')
).add_to(m)

# --- 5. 결과 지도 파일 저장 ---
map_filename = 'dalseo_routes_map.html'
m.save(map_filename)

print("\n" + "="*50)
print(f"🎉 프로젝트 최종 완료! '{map_filename}' 파일을 확인하세요!")
print("   - 이 파일을 웹 브라우저로 열면 대화형 지도를 볼 수 있습니다.")
print("="*50)