# -*- coding: utf-8 -*-
"""简单 Bearer Token 鉴权。"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

_bearer = HTTPBearer(auto_error=False)


def require_token(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    if credentials.credentials != settings.api_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid token")
    return credentials.credentials
