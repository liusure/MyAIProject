import uuid
from typing import Annotated

from fastapi import Depends, Request, Response


DEVICE_COOKIE_NAME = "device_id"
DEVICE_COOKIE_MAX_AGE = 365 * 24 * 3600  # 1 year


def get_or_create_device(request: Request, response: Response) -> str:
    """从 Cookie 获取 device_id，不存在则自动生成"""
    device_id = request.cookies.get(DEVICE_COOKIE_NAME)
    if not device_id:
        device_id = str(uuid.uuid4())
        response.set_cookie(
            key=DEVICE_COOKIE_NAME,
            value=device_id,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=DEVICE_COOKIE_MAX_AGE,
        )
    return device_id
