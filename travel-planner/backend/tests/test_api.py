from fastapi.testclient import TestClient

from app.main import app


def test_plan_endpoint_accepts_camel_case_and_returns_contract():
    with TestClient(app) as client:
        response = client.post('/api/v1/plans', json={
            'destination': '杭州',
            'duration': {'value': 1, 'unit': 'days'},
            'preferences': ['natural', 'museum'],
            'transportMode': 'walking',
            'dailyHours': 8,
            'groupSize': {'adults': 2, 'children': 0},
        })
    assert response.status_code == 200
    body = response.json()
    assert body['totalDays'] == 1
    assert body['overallStats']['backtrackCheck'] == 'passed'
    assert all('arrivalTime' in spot for spot in body['routes'][0]['spots'])
