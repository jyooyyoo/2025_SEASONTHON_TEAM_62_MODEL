import networkx as nx
import random

# --- 1. 2단계에서 생성한 최종 그래프 불러오기 ---
graph_filename = 'dalseo_real_graph.graphml'
try:
    G = nx.read_graphml(graph_filename)
    print(f"✅ '{graph_filename}' 그래프를 성공적으로 불러왔습니다.")
    # 노드 ID를 정수형으로 변환 (파일에서 문자열로 읽어올 수 있기 때문)
    G = nx.relabel_nodes(G, {node: int(node) for node in G.nodes()})
    print(f"   - 총 노드 수: {len(G.nodes())}")
    print(f"   - 총 엣지 수: {len(G.edges())}")
except FileNotFoundError:
    print(f"오류: '{graph_filename}' 파일을 찾을 수 없습니다.")
    print("2단계 코드를 먼저 실행하여 그래프 파일을 생성해주세요.")
    exit()

# --- 2. 경로 탐색 함수 정의 ---

# 함수 1: A* 알고리즘을 이용한 최단 경로 탐색
def find_shortest_path(graph, start_node, end_node):
    """실제 거리(length)가 가장 짧은 경로를 찾습니다."""
    try:
        # A* 알고리즘은 목표점까지의 추정 거리를 사용하는 휴리스틱 함수가 필요하지만,
        # networkx에서는 단순 최단 경로 탐색 시 dijkstra_path를 주로 사용합니다.
        # A*의 효과를 보려면 위도/경도 기반의 휴리스틱 함수를 직접 정의해야 합니다.
        # 여기서는 dijkstra를 사용해 'length' 가중치 기반의 최단 경로를 찾겠습니다.
        path = nx.dijkstra_path(graph, source=start_node, target=end_node, weight='length')
        total_length = nx.dijkstra_path_length(graph, source=start_node, target=end_node, weight='length')
        return path, total_length
    except nx.NetworkXNoPath:
        return None, float('inf')

# 함수 2: 가장 안전한 경로 탐색
def find_safest_path(graph, start_node, end_node):
    """안전 비용(safety_cost)이 가장 낮은 경로를 찾습니다."""
    try:
        path = nx.dijkstra_path(graph, source=start_node, target=end_node, weight='safety_cost')
        total_safety_cost = nx.dijkstra_path_length(graph, source=start_node, target=end_node, weight='safety_cost')
        return path, total_safety_cost
    except nx.NetworkXNoPath:
        return None, float('inf')

# 함수 3: 하이브리드 경로 탐색
def find_hybrid_path(graph, start_node, end_node):
    """거리와 안전을 모두 고려한 복합 가중치(hybrid_weight)가 가장 낮은 경로를 찾습니다."""
    try:
        path = nx.dijkstra_path(graph, source=start_node, target=end_node, weight='hybrid_weight')
        total_hybrid_weight = nx.dijkstra_path_length(graph, source=start_node, target=end_node, weight='hybrid_weight')
        return path, total_hybrid_weight
    except nx.NetworkXNoPath:
        return None, float('inf')

# --- 3. 실제 경로 탐색 실행 예시 ---

# 그래프에 있는 실제 노드 중에서 임의의 출발지/도착지 선택
node_list = list(G.nodes())
start_point = random.choice(node_list)
end_point = random.choice(node_list)

# 두 지점이 너무 가깝지 않도록 다시 선택
while start_point == end_point or nx.shortest_path_length(G, start_point, end_point) < 10:
    end_point = random.choice(node_list)

print("\n" + "="*50)
print(f"📍 출발지(Origin): {start_point}")
print(f"🏁 도착지(Destination): {end_point}")
print("="*50 + "\n")


# 1) 최단 경로 탐색
shortest_p, shortest_dist = find_shortest_path(G, start_point, end_point)
if shortest_p:
    print(f"🚗 최단 경로 (A* 알고리즘 활용):")
    print(f"  - 총 거리: {shortest_dist:.2f} 미터")
    # print(f"  - 경로 노드: {shortest_p}") # 경로가 너무 길어 주석 처리
else:
    print("🚗 최단 경로를 찾을 수 없습니다.")

print("\n" + "-"*50 + "\n")

# 2) 가장 안전한 경로 탐색
safest_p, safest_cost = find_safest_path(G, start_point, end_point)
if safest_p:
    print(f"🛡️ 가장 안전한 경로:")
    print(f"  - 총 안전 비용: {safest_cost:.2f} (낮을수록 안전)")
    # print(f"  - 경로 노드: {safest_p}")
else:
    print("🛡️ 가장 안전한 경로를 찾을 수 없습니다.")

print("\n" + "-"*50 + "\n")

# 3) 하이브리드 경로 탐색
hybrid_p, hybrid_weight = find_hybrid_path(G, start_point, end_point)
if hybrid_p:
    print(f"⚖️ 하이브리드 경로 (거리와 안전 균형):")
    print(f"  - 총 복합 가중치: {hybrid_weight:.4f} (낮을수록 좋음)")
    # print(f"  - 경로 노드: {hybrid_p}")
else:
    print("⚖️ 하이브리드 경로를 찾을 수 없습니다.")