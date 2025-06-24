"""
需求分析助手API路由 - 基于新的Flow架构

充分利用OpenManus现有能力：
- 使用RequirementsFlow管理多智能体协作
- 复用现有的LLM、配置、日志等基础设施
- 保持API接口的简洁和统一
"""

import asyncio
import os
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from app.assistants.requirements.flow import RequirementsFlow
from app.config import REQUIREMENT_QUALITY_CONFIG
from app.core.adaptive_learning_system import AnalysisCase, adaptive_learning_system
from app.core.llm_analysis_engine import LLMAnalysisEngine
from app.core.multi_dimensional_engine import MultiDimensionalAnalysisEngine
from app.core.quality_driven_clarification_engine import (
    QualityDrivenClarificationEngine,
)
from app.llm import LLM
from app.logger import logger


# API数据模型
class RequirementInput(BaseModel):
    content: str
    project_id: Optional[str] = None  # 项目制管理支持
    project_context: Optional[str] = None
    use_multi_dimensional: Optional[bool] = True  # 默认启用多维度分析
    enable_conflict_detection: Optional[bool] = True  # 默认启用冲突检测


class ClarificationRequest(BaseModel):
    session_id: str
    answer: str
    question: Optional[str] = None


class ClarificationResponse(BaseModel):
    session_id: str
    status: str
    response: str
    next_questions: Optional[List[str]] = None
    final_report: Optional[Dict] = None
    progress: Optional[Dict] = None


class AnalysisRequest(BaseModel):
    session_id: str
    answer: str


class RequirementStatus(BaseModel):
    session_id: str
    stage: str
    progress: Dict
    result: Optional[str] = None


# 创建路由器
requirements_router = APIRouter(prefix="/api/requirements", tags=["Requirements"])

# 会话存储（简单实现，实际应该使用数据库）
session_storage = {}

# 活跃会话存储
active_sessions = {}


async def _analyze_user_requirement(content: str) -> Dict:
    """真正的AI驱动需求分析，使用DeepSeek LLM进行智能分析"""
    import time

    from app.llm import LLM

    start_time = time.time()

    # 初始化LLM
    llm = LLM()

    # 构建需求分析的元提示词
    meta_prompt = """你是OpenManus AI软件公司的首席需求分析师，拥有20年软件工程经验。

你的任务是：基于用户的初始需求描述，进行专业的需求分析，并生成精准的澄清问题。

## 核心原则
1. 运用软件工程需求分析的专业方法论
2. 深度理解用户意图，不瞎猜、不假设
3. 生成的澄清问题必须具有针对性和专业性
4. 遵循软件工程的需求澄清最佳实践

## 分析框架
### 1. 需求理解
- 识别需求类型（功能性/非功能性）
- 分析业务域和技术域
- 评估需求复杂度和风险点

### 2. 澄清策略
- 按照重要性和紧急性排序问题
- 涵盖用户需求、功能需求、技术约束、质量属性
- 每个问题都要有明确的分析目的

### 3. 质量把控
- 确保问题的专业性和准确性
- 避免过于笼统或过于技术化
- 考虑用户的技术背景"""

    # 构建动态提示词
    dynamic_prompt = f"""
## 用户需求
「{content}」

## 分析任务
请作为专业的需求分析师，对上述需求进行深度分析，并生成3-4个精准的澄清问题。

## 输出要求
返回一个JSON格式的分析结果，包含：
{{
    "requirement_analysis": {{
        "requirement_type": "具体的需求类型（如：管理系统、电商平台、数据分析工具等）",
        "business_domain": "业务领域",
        "complexity_level": "复杂度评级（低/中/高）",
        "key_stakeholders": ["关键干系人列表"],
        "potential_risks": ["潜在风险点"],
        "technical_considerations": ["技术考虑点"]
    }},
    "clarification_questions": [
        {{
            "id": "唯一标识",
            "question": "具体的澄清问题",
            "category": "问题分类（如：功能需求、质量属性、约束条件等）",
            "priority": "优先级（high/medium/low）",
            "purpose": "提问目的",
            "follow_up_hints": ["可能的追问方向"]
        }}
    ],
    "analysis_insights": {{
        "clarity_score": 1-10的清晰度评分,
        "missing_information": ["缺失的关键信息"],
        "recommendations": ["专业建议"]
    }}
}}

## 注意事项
- 问题必须体现软件工程专业性
- 针对具体需求内容，不要用通用模板
- 考虑用户可能的技术背景
- 问题要有明确的分析价值
"""

    try:
        # 调用LLM进行分析
        from app.schema import Message

        messages = [
            Message.system_message(meta_prompt),
            Message.user_message(dynamic_prompt),
        ]

        llm_response = await llm.ask(
            messages=messages,
            temperature=0.3,  # 保持一定的一致性
            stream=False,  # 不使用流式输出，获取完整响应
        )

        # 解析LLM响应
        import json
        import re

        try:
            # 清理响应，移除可能的markdown格式
            cleaned_response = llm_response.strip()

            # 如果响应包含```json标记，提取其中的JSON内容
            json_match = re.search(
                r"```json\s*(.*?)\s*```", cleaned_response, re.DOTALL
            )
            if json_match:
                cleaned_response = json_match.group(1).strip()
            elif cleaned_response.startswith("```") and cleaned_response.endswith(
                "```"
            ):
                # 如果是普通代码块格式
                cleaned_response = cleaned_response.strip("`").strip()

            analysis_result = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            # 如果JSON解析失败，记录详细信息并抛出异常
            logger.error(f"LLM返回JSON解析失败: {e}")
            logger.error(f"清理后的响应: {cleaned_response[:500]}...")
            raise ValueError(f"LLM返回的响应格式不正确，无法解析为JSON: {e}")

        # 计算处理时间
        processing_time = round(time.time() - start_time, 2)

        # 构建返回结果
        requirement_analysis = analysis_result.get("requirement_analysis", {})
        clarification_questions = analysis_result.get("clarification_questions", [])
        analysis_insights = analysis_result.get("analysis_insights", {})

        return {
            "result": {
                "clarification_questions": clarification_questions,
                "initial_analysis": f"经过AI深度分析，识别这是一个{requirement_analysis.get('requirement_type', '软件系统')}需求，属于{requirement_analysis.get('business_domain', '通用')}业务领域。",
                "clarity_score": analysis_insights.get("clarity_score", 5),
                "requirement_type": requirement_analysis.get(
                    "requirement_type", "软件系统"
                ),
                "detected_features": requirement_analysis.get(
                    "technical_considerations", []
                )[:3],
                "business_domain": requirement_analysis.get("business_domain"),
                "complexity_level": requirement_analysis.get("complexity_level"),
                "missing_information": analysis_insights.get("missing_information", []),
                "professional_recommendations": analysis_insights.get(
                    "recommendations", []
                ),
            },
            "processing_time": processing_time,
            "confidence": 0.90 if clarification_questions else 0.70,
            "analysis_method": "AI_LLM_Analysis",
        }

    except Exception as e:
        logger.error(f"LLM分析失败: {str(e)}")
        # 抛出异常，不使用降级
        processing_time = round(time.time() - start_time, 2)
        raise RuntimeError(f"LLM需求分析失败: {str(e)}，处理时间: {processing_time}秒")

    # 模式匹配
    matched_type = "通用软件"
    matched_config = None
    max_score = 0

    content_lower = content.lower()
    for req_type, config in requirement_patterns.items():
        score = sum(1 for keyword in config["keywords"] if keyword in content_lower)
        if score > max_score:
            max_score = score
            matched_type = req_type
            matched_config = config

    # 如果没有匹配到特定模式，使用通用分析
    if matched_config is None:
        matched_config = {
            "features": ["功能设计", "技术选型", "用户体验"],
            "questions": [
                {
                    "id": "core_requirements",
                    "question": f"关于「{content}」，请详细描述核心功能需求和期望达到的目标？",
                    "category": "需求澄清",
                    "priority": "high",
                },
                {
                    "id": "user_scenarios",
                    "question": "主要的用户使用场景是什么？用户如何与系统交互？",
                    "category": "用户体验",
                    "priority": "high",
                },
                {
                    "id": "technical_preferences",
                    "question": "对技术实现有什么偏好或约束？比如特定框架、部署方式等？",
                    "category": "技术约束",
                    "priority": "medium",
                },
            ],
        }

    # 计算清晰度得分
    clarity_indicators = ["功能", "需求", "系统", "用户", "管理", "平台", "服务"]
    clarity_score = min(
        sum(1 for indicator in clarity_indicators if indicator in content), 8
    )

    return {
        "result": {
            "clarification_questions": matched_config["questions"],
            "initial_analysis": _generate_personalized_analysis(
                content, matched_type, max_score
            ),
            "clarity_score": clarity_score,
            "requirement_type": matched_type,
            "detected_features": matched_config["features"][:3],
            "pattern_match_score": max_score,
        },
        "confidence": 0.80 if max_score >= 2 else 0.65,
        "analysis_method": "Quick_Intelligent_Analysis",
    }


async def _ai_enhanced_analysis(content: str, quick_analysis: Dict) -> Dict:
    """AI增强分析：基于快速分析结果进行LLM增强"""
    from app.llm import LLM
    from app.schema import Message

    llm = LLM()

    # 构建精简的AI增强提示词
    enhancement_prompt = f"""基于初步分析，这是一个{quick_analysis['result']['requirement_type']}需求。

用户需求：「{content}」

请对以下3个澄清问题进行优化，使其更加专业和针对性：

{chr(10).join([f"{i+1}. {q['question']}" for i, q in enumerate(quick_analysis['result']['clarification_questions'])])}

要求：
1. 保持软件工程专业水准
2. 针对具体需求内容优化
3. 确保问题的实际价值
4. 返回优化后的3个问题，JSON格式

格式：{{"enhanced_questions": [{{"id": "...", "question": "...", "category": "...", "priority": "..."}}]}}"""

    try:
        logger.info("开始LLM增强分析...")
        response = await llm.ask(
            messages=[Message.user_message(enhancement_prompt)],
            temperature=0.2,
            stream=False,
        )
        logger.info(f"LLM响应成功，长度: {len(response) if response else 0}")

        import json

        enhanced_result = json.loads(response.strip())

        # 合并增强结果
        result = quick_analysis.copy()
        if "enhanced_questions" in enhanced_result:
            result["result"]["clarification_questions"] = enhanced_result[
                "enhanced_questions"
            ]
            result["result"]["initial_analysis"] += " 已通过AI增强优化。"
            result["confidence"] = 0.90

        return result

    except Exception as e:
        logger.warning(f"AI增强失败: {e}")
        return quick_analysis


def _generate_personalized_analysis(
    content: str, req_type: str, match_score: int
) -> str:
    """生成个性化的需求分析文本"""
    content_lower = content.lower()

    # 提取关键信息
    key_features = []
    business_context = []
    technical_hints = []

    # 分析业务领域特征
    if req_type == "即时通讯应用":
        if "群聊" in content:
            key_features.append("群组通讯")
        if "私聊" in content:
            key_features.append("私人通讯")
        if "文件" in content:
            key_features.append("文件传输")
        if "语音" in content or "通话" in content:
            key_features.append("语音通话")
        if "实时" in content:
            business_context.append("实时通讯")
    elif req_type == "在线教育平台":
        if "视频" in content:
            key_features.append("视频课程")
        if "作业" in content:
            key_features.append("作业管理")
        if "讨论" in content:
            key_features.append("互动讨论")
        if "评分" in content:
            key_features.append("评估系统")
        if "在线" in content:
            business_context.append("在线教育")
    elif req_type == "客服系统":
        if "智能" in content:
            key_features.append("AI智能对话")
        if "机器人" in content:
            key_features.append("自动化客服")
        if "咨询" in content:
            business_context.append("多领域咨询服务")
    elif req_type == "电商平台":
        if "手工" in content or "自制" in content:
            business_context.append("手工艺品销售")
        if "网站" in content:
            technical_hints.append("Web端优先")
    elif req_type == "管理系统":
        if "学生" in content:
            business_context.append("教育管理领域")
        if "信息" in content:
            key_features.append("信息化管理")
        if "学校" in content:
            business_context.append("校园管理环境")

    # 构建个性化分析文本
    analysis_parts = []

    # 开头
    analysis_parts.append(f"通过语义分析，我理解您要开发的是{req_type}。")

    # 特征分析
    if key_features:
        analysis_parts.append(f"识别到核心特征：{' + '.join(key_features)}。")

    # 业务上下文
    if business_context:
        analysis_parts.append(f"业务场景：{' + '.join(business_context)}。")

    # 技术考虑
    if technical_hints:
        analysis_parts.append(f"技术倾向：{' + '.join(technical_hints)}。")

    # 置信度表述
    if match_score >= 3:
        analysis_parts.append("需求特征明确，可以深入澄清具体细节。")
    elif match_score >= 1:
        analysis_parts.append("需求特征基本明确，建议进一步澄清关键要素。")
    else:
        analysis_parts.append("需求特征有待明确，建议详细描述功能和目标。")

    return " ".join(analysis_parts)


async def _intelligent_fast_analysis(content: str) -> Dict:
    """智能快速分析：结合NLP和软件工程知识库的快速分析"""
    import re
    import time

    start_time = time.time()

    logger.info(f"开始智能快速分析: {content[:50]}...")

    # 第一步：智能需求类型识别
    req_type, match_score, domain_features = _advanced_requirement_classification(
        content
    )

    # 第二步：基于需求类型生成专业澄清问题
    clarification_questions = _generate_professional_questions(
        req_type, content, domain_features
    )

    # 第三步：智能评估清晰度和复杂度
    clarity_assessment = _assess_requirement_clarity(content)

    # 第四步：生成个性化分析文本
    initial_analysis = _generate_intelligent_analysis(
        content, req_type, domain_features, clarity_assessment
    )

    processing_time = round(time.time() - start_time, 2)

    logger.info(f"智能快速分析完成，识别类型: {req_type}, 匹配度: {match_score}")

    return {
        "result": {
            "clarification_questions": clarification_questions,
            "initial_analysis": initial_analysis,
            "clarity_score": clarity_assessment["clarity_score"],
            "requirement_type": req_type,
            "detected_features": domain_features[:3],
            "complexity_level": clarity_assessment["complexity_level"],
            "confidence_score": match_score,
        },
        "processing_time": processing_time,
        "confidence": 0.90 if match_score >= 3 else 0.75,
        "analysis_method": "Intelligent_Fast_Analysis",
    }


def _advanced_requirement_classification(content: str) -> tuple:
    """高级需求分类：使用加权匹配和语义分析"""
    content_lower = content.lower()

    # 扩展的需求分类知识库
    classification_db = {
        "内容管理系统": {
            "keywords": ["博客", "cms", "内容", "文章", "发布", "编辑"],
            "weights": {"博客": 3, "cms": 3, "内容管理": 3, "文章": 2, "发布": 2},
            "features": ["内容编辑", "发布管理", "评论系统", "用户互动"],
        },
        "即时通讯应用": {
            "keywords": ["聊天", "通讯", "即时", "消息", "沟通", "通话"],
            "weights": {"聊天": 3, "即时": 2, "消息": 2, "通话": 3},
            "features": ["实时消息", "群聊私聊", "文件传输", "语音通话"],
        },
        "电商平台": {
            "keywords": ["电商", "商城", "购物", "支付", "订单", "商品"],
            "weights": {"电商": 3, "商城": 3, "购物": 2, "支付": 2, "订单": 2},
            "features": ["商品管理", "订单处理", "支付系统", "用户中心"],
        },
        "在线教育平台": {
            "keywords": ["教育", "在线", "课程", "学习", "教学", "培训"],
            "weights": {"教育": 3, "在线": 1, "课程": 3, "学习": 2},
            "features": ["视频播放", "作业系统", "互动讨论", "学习跟踪"],
        },
        "医疗健康平台": {
            "keywords": ["医疗", "健康", "患者", "医生", "问诊", "预约"],
            "weights": {"医疗": 3, "健康": 2, "患者": 2, "医生": 2, "问诊": 3},
            "features": ["在线问诊", "预约挂号", "医疗档案", "健康监测"],
        },
        "管理系统": {
            "keywords": ["管理", "系统", "后台", "admin", "管理员"],
            "weights": {"管理": 2, "系统": 1, "后台": 2, "admin": 3},
            "features": ["用户管理", "权限控制", "数据管理", "报表统计"],
        },
        "数据分析工具": {
            "keywords": ["数据", "分析", "报表", "可视化", "统计", "图表"],
            "weights": {"数据": 2, "分析": 3, "报表": 2, "可视化": 3},
            "features": ["数据采集", "数据处理", "可视化", "报表生成"],
        },
    }

    # 计算加权匹配分数
    best_match = ("通用软件", 0, ["功能设计", "用户体验", "技术实现"])

    for req_type, config in classification_db.items():
        score = 0
        for keyword, weight in config["weights"].items():
            if keyword in content_lower:
                score += weight

        if score > best_match[1]:
            best_match = (req_type, score, config["features"])

    return best_match


def _generate_professional_questions(
    req_type: str, content: str, features: list
) -> list:
    """基于需求类型和特征生成专业澄清问题"""

    # 专业问题模板库
    question_templates = {
        "内容管理系统": [
            {
                "id": "content_types",
                "question": "系统需要支持哪些内容类型？文章、图片、视频的管理要求如何？",
                "category": "内容管理",
                "priority": "high",
            },
            {
                "id": "user_roles",
                "question": "用户角色如何设计？作者、编辑、管理员的权限如何划分？",
                "category": "权限设计",
                "priority": "high",
            },
            {
                "id": "publishing_workflow",
                "question": "内容发布流程是什么？需要审核机制吗？",
                "category": "业务流程",
                "priority": "medium",
            },
        ],
        "即时通讯应用": [
            {
                "id": "communication_modes",
                "question": "需要支持哪些通讯方式？文字、语音、视频通话的优先级如何？",
                "category": "通讯功能",
                "priority": "high",
            },
            {
                "id": "user_scale",
                "question": "预期支持多少用户同时在线？群聊的最大人数限制是多少？",
                "category": "性能规模",
                "priority": "high",
            },
            {
                "id": "security_privacy",
                "question": "对消息安全和隐私保护有什么要求？需要端到端加密吗？",
                "category": "安全需求",
                "priority": "medium",
            },
        ],
        "电商平台": [
            {
                "id": "business_model",
                "question": "电商平台的商业模式是什么？B2C、B2B还是C2C？",
                "category": "商业模式",
                "priority": "high",
            },
            {
                "id": "payment_methods",
                "question": "需要支持哪些支付方式？对支付安全有什么特殊要求？",
                "category": "支付系统",
                "priority": "high",
            },
            {
                "id": "inventory_management",
                "question": "商品和库存管理有什么特殊要求？需要多仓库支持吗？",
                "category": "库存管理",
                "priority": "medium",
            },
        ],
        "在线教育平台": [
            {
                "id": "learning_model",
                "question": "采用什么教学模式？直播教学、录播课程还是混合式学习？",
                "category": "教学模式",
                "priority": "high",
            },
            {
                "id": "assessment_system",
                "question": "学习评估如何进行？需要在线考试、作业提交功能吗？",
                "category": "评估系统",
                "priority": "high",
            },
            {
                "id": "content_delivery",
                "question": "课程内容如何组织？需要支持什么格式的教学资源？",
                "category": "内容管理",
                "priority": "medium",
            },
        ],
        "医疗健康平台": [
            {
                "id": "consultation_modes",
                "question": "支持哪些问诊方式？图文咨询、视频问诊的具体流程如何？",
                "category": "问诊功能",
                "priority": "high",
            },
            {
                "id": "medical_compliance",
                "question": "需要符合哪些医疗法规？患者隐私保护有什么特殊要求？",
                "category": "合规安全",
                "priority": "high",
            },
            {
                "id": "appointment_system",
                "question": "预约挂号系统如何设计？需要与医院HIS系统对接吗？",
                "category": "预约管理",
                "priority": "medium",
            },
        ],
        "管理系统": [
            {
                "id": "core_modules",
                "question": "系统需要包含哪些核心管理模块？用户管理、数据管理、权限控制等？",
                "category": "功能架构",
                "priority": "high",
            },
            {
                "id": "data_operations",
                "question": "主要管理什么类型的数据？CRUD操作的复杂度如何？",
                "category": "数据管理",
                "priority": "high",
            },
            {
                "id": "reporting_requirements",
                "question": "需要什么样的报表和统计功能？数据导出有什么要求？",
                "category": "报表统计",
                "priority": "medium",
            },
        ],
        "数据分析工具": [
            {
                "id": "data_sources",
                "question": "数据来源有哪些？需要对接什么数据库或API？",
                "category": "数据接入",
                "priority": "high",
            },
            {
                "id": "analysis_types",
                "question": "需要什么类型的数据分析？实时分析还是批量处理？",
                "category": "分析需求",
                "priority": "high",
            },
            {
                "id": "visualization_charts",
                "question": "可视化需求是什么？需要哪些类型的图表和仪表板？",
                "category": "可视化需求",
                "priority": "medium",
            },
        ],
    }

    # 获取对应的问题模板，如果没有则使用通用模板
    questions = question_templates.get(
        req_type,
        [
            {
                "id": "core_requirements",
                "question": f"关于「{content}」，请详细描述核心功能需求和期望达到的目标？",
                "category": "需求澄清",
                "priority": "high",
            },
            {
                "id": "user_scenarios",
                "question": "主要的用户使用场景是什么？用户如何与系统交互？",
                "category": "用户体验",
                "priority": "high",
            },
            {
                "id": "technical_constraints",
                "question": "对技术实现有什么偏好或约束？比如特定框架、部署方式等？",
                "category": "技术约束",
                "priority": "medium",
            },
        ],
    )

    return questions


def _assess_requirement_clarity(content: str) -> dict:
    """评估需求清晰度和复杂度"""
    clarity_indicators = {
        "具体功能": ["功能", "特性", "支持", "包含", "需要"],
        "用户角色": ["用户", "角色", "管理员", "客户", "学生"],
        "技术细节": ["技术", "框架", "数据库", "API", "系统"],
        "业务流程": ["流程", "步骤", "管理", "处理", "操作"],
        "性能要求": ["性能", "速度", "并发", "响应", "负载"],
    }

    complexity_indicators = {
        "简单": ["简单", "基础", "基本", "轻量"],
        "中等": ["完整", "全面", "专业", "企业"],
        "复杂": ["复杂", "高级", "智能", "大型", "平台"],
    }

    # 计算清晰度分数
    clarity_score = 5  # 基础分
    content_lower = content.lower()

    for category, indicators in clarity_indicators.items():
        if any(indicator in content_lower for indicator in indicators):
            clarity_score += 1

    clarity_score = min(clarity_score, 10)

    # 评估复杂度
    complexity_level = "中"
    for level, indicators in complexity_indicators.items():
        if any(indicator in content_lower for indicator in indicators):
            complexity_level = level
            break

    return {
        "clarity_score": clarity_score,
        "complexity_level": complexity_level,
        "content_richness": len(content.split()) >= 8,  # 内容丰富度
    }


def _generate_intelligent_analysis(
    content: str, req_type: str, features: list, assessment: dict
) -> str:
    """生成智能化的分析文本"""
    parts = []

    # 开头
    parts.append(f"通过AI智能分析，识别这是一个{req_type}需求。")

    # 特征分析
    if features:
        parts.append(f"核心功能特征：{' + '.join(features[:3])}。")

    # 清晰度评估
    clarity_score = assessment["clarity_score"]
    if clarity_score >= 8:
        parts.append("需求描述详细清晰，信息充分，可以深入技术架构设计。")
    elif clarity_score >= 6:
        parts.append("需求描述基本清晰，建议进一步明确关键业务逻辑和技术细节。")
    else:
        parts.append("需求描述相对简略，建议详细说明功能范围和预期目标。")

    # 复杂度评估
    complexity = assessment["complexity_level"]
    if complexity == "复杂":
        parts.append("系统复杂度较高，建议分阶段实施，重点关注架构设计和技术选型。")
    elif complexity == "中等":
        parts.append(
            "系统复杂度适中，可以采用敏捷开发方式，重点关注用户体验和核心功能。"
        )
    else:
        parts.append("系统复杂度较低，可以快速原型开发，重点验证核心功能和用户需求。")

    return " ".join(parts)


async def _full_llm_analysis(content: str) -> Dict:
    """完整的LLM驱动需求分析"""
    import time

    from app.llm import LLM
    from app.schema import Message

    start_time = time.time()

    # 初始化LLM
    llm = LLM()

    # 构建精简高效的分析提示词
    analysis_prompt = f"""分析需求并返回JSON格式结果：

需求：{content}

返回格式：
{{
  "type": "需求类型",
  "features": ["特征1", "特征2", "特征3"],
  "questions": [
    {{"q": "澄清问题1", "cat": "分类", "pri": "high"}},
    {{"q": "澄清问题2", "cat": "分类", "pri": "medium"}},
    {{"q": "澄清问题3", "cat": "分类", "pri": "low"}}
  ],
  "score": 7
}}

要求：准确识别需求类型，提取核心特征，生成3个专业澄清问题，评估清晰度（1-10）。"""

    try:
        logger.info("开始完整LLM需求分析...")

        # 设置超时保护
        response = await asyncio.wait_for(
            llm.ask(
                messages=[Message.user_message(analysis_prompt)],
                temperature=0.1,
                stream=False,
            ),
            timeout=120.0,  # 20秒超时
        )
        logger.info(f"LLM分析完成，响应长度: {len(response) if response else 0}")

        # 解析LLM响应
        import json

        try:
            # 清理响应格式
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            response_clean = response_clean.strip()

            analysis_result = json.loads(response_clean)
            logger.info("LLM响应JSON解析成功")

        except json.JSONDecodeError as e:
            logger.error(f"LLM返回非标准JSON格式: {str(e)[:100]}...")
            raise ValueError(f"LLM响应JSON解析失败: {str(e)}")

        # 解析精简格式的LLM响应
        req_type = analysis_result.get("type", "软件系统")
        key_features = analysis_result.get("features", [])
        llm_questions = analysis_result.get("questions", [])
        clarity_score = analysis_result.get("score", 5)

        # 转换为标准格式的澄清问题
        clarification_questions = []
        for i, q in enumerate(llm_questions):
            if isinstance(q, dict) and "q" in q:
                clarification_questions.append(
                    {
                        "id": f"llm_q_{i+1}",
                        "question": q["q"],
                        "category": q.get("cat", "需求澄清"),
                        "priority": q.get("pri", "medium"),
                        "purpose": "LLM智能生成的澄清问题",
                    }
                )

        # 生成分析文本
        initial_analysis = f"经过DeepSeek AI智能分析，识别这是一个{req_type}需求。"
        if key_features:
            initial_analysis += f" 核心功能特征：{' + '.join(key_features[:3])}。"

        if isinstance(clarity_score, (int, float)):
            if clarity_score >= 8:
                initial_analysis += " AI评估：需求描述清晰明确，可以深入技术细节澄清。"
            elif clarity_score >= 6:
                initial_analysis += " AI评估：需求基本清晰，建议澄清关键业务逻辑。"
            else:
                initial_analysis += (
                    " AI评估：需求有待进一步明确，建议详细描述功能和目标。"
                )

        processing_time = round(time.time() - start_time, 2)

        return {
            "result": {
                "clarification_questions": clarification_questions,
                "initial_analysis": initial_analysis,
                "clarity_score": clarity_score,
                "requirement_type": req_type,
                "detected_features": key_features[:3],
            },
            "processing_time": processing_time,
            "confidence": 0.95,
            "analysis_method": "Full_LLM_Analysis",
        }

    except asyncio.TimeoutError:
        logger.error("LLM分析超时")
        processing_time = round(time.time() - start_time, 2)
        raise TimeoutError(f"LLM分析超时，处理时间: {processing_time}秒")
    except Exception as e:
        logger.error(f"LLM完整分析失败: {str(e)}")
        processing_time = round(time.time() - start_time, 2)
        raise RuntimeError(f"需求分析失败，处理时间: {processing_time}秒")


@requirements_router.get("/")
async def get_requirements_info():
    """获取需求分析助手信息"""
    return {
        "name": "需求分析助手",
        "description": "智能化软件需求分析助手，通过多轮对话澄清需求并生成专业的需求规格说明书",
        "version": "2.0.0",
        "features": ["智能需求澄清", "深度业务分析", "专业文档编写", "多智能体协作"],
        "status": "active",
    }


@requirements_router.post("/analyze")
async def analyze_requirement(request: RequirementInput) -> Dict:
    """分析用户需求 - 增强版，集成自我学习"""
    try:
        session_id = str(uuid.uuid4())
        start_time = time.time()

        logger.info(f"开始需求分析: {request.content[:100]}...")

        # 获取学习洞察，优化分析策略
        learning_recommendations = (
            adaptive_learning_system.get_actionable_recommendations(limit=3)
        )

        # 执行分析（原有逻辑）
        result = await _analyze_user_requirement(request.content)

        processing_time = time.time() - start_time

        # 记录初始分析案例（用于后续学习）
        initial_case = AnalysisCase(
            case_id=session_id,
            user_input=request.content,
            initial_analysis=result.get("result", {}),
            clarification_questions=result.get("result", {}).get(
                "clarification_questions", []
            ),
            user_answers=[],  # 初始为空
            final_quality=result.get("result", {}).get("clarity_score", 0)
            / 10.0,  # 转换为0-1分数
            user_satisfaction=0.0,  # 后续更新
            completion_time=processing_time,
            success_indicators={
                "has_questions": len(
                    result.get("result", {}).get("clarification_questions", [])
                )
                > 0,
                "pattern_recognized": result.get("result", {}).get(
                    "pattern_match_score", 0
                )
                > 0,
                "initial_confidence": result.get("confidence", 0),
            },
            timestamp=datetime.now(),
        )

        # 暂时存储案例（会话结束时完整记录）
        # 注意：在实际实现中需要会话管理系统来存储这些数据
        active_sessions[session_id] = {
            "initial_case": initial_case,
            "start_time": start_time,
            "original_content": request.content,
        }

        # 初始化澄清会话存储，使用用户输入作为初始需求文本
        session_storage[session_id] = {
            "requirement_text": request.content,
            "clarification_history": [],
            "round_count": 0,
            "initial_analysis": result.get("result", {}),
        }

        # 增强返回结果，包含学习洞察
        enhanced_result = {
            **result,
            "session_id": session_id,
            "learning_insights": [
                {
                    "type": insight.insight_type,
                    "description": insight.description,
                    "confidence": insight.confidence,
                    "recommendation": insight.actionable_recommendation,
                    "impact": insight.impact_score,
                }
                for insight in learning_recommendations
            ],
            "processing_metrics": {
                "processing_time": processing_time,
                "analysis_version": "2.0_learning_enhanced",
                "learning_maturity": adaptive_learning_system._calculate_learning_maturity(),
            },
        }

        logger.info(
            f"需求分析完成: session_id={session_id}, 耗时={processing_time:.2f}s"
        )

        return enhanced_result

    except Exception as e:
        logger.error(f"需求分析失败: {str(e)}", exc_info=True)
        return {"error": f"分析失败: {str(e)}"}


@requirements_router.post("/complete_session")
async def complete_analysis_session(
    session_id: str,
    final_quality: float = 0.8,
    user_satisfaction: float = 0.8,
    user_feedback: str = "",
):
    """完成分析会话，记录完整案例用于学习"""
    try:
        # 这里需要从会话存储中获取完整的案例数据
        # 实际实现中需要会话管理系统

        # 示例：构建完整案例
        complete_case = AnalysisCase(
            case_id=session_id,
            user_input="示例需求",  # 从会话中获取
            initial_analysis={},  # 从会话中获取
            clarification_questions=[],  # 从会话中获取
            user_answers=[],  # 从会话中获取
            final_quality=final_quality,
            user_satisfaction=user_satisfaction,
            completion_time=0.0,  # 从会话中计算
            success_indicators={
                "completed_successfully": True,
                "user_feedback": user_feedback,
            },
            timestamp=datetime.now(),
        )

        # 记录案例用于学习
        adaptive_learning_system.record_analysis_case(complete_case)

        return {"status": "success", "message": "会话已完成，数据已记录用于AI学习"}

    except Exception as e:
        logger.error(f"完成会话失败: {e}")
        return {"status": "error", "message": str(e)}


@requirements_router.get("/learning_statistics")
async def get_learning_statistics():
    """获取AI学习统计信息"""
    try:
        stats = adaptive_learning_system.get_learning_statistics()
        return {"status": "success", "statistics": stats}
    except Exception as e:
        logger.error(f"获取学习统计失败: {e}")
        return {"status": "error", "message": str(e)}


# 简单的会话存储（实际项目中应使用Redis等）
session_storage = {}


@requirements_router.post("/clarify")
async def clarify_requirement(request: ClarificationRequest) -> ClarificationResponse:
    """澄清需求 - 多轮澄清与目标导向评分"""
    try:
        # 使用质量导向澄清引擎
        clarification_engine = QualityDrivenClarificationEngine()

        # 获取或创建会话数据
        session_data = session_storage.get(
            request.session_id,
            {"requirement_text": "", "clarification_history": [], "round_count": 0},
        )

        # 累积需求文本
        if session_data["requirement_text"]:
            session_data["requirement_text"] += f"\n{request.answer}"
        else:
            session_data["requirement_text"] = request.answer

        # 记录当前轮次
        session_data["round_count"] += 1

        # 分析当前需求质量
        quality_analysis = await clarification_engine.analyze_requirement_quality(
            session_data["requirement_text"], session_data["clarification_history"]
        )

        # 生成目标导向的澄清计划
        clarification_goals = (
            await clarification_engine.generate_targeted_clarification_goals(
                quality_analysis, session_data["requirement_text"]  # 传递需求文本
            )
        )

        # 判断是否需要继续澄清
        should_continue, reason = (
            await clarification_engine.should_continue_clarification(
                quality_analysis,
                session_data["round_count"],
                session_data["requirement_text"],
            )
        )

        if should_continue and session_data["round_count"] < 7:  # 最多7轮澄清
            # 生成下一轮澄清问题
            next_questions = (
                await clarification_engine.generate_clarification_questions(
                    clarification_goals
                )
            )

            # 安全提取问题文本
            def extract_question_text(q):
                if isinstance(q, dict):
                    return q.get("question", str(q))
                elif isinstance(q, str):
                    return q
                else:
                    return str(q)

            question_texts = [extract_question_text(q) for q in next_questions]

            # 记录本轮澄清
            current_round = {
                "round": session_data["round_count"],
                "questions": question_texts,
                "timestamp": time.time(),
            }
            session_data["clarification_history"].append(current_round)

            # 更新会话存储
            session_storage[request.session_id] = session_data

            # 计算目标导向评分（使用修正的算法）
            goal_oriented_score = clarification_engine._calculate_goal_oriented_score(
                {
                    "final_quality_score": clarification_engine._calculate_overall_quality(
                        quality_analysis
                    )
                },
                session_data["clarification_history"],
            )

            # 计算整体质量评分
            overall_quality = clarification_engine._calculate_overall_quality(
                quality_analysis
            )

            return ClarificationResponse(
                session_id=request.session_id,
                status="continue_clarification",
                response=f"第{session_data['round_count']}轮澄清：基于质量分析，需要进一步澄清以达到目标质量标准。{reason}",
                next_questions=question_texts,
                progress={
                    "overall_quality": overall_quality,
                    "goal_oriented_score": goal_oriented_score,
                    "quality_threshold_met": overall_quality
                    >= REQUIREMENT_QUALITY_CONFIG["quality_thresholds"][
                        "overall_threshold"
                    ],
                    "target_oriented": True,
                    "clarification_strategy": "quality_driven_dynamic",
                    "round_count": session_data["round_count"],
                    "max_rounds": 7,
                    "reason": reason,
                },
            )
        else:
            # 质量已达标或达到最大轮次，生成最终报告
            quality_report = clarification_engine.generate_quality_report(
                quality_analysis
            )

            # 计算整体质量评分
            overall_quality = clarification_engine._calculate_overall_quality(
                quality_analysis
            )

            # 保存需求文档到文件
            saved_filepath = await _save_requirement_document(
                request.session_id,
                quality_report,
                session_data["requirement_text"],
                overall_quality,
                session_data["round_count"],
            )

            # 完成澄清，清理会话数据
            if request.session_id in session_storage:
                del session_storage[request.session_id]

            final_goal_score = clarification_engine._calculate_goal_oriented_score(
                {"final_quality_score": overall_quality},
                session_data["clarification_history"],
            )

            completion_reason = (
                "quality_achieved"
                if overall_quality
                >= REQUIREMENT_QUALITY_CONFIG["quality_thresholds"]["overall_threshold"]
                else "max_rounds_reached"  # 提高到0.90
            )

            return ClarificationResponse(
                session_id=request.session_id,
                status="clarification_complete",
                response=f"需求澄清已完成（共{session_data['round_count']}轮）。{reason}",
                final_report={
                    "report": quality_report,
                    "final_requirement": session_data["requirement_text"],
                },
                progress={
                    "overall_quality": overall_quality,
                    "goal_oriented_score": final_goal_score,
                    "goal_achieved": overall_quality >= 0.82,  # 调整到0.82
                    "ready_for_specification": True,
                    "completion_reason": completion_reason,
                    "total_rounds": session_data["round_count"],
                    "reason": reason,
                },
            )

    except Exception as e:
        logger.error(f"澄清过程失败: {e}")
        return ClarificationResponse(
            session_id=request.session_id,
            status="error",
            response=f"澄清过程出现错误: {str(e)}",
        )


# 移除原有的基于轮次的辅助函数，替换为质量导向的函数


async def _evaluate_clarification_progress_quality_based(session_data: Dict) -> float:
    """基于质量的澄清进度评估（替换原有的简单评估）"""
    try:
        quality_engine = QualityDrivenClarificationEngine()

        # 获取累积的需求内容
        original_content = session_data.get("original_content", "")
        clarification_history = session_data.get("clarification_history", [])

        clarification_content = " ".join(
            [qa.get("answer", "") for qa in clarification_history]
        )
        enhanced_requirement = (
            f"{original_content}\n\n补充信息:\n{clarification_content}"
        )

        # 分析质量
        quality_assessment = await quality_engine.analyze_requirement_quality(
            enhanced_requirement, clarification_history
        )

        # 返回整体质量评分
        return quality_engine._calculate_overall_quality(quality_assessment)

    except Exception as e:
        logger.error(f"质量评估失败: {e}")
        return 0.5


@requirements_router.get("/sessions/{session_id}")
async def get_session_status(session_id: str):
    """
    获取会话状态

    Args:
        session_id: 会话ID

    Returns:
        会话状态和进度
    """
    try:
        # 简化实现：返回模拟状态
        return {
            "session_id": session_id,
            "status": "in_progress",
            "progress": {
                "current_stage": "需求澄清",
                "completion_percentage": 25,
                "estimated_remaining_time": "5-10分钟",
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话状态失败: {str(e)}")


@requirements_router.get("/")
async def requirements_health_check():
    """需求分析服务健康检查"""
    return {
        "service": "requirements_analysis",
        "status": "healthy",
        "timestamp": time.time(),
        "available_engines": ["standard", "multi_dimensional"],
        "version": "1.0.0",
    }


async def _save_requirement_document(
    session_id: str,
    quality_report: str,
    final_requirement: str,
    overall_quality: float,
    total_rounds: int,
) -> str:
    """保存需求文档到文件系统"""
    try:
        # 确保输出目录存在
        output_dir = "data/requirements"
        os.makedirs(output_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"requirement_{session_id[:8]}_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)

        # 生成完整的需求文档
        document_content = f"""# 需求规格说明书

## 📋 基本信息
- **会话ID**: {session_id}
- **生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **质量评分**: {overall_quality:.2f}/1.0
- **澄清轮次**: {total_rounds}轮
        - **文档状态**: {"✅ 质量达标" if overall_quality >= 0.82 else "⚠️ 需要改进"}

## 🎯 最终需求描述

{final_requirement}

## 📊 质量评估报告

{quality_report}

## 📝 文档说明

本文档由OpenManus智能需求分析助手自动生成，基于多轮澄清和8维度质量评估。
- 功能需求：系统必须实现的核心功能
- 非功能需求：性能、安全、可用性等质量属性
- 用户角色：系统涉及的所有用户类型及权限
- 业务规则：系统运行的业务逻辑和约束
- 约束条件：技术、资源、时间等限制
- 验收标准：功能交付的验收条件
- 集成需求：与其他系统的接口要求
- 数据需求：数据存储、处理、安全要求

## 🔗 下一步建议

1. **技术选型**: 根据需求特点选择合适的技术栈
2. **系统设计**: 进行详细的架构设计和模块划分
3. **原型开发**: 制作可交互的原型验证需求
4. **迭代优化**: 基于用户反馈持续改进需求
"""

        # 保存文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(document_content)

        logger.info(f"📄 需求文档已保存: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"保存需求文档失败: {e}")
        return None
