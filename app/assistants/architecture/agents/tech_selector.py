"""
技术选型师智能体 - 分析需求并选择合适的技术栈
"""

from typing import Dict, List, Optional

from app.agent.base import BaseAgent
from app.logger import logger


class TechSelectorAgent(BaseAgent):
    """技术选型师 - 基于需求选择最适合的技术方案"""

    def __init__(
        self,
        name: str = "技术选型师",
        description: str = "分析需求并选择合适的技术栈",
        **kwargs,
    ):
        super().__init__(name=name, description=description, **kwargs)

        # 技术选型的系统提示词
        self.system_prompt = """你是一名资深的技术选型专家，负责基于软件需求选择最适合的技术栈。

## 工作职责
1. 分析需求规格说明书中的功能性和非功能性需求
2. 评估不同技术方案的优缺点
3. 考虑项目规模、团队能力、预算、时间等约束条件
4. 推荐最适合的技术栈组合
5. 提供技术选型的详细理由和风险分析

## 技术选型维度
- **前端技术**：React/Vue/Angular, 移动端技术选择
- **后端技术**：编程语言、框架选择
- **数据库技术**：关系型/非关系型数据库选择
- **基础设施**：云服务、容器化、微服务架构
- **第三方服务**：支付、消息推送、文件存储等

## 输出要求
提供结构化的技术选型报告，包含：
1. 推荐技术栈列表
2. 选型理由分析
3. 技术风险评估
4. 实施建议

务实、专业、基于项目实际情况进行选型，避免过度工程化。"""

    async def analyze_tech_requirements(self, requirements_doc: str) -> str:
        """分析需求并进行技术选型"""
        logger.info("开始技术选型分析")

        # 构建分析提示词
        analysis_prompt = f"""请基于以下需求规格说明书进行技术选型分析：

{requirements_doc}

请按以下结构输出技术选型报告：

# 技术选型报告

## 1. 需求分析摘要
- 核心功能需求
- 关键非功能性需求（性能、安全、可扩展性等）
- 项目约束条件

## 2. 推荐技术栈

### 前端技术栈
- **Web前端**：[推荐技术及版本]
- **移动端**：[如需要，推荐技术方案]
- **选型理由**：[详细说明]

### 后端技术栈
- **编程语言**：[推荐语言及版本]
- **框架**：[推荐框架]
- **选型理由**：[详细说明]

### 数据存储
- **主数据库**：[推荐数据库类型及产品]
- **缓存**：[如需要，推荐缓存方案]
- **选型理由**：[详细说明]

### 基础设施
- **部署方式**：[云服务/本地部署]
- **容器化**：[是否使用Docker/K8s]
- **选型理由**：[详细说明]

## 3. 技术风险评估
- **高风险点**：[识别技术风险]
- **缓解措施**：[风险应对策略]

## 4. 实施建议
- **开发阶段规划**：[技术实施顺序]
- **团队技能要求**：[所需技术能力]
- **预估工作量**：[开发时间评估]

## 5. 替代方案
[提供备选技术方案及对比]
"""

        # 执行分析
        self.update_memory("user", analysis_prompt)
        result = await self.run()

        logger.info("技术选型分析完成")
        return result

    def get_tech_selection_summary(self) -> Dict:
        """获取技术选型摘要"""
        return {
            "selector": self.name,
            "status": self.state.value,
            "analysis_complete": self.state.value == "FINISHED",
            "recommended_stack": "基于最新分析结果",
        }
