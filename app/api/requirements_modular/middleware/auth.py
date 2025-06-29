"""
认证中间件
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[str]:
    """获取当前用户"""
    if token is None:
        return None

    # TODO: 实现真实的用户认证
    # 目前直接返回 token 作为用户标识
    return token
