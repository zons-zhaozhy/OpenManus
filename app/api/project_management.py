"""
项目管理API

提供完整的项目制管理功能：
1. 项目生命周期管理
2. 代码库与项目的一对一绑定
3. 知识库的多项目挂载
4. 项目上下文管理
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.logger import logger
from app.schema import (
    KnowledgeBase,
    KnowledgeBaseType,
    Project,
    ProjectCodebase,
    ProjectContext,
    ProjectKnowledgeMount,
    ProjectSession,
    ProjectStage,
    ProjectStatus,
    ProjectType,
)

# 项目管理路由器
project_router = APIRouter(prefix="/api/projects", tags=["Project Management"])

# 内存存储（生产环境建议使用数据库）
projects_store: Dict[str, Project] = {}
codebases_store: Dict[str, ProjectCodebase] = {}
knowledge_bases_store: Dict[str, KnowledgeBase] = {}
knowledge_mounts_store: Dict[str, ProjectKnowledgeMount] = {}
project_contexts_store: Dict[str, ProjectContext] = {}
project_sessions_store: Dict[str, ProjectSession] = {}


# API 请求模型
class CreateProjectRequest(BaseModel):
    name: str
    description: str
    objective: str
    background: str
    project_type: ProjectType
    success_criteria: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    priority: int = 3
    stakeholders: Optional[List[str]] = None


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    objective: Optional[str] = None
    background: Optional[str] = None
    status: Optional[ProjectStatus] = None
    current_stage: Optional[ProjectStage] = None
    priority: Optional[int] = None
    success_criteria: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    stakeholders: Optional[List[str]] = None


class CreateCodebaseRequest(BaseModel):
    name: str
    description: str
    local_path: str
    main_language: str
    framework: Optional[str] = None
    dependencies: Optional[List[str]] = None
    repository_url: Optional[str] = None


class CreateKnowledgeBaseRequest(BaseModel):
    name: str
    description: str
    kb_type: KnowledgeBaseType
    content: Optional[Dict] = None
    patterns: Optional[List[Dict]] = None
    templates: Optional[List[Dict]] = None


class MountKnowledgeBaseRequest(BaseModel):
    knowledge_base_id: str
    mount_type: str = "read_only"
    priority: int = 3


# 项目管理端点
@project_router.post("/", response_model=Project)
async def create_project(request: CreateProjectRequest) -> Project:
    """创建新项目"""
    try:
        project_id = str(uuid.uuid4())

        project = Project(
            id=project_id,
            name=request.name,
            description=request.description,
            objective=request.objective,
            background=request.background,
            type=request.project_type,
            success_criteria=request.success_criteria or [],
            constraints=request.constraints or [],
            priority=request.priority,
            stakeholders=request.stakeholders or [],
        )

        projects_store[project_id] = project

        # 创建项目上下文
        project_context = ProjectContext(
            project_id=project_id,
            objective_guidance=request.objective,
            background_context=request.background,
            success_criteria=request.success_criteria or [],
            constraints=request.constraints or [],
            current_stage="initialization",
            stage_objectives=["项目初始化", "资源配置", "团队组建"],
        )

        project_contexts_store[project_id] = project_context

        logger.info(f"创建项目成功: {project.name} ({project_id})")
        return project

    except Exception as e:
        logger.error(f"创建项目失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")


@project_router.get("/", response_model=List[Project])
async def list_projects(
    status: Optional[ProjectStatus] = None,
    project_type: Optional[ProjectType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> List[Project]:
    """获取项目列表"""
    try:
        projects = list(projects_store.values())

        # 过滤条件
        if status:
            projects = [p for p in projects if p.status == status]
        if project_type:
            projects = [p for p in projects if p.type == project_type]

        # 分页
        total = len(projects)
        projects = projects[skip : skip + limit]

        logger.info(f"获取项目列表: {len(projects)}/{total}")
        return projects

    except Exception as e:
        logger.error(f"获取项目列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")


@project_router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str) -> Project:
    """获取项目详情"""
    try:
        if project_id not in projects_store:
            raise HTTPException(status_code=404, detail="项目不存在")

        project = projects_store[project_id]
        logger.info(f"获取项目详情: {project.name}")
        return project

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {str(e)}")


@project_router.put("/{project_id}", response_model=Project)
async def update_project(project_id: str, request: UpdateProjectRequest) -> Project:
    """更新项目"""
    try:
        if project_id not in projects_store:
            raise HTTPException(status_code=404, detail="项目不存在")

        project = projects_store[project_id]

        # 更新字段
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        project.updated_at = datetime.now()
        projects_store[project_id] = project

        # 同步更新项目上下文
        if project_id in project_contexts_store:
            context = project_contexts_store[project_id]
            if request.objective:
                context.objective_guidance = request.objective
            if request.background:
                context.background_context = request.background
            if request.success_criteria:
                context.success_criteria = request.success_criteria
            if request.constraints:
                context.constraints = request.constraints
            context.updated_at = datetime.now()

        logger.info(f"更新项目成功: {project.name}")
        return project

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新项目失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新项目失败: {str(e)}")


@project_router.delete("/{project_id}")
async def delete_project(project_id: str) -> Dict:
    """删除项目（级联删除相关资源）"""
    try:
        if project_id not in projects_store:
            raise HTTPException(status_code=404, detail="项目不存在")

        project = projects_store[project_id]

        # 级联删除相关资源
        # 1. 删除代码库
        codebases_to_delete = [
            cb_id
            for cb_id, cb in codebases_store.items()
            if cb.project_id == project_id
        ]
        for cb_id in codebases_to_delete:
            del codebases_store[cb_id]

        # 2. 删除知识库挂载关系
        mounts_to_delete = [
            mount_id
            for mount_id, mount in knowledge_mounts_store.items()
            if mount.project_id == project_id
        ]
        for mount_id in mounts_to_delete:
            del knowledge_mounts_store[mount_id]

        # 3. 删除项目上下文
        if project_id in project_contexts_store:
            del project_contexts_store[project_id]

        # 4. 删除项目会话
        sessions_to_delete = [
            session_id
            for session_id, session in project_sessions_store.items()
            if session.project_id == project_id
        ]
        for session_id in sessions_to_delete:
            del project_sessions_store[session_id]

        # 最后删除项目
        del projects_store[project_id]

        logger.info(f"删除项目成功: {project.name}")
        return {
            "message": "项目删除成功",
            "project_id": project_id,
            "deleted_resources": {
                "codebases": len(codebases_to_delete),
                "knowledge_mounts": len(mounts_to_delete),
                "sessions": len(sessions_to_delete),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")


# 代码库管理端点
@project_router.post("/{project_id}/codebase", response_model=ProjectCodebase)
async def create_project_codebase(
    project_id: str, request: CreateCodebaseRequest
) -> ProjectCodebase:
    """为项目创建代码库（一对一绑定）"""
    try:
        if project_id not in projects_store:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 检查项目是否已有代码库
        existing_codebase = next(
            (cb for cb in codebases_store.values() if cb.project_id == project_id), None
        )
        if existing_codebase:
            raise HTTPException(status_code=400, detail="项目已绑定代码库")

        codebase_id = str(uuid.uuid4())

        codebase = ProjectCodebase(
            id=codebase_id,
            project_id=project_id,
            name=request.name,
            description=request.description,
            local_path=request.local_path,
            main_language=request.main_language,
            framework=request.framework,
            dependencies=request.dependencies or [],
            repository_url=request.repository_url,
        )

        codebases_store[codebase_id] = codebase

        # 更新项目上下文
        if project_id in project_contexts_store:
            context = project_contexts_store[project_id]
            context.codebase_info = {
                "id": codebase_id,
                "name": codebase.name,
                "language": codebase.main_language,
                "framework": codebase.framework,
            }
            context.updated_at = datetime.now()

        logger.info(f"创建代码库成功: {codebase.name} -> 项目: {project_id}")
        return codebase

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建代码库失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建代码库失败: {str(e)}")


@project_router.get("/{project_id}/codebase", response_model=Optional[ProjectCodebase])
async def get_project_codebase(project_id: str) -> Optional[ProjectCodebase]:
    """获取项目代码库"""
    try:
        if project_id not in projects_store:
            raise HTTPException(status_code=404, detail="项目不存在")

        codebase = next(
            (cb for cb in codebases_store.values() if cb.project_id == project_id), None
        )

        return codebase

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目代码库失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取项目代码库失败: {str(e)}")


# 知识库管理端点
@project_router.post("/knowledge-bases", response_model=KnowledgeBase)
async def create_knowledge_base(request: CreateKnowledgeBaseRequest) -> KnowledgeBase:
    """创建知识库"""
    try:
        kb_id = str(uuid.uuid4())

        knowledge_base = KnowledgeBase(
            id=kb_id,
            name=request.name,
            description=request.description,
            type=request.kb_type,
            content=request.content or {},
            patterns=request.patterns or [],
            templates=request.templates or [],
        )

        knowledge_bases_store[kb_id] = knowledge_base

        logger.info(f"创建知识库成功: {knowledge_base.name}")
        return knowledge_base

    except Exception as e:
        logger.error(f"创建知识库失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建知识库失败: {str(e)}")


@project_router.get("/knowledge-bases", response_model=List[KnowledgeBase])
async def list_knowledge_bases(
    kb_type: Optional[KnowledgeBaseType] = None,
) -> List[KnowledgeBase]:
    """获取知识库列表"""
    try:
        knowledge_bases = list(knowledge_bases_store.values())

        if kb_type:
            knowledge_bases = [kb for kb in knowledge_bases if kb.type == kb_type]

        return knowledge_bases

    except Exception as e:
        logger.error(f"获取知识库列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识库列表失败: {str(e)}")


@project_router.post(
    "/{project_id}/mount-knowledge", response_model=ProjectKnowledgeMount
)
async def mount_knowledge_base(
    project_id: str, request: MountKnowledgeBaseRequest
) -> ProjectKnowledgeMount:
    """挂载知识库到项目"""
    try:
        if project_id not in projects_store:
            raise HTTPException(status_code=404, detail="项目不存在")

        if request.knowledge_base_id not in knowledge_bases_store:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 检查是否已挂载
        existing_mount = next(
            (
                mount
                for mount in knowledge_mounts_store.values()
                if mount.project_id == project_id
                and mount.knowledge_base_id == request.knowledge_base_id
            ),
            None,
        )
        if existing_mount:
            raise HTTPException(status_code=400, detail="知识库已挂载到此项目")

        mount_id = str(uuid.uuid4())

        mount = ProjectKnowledgeMount(
            id=mount_id,
            project_id=project_id,
            knowledge_base_id=request.knowledge_base_id,
            mount_type=request.mount_type,
            priority=request.priority,
        )

        knowledge_mounts_store[mount_id] = mount

        # 更新知识库挂载统计
        kb = knowledge_bases_store[request.knowledge_base_id]
        kb.project_mount_count += 1

        # 更新项目上下文
        if project_id in project_contexts_store:
            context = project_contexts_store[project_id]
            context.available_knowledge_bases.append(request.knowledge_base_id)
            context.updated_at = datetime.now()

        logger.info(
            f"知识库挂载成功: {request.knowledge_base_id} -> 项目: {project_id}"
        )
        return mount

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"挂载知识库失败: {e}")
        raise HTTPException(status_code=500, detail=f"挂载知识库失败: {str(e)}")


@project_router.get("/{project_id}/knowledge-mounts", response_model=List[Dict])
async def get_project_knowledge_mounts(project_id: str) -> List[Dict]:
    """获取项目的知识库挂载"""
    try:
        if project_id not in projects_store:
            raise HTTPException(status_code=404, detail="项目不存在")

        mounts = [
            mount
            for mount in knowledge_mounts_store.values()
            if mount.project_id == project_id
        ]

        # 附加知识库详细信息
        result = []
        for mount in mounts:
            kb = knowledge_bases_store.get(mount.knowledge_base_id)
            if kb:
                result.append(
                    {
                        "mount": mount,
                        "knowledge_base": kb,
                    }
                )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目知识库挂载失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取项目知识库挂载失败: {str(e)}")


@project_router.get("/{project_id}/context", response_model=ProjectContext)
async def get_project_context(project_id: str) -> ProjectContext:
    """获取项目上下文（供智能体使用）"""
    try:
        if project_id not in projects_store:
            raise HTTPException(status_code=404, detail="项目不存在")

        if project_id not in project_contexts_store:
            raise HTTPException(status_code=404, detail="项目上下文不存在")

        context = project_contexts_store[project_id]
        return context

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目上下文失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取项目上下文失败: {str(e)}")


# 项目统计端点
@project_router.get("/stats/overview")
async def get_projects_overview() -> Dict:
    """获取项目总览统计"""
    try:
        projects = list(projects_store.values())

        stats = {
            "total_projects": len(projects),
            "active_projects": len(
                [p for p in projects if p.status == ProjectStatus.ACTIVE]
            ),
            "completed_projects": len(
                [p for p in projects if p.status == ProjectStatus.COMPLETED]
            ),
            "projects_by_type": {},
            "projects_by_status": {},
            "total_codebases": len(codebases_store),
            "total_knowledge_bases": len(knowledge_bases_store),
            "total_knowledge_mounts": len(knowledge_mounts_store),
        }

        # 按类型统计
        for project in projects:
            project_type = project.type.value
            stats["projects_by_type"][project_type] = (
                stats["projects_by_type"].get(project_type, 0) + 1
            )

        # 按状态统计
        for project in projects:
            project_status = project.status.value
            stats["projects_by_status"][project_status] = (
                stats["projects_by_status"].get(project_status, 0) + 1
            )

        return stats

    except Exception as e:
        logger.error(f"获取项目统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取项目统计失败: {str(e)}")
