# -*- coding: utf-8 -*-
"""
对象存储封装（MinIO / 任意 S3 兼容存储）。
- 原图与结果图都存 bucket
- 返回预签名 GET URL，直接下发给 APP 预览/保存
"""
import io
import uuid
import boto3
from botocore.config import Config as BotoConfig

from app.core.config import settings

_s3 = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
    config=BotoConfig(signature_version="s3v4"),
    region_name="us-east-1",
)


def ensure_bucket() -> None:
    buckets = [b["Name"] for b in _s3.list_buckets().get("Buckets", [])]
    if settings.s3_bucket not in buckets:
        _s3.create_bucket(Bucket=settings.s3_bucket)


def upload_image_bytes(data: bytes, kind: str, ext: str = "png") -> str:
    """上传图片字节流，返回对象 key。kind ∈ {input, result}"""
    ensure_bucket()
    key = f"{kind}/{uuid.uuid4().hex}.{ext.lstrip('.')}"
    _s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=io.BytesIO(data), ContentType=f"image/{ext.lstrip('.')}")
    return key


def presigned_url(key: str) -> str:
    return _s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=settings.presign_expire_seconds,
    )
