from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.config import settings

app = FastAPI(
    title='行迹智能旅行路线 API',
    version='1.0.0',
    description=(
        '基于高德 POI/距离矩阵、地理聚类、最近邻与 2-opt 的旅行路线规划服务。'
        '所有高德 Web Service 调用仅发生在服务端。'
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ['http://localhost:5173'],
    allow_credentials=False,
    allow_methods=['GET', 'POST', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization', 'X-Request-ID'],
)
app.include_router(router)


@app.get('/', tags=['system'])
async def root() -> dict[str, str]:
    return {
        'name': settings.app_name,
        'docs': '/docs',
        'health': '/api/v1/health',
    }
