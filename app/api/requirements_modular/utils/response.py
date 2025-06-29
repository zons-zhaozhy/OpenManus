"""
响应工具
"""

from typing import Any, Dict, Optional, Union

from fastapi.responses import JSONResponse

from ..models import WorkflowResponse


def create_response(
    status: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    workflow_id: Optional[str] = None,
    status_code: int = 200,
) -> Union[Dict[str, Any], JSONResponse]:
    """创建标准响应"""
    response = WorkflowResponse(
        workflow_id=workflow_id or "",
        status=status,
        message=message,
        data=data,
        error=error,
    )
    
    if status_code != 200:
        return JSONResponse(
            status_code=status_code,
            content=response.dict(),
        )
    
    return response.dict()
