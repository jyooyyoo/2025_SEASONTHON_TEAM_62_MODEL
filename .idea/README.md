밤지기(Bamjigi) 경로 추천 모델 및 API 서버
이 프로젝트는 대구 달서구의 도로망 데이터를 기반으로, 사용자가 원하는 거리의 안전한 원형 달리기/산책 코스를 추천하는 백엔드 서버입니다.

주요 기능
원형 경로 추천: 출발지와 목표 거리를 입력하면 안전, 균형, 최단 거리 타입의 세 가지 원형 경로를 추천합니다.

RESTful API 제공: 프론트엔드(앱)와 통신할 수 있도록 경로 추천, 즐겨찾기, 러닝 세션 관리 API를 제공합니다.

파일 구성
dalseo_real_graph.graphml: 대구 달서구의 도로망, 안전 점수 등 모든 정보가 담긴 그래프 데이터 파일.

route_generator.py: 원형 경로를 계산하는 핵심 알고리즘이 포함된 파이썬 모듈.

api_server.py: Flask를 사용하여 API 엔드포인트를 구현한 웹 서버 파일.

실행 방법
1. 사전 준비
   프로젝트를 실행하기 위해서는 아래의 파이썬 라이브러리들이 필요합니다.

pip install networkx pandas numpy scipy flask

2. API 서버 실행
   터미널에서 아래 명령어를 입력하여 API 서버를 시작합니다.

python api_server.py

서버가 성공적으로 실행되면 다음과 같은 메시지가 나타납니다.

* Serving Flask app 'api_server'
* Debug mode: on
  WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
* Running on all addresses (0.0.0.0)
* Running on [http://127.0.0.1:5000](http://127.0.0.1:5000)
* Running on http://[YOUR_IP_ADDRESS]:5000
  Press CTRL+C to quit

3. API 테스트 (예시)
   서버가 실행 중인 상태에서, Postman 같은 API 테스트 도구를 사용하거나 curl 명령어로 요청을 보낼 수 있습니다.

경로 추천 요청 예시 (curl):

curl -X POST [http://127.0.0.1:5000/api/routes](http://127.0.0.1:5000/api/routes) \
-H "Content-Type: application/json" \
-d '{
"start": [35.8514, 128.5093],
"distance_km": 3.0
}'

위 요청을 보내면, 서버는 세 가지 타입의 추천 경로 정보를 JSON 형식으로 응답합니다.