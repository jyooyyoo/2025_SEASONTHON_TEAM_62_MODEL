import networkx as nx
import random
import folium
import pandas as pd
import numpy as np

# --- 1. 최종 그래프 불러오기 ---
graph_filename = 'dalseo_real_graph.graphml'
try:
    G = nx.read_graphml(graph_filename)
    print(f"✅ '{graph_filename}' 그래프를 성공적으로 불러왔습니다.")
    G = nx.relabel_nodes(G, {node: int(node) for node in G.nodes()})
except FileNotFoundError:
    print(f"오류: '{graph_filename}' 파일을 찾을 수 없습니다.")
    exit()

# --- 2. 안전 등급 산출을 위한 기준 설정 ---
all_safety_scores = pd.Series([data['safety_score'] for node, data in G.nodes(data=True) if 'safety_score' in data])

# 안전 등급을 나눌 구간(bin)과 라벨 정의
grade_labels = ['5등급', '4등급', '3등급', '2등급', '1등급']
bin_edges = None

try:
    # pd.qcut을 사용하여 데이터를 5개의 동일한 개수로 나눔
    score_bins, bin_edges = pd.qcut(all_safety_scores, 5, labels=grade_labels, retbins=True, duplicates='drop')
    print("✅ 안전 등급(1~5) 산출 기준을 설정했습니다.")
except ValueError:
    print("⚠️ 노드 데이터의 분포가 균일하지 않아 5개 등급으로 나눌 수 없습니다. 등급 없이 진행합니다.")

def get_path_grade(graph, path):
    """경로의 평균 안전 점수로 등급을 반환합니다."""
    if not path or bin_edges is None:
        return ""

    path_scores = [graph.nodes[node]['safety_score'] for node in path if 'safety_score' in graph.nodes[node]]
    if not path_scores:
        return ""

    avg_score = np.mean(path_scores)

    # np.digitize는 avg_score가 bin_edges의 어느 구간에 속하는지 인덱스를 찾아줌
    # 인덱스는 1부터 시작하므로 1을 빼서 0부터 시작하게 만듦
    grade_index = np.digitize(avg_score, bins=bin_edges) - 1

    # 인덱스가 유효한 범위 내에 있는지 확인
    if 0 <= grade_index < len(grade_labels):
        # 점수가 높을수록 좋은 등급(1등급)이므로, 라벨 순서를 뒤집어서 선택
        return f"(안전 {grade_labels[::-1][grade_index]})"
    return ""

# --- 3. 경로 탐색 함수들 ---
def find_path(graph, start, end, weight):
    try:
        path = nx.dijkstra_path(graph, source=start, target=end, weight=weight)
        return path
    except nx.NetworkXNoPath:
        return None

# --- 4. 경로 탐색 실행 ---
node_list = list(G.nodes())
start_node = random.choice(node_list)
end_node = random.choice(node_list)

# 출발지와 도착지가 같거나 너무 가까우면 다시 선택
while start_node == end_node or not nx.has_path(G, start_node, end_node) or nx.shortest_path_length(G, start_node, end_node) < 15:
    start_node = random.choice(node_list)
    end_node = random.choice(node_list)

print("\n" + "="*50)
print(f"📍 출발지: {start_node}")
print(f"🏁 도착지: {end_node}")
print("="*50 + "\n")

shortest_path = find_path(G, start_node, end_node, 'length')
safest_path = find_path(G, start_node, end_node, 'safety_cost')
hybrid_path = find_path(G, start_node, end_node, 'hybrid_weight')

# 최단 경로와 안전 경로가 일치하는지 확인
if shortest_path and safest_path and shortest_path == safest_path:
    print("✨ 정보: 최단 경로와 안전 경로가 동일합니다!")
    safest_path = None # 동일하면 안전 경로는 따로 그리지 않음

# --- 5. Folium을 이용한 지도 시각화 ---
start_lat, start_lon = G.nodes[start_node]['y'], G.nodes[start_node]['x']
m = folium.Map(location=[start_lat, start_lon], zoom_start=14)

def plot_path(graph, path, map_obj, color, weight, legend, offset=0):
    if not path:
        print(f"❌ '{legend}' 경로를 찾지 못했습니다.")
        return

    path_grade = get_path_grade(graph, path)
    full_legend = f"{legend} {path_grade}"

    path_coords = [(graph.nodes[node]['y'], graph.nodes[node]['x']) for node in path]

    # offset 옵션으로 경로를 시각적으로 분리
    folium.PolyLine(
        locations=path_coords, color=color, weight=weight,
        opacity=0.9, tooltip=full_legend, offset=offset
    ).add_to(map_obj)
    print(f"✅ '{full_legend}' 경로를 지도에 그렸습니다.")

# 경로 그리기
if safest_path is None: # 두 경로가 일치할 경우
    plot_path(G, shortest_path, m, 'purple', 7, '최단/안전 경로 (일치)')
else:
    plot_path(G, safest_path, m, 'blue', 5, '안전 경로')
    plot_path(G, shortest_path, m, 'red', 5, '최단 경로', offset=5)

plot_path(G, hybrid_path, m, 'green', 5, '중간 경로', offset=-5)

# 마커 추가
folium.Marker(location=[start_lat, start_lon], popup='<strong>출발지</strong>', icon=folium.Icon(color='orange', icon='star')).add_to(m)
folium.Marker(location=[G.nodes[end_node]['x'], G.nodes[end_node]['y']], popup='<strong>도착지</strong>', icon=folium.Icon(color='purple', icon='flag')).add_to(m)


# --- 6. 결과 지도 파일 저장 ---
map_filename = 'dalseo_routes_map_v2.html'
m.save(map_filename)

print("\n" + "="*50)
print(f"🎉 프로젝트 최종 완료! '{map_filename}' 파일을 확인하세요!")
print("="*50)