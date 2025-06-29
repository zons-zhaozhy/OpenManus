"""
API层 - 系统接口层

职责：
1. 定义REST API接口和路由
2. 处理HTTP请求和响应
3. 参数验证和错误处理
4. 调用modules层的服务实现业务逻辑

架构说明：
- API层位于系统的最外层，直接与客户端交互
- API层不包含复杂业务逻辑，主要负责请求处理和响应格式化
- 具体的业务逻辑实现在modules层中，API层通过调用modules层的服务来完成功能
- 这种分层设计有助于关注点分离，提高代码的可维护性和可测试性

例如：
- api/knowledge_base.py定义了知识库的API接口
- modules/knowledge_base/实现了知识库的核心功能
"""

from fastapi import APIRouter

from .architecture import architecture_router
from .requirements_modular import requirements_router

# 创建主路由器
router = APIRouter(prefix="/api", tags=["API"])

# 注册子路由
router.include_router(architecture_router)
router.include_router(requirements_router)

__all__ = [
    "router",
    "architecture_router",
    "requirements_router",
]
