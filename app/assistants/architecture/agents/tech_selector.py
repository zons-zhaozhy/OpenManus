"""
技术选型师智能体 - 专业级技术栈分析与选型
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.agent.base import BaseAgent
from app.logger import logger
from app.schema import Message


class TechSelectorAgent(BaseAgent):
    """专业技术选型师 - 基于深度分析选择最适合的技术方案"""

    def __init__(
        self,
        name: str = "资深技术选型师",
        description: str = "基于技术趋势、性能对比、成本效益进行专业技术选型",
        **kwargs,
    ):
        super().__init__(name=name, description=description, **kwargs)

        # 技术知识库 - 2024-2025年技术趋势
        self.tech_trends_2024_2025 = {
            "frontend": {
                "trending": [
                    "React 18+",
                    "Vue 3",
                    "Svelte",
                    "Next.js 14",
                    "Nuxt 3",
                    "Vite",
                ],
                "stable": ["React", "Vue", "Angular", "TypeScript"],
                "declining": ["jQuery", "AngularJS", "Webpack (被Vite替代)"],
                "performance_leaders": ["Svelte", "Vue 3", "React with RSC"],
                "ecosystem_maturity": {
                    "React": 9.5,
                    "Vue": 8.8,
                    "Angular": 8.5,
                    "Svelte": 7.2,
                },
            },
            "backend": {
                "trending": ["Go", "Rust", "Node.js", "Python FastAPI", "Deno", "Bun"],
                "stable": [
                    "Java Spring",
                    "Python Django/Flask",
                    "Node.js Express",
                    ".NET Core",
                ],
                "performance_leaders": ["Rust", "Go", "Java", "C++"],
                "ecosystem_maturity": {
                    "Java": 9.8,
                    "Python": 9.5,
                    "Node.js": 9.2,
                    "Go": 8.5,
                    "Rust": 7.8,
                },
                "ai_integration": ["Python", "JavaScript", "Go", "Rust"],
            },
            "database": {
                "sql_trending": [
                    "PostgreSQL",
                    "MySQL 8+",
                    "CockroachDB",
                    "PlanetScale",
                ],
                "nosql_trending": ["MongoDB", "Redis", "Elasticsearch", "ClickHouse"],
                "performance_db": ["ClickHouse", "PostgreSQL", "Redis", "ScyllaDB"],
                "cloud_native": ["Aurora", "Cloud SQL", "DynamoDB", "CosmosDB"],
            },
            "infrastructure": {
                "trending": ["Kubernetes", "Docker", "Serverless", "Edge Computing"],
                "cloud_leaders": ["AWS", "Azure", "GCP", "Vercel", "Cloudflare"],
                "devops_tools": ["GitHub Actions", "GitLab CI", "Docker", "Terraform"],
            },
        }

        # 性能基准数据 (相对评分 1-10)
        self.performance_benchmarks = {
            "frontend_frameworks": {
                "React": {
                    "bundle_size": 7,
                    "runtime_performance": 8,
                    "memory_usage": 7,
                },
                "Vue": {
                    "bundle_size": 8,
                    "runtime_performance": 8.5,
                    "memory_usage": 8,
                },
                "Svelte": {
                    "bundle_size": 9,
                    "runtime_performance": 9,
                    "memory_usage": 9,
                },
                "Angular": {
                    "bundle_size": 6,
                    "runtime_performance": 7.5,
                    "memory_usage": 6.5,
                },
            },
            "backend_languages": {
                "Go": {
                    "throughput": 9,
                    "latency": 9,
                    "memory_efficiency": 8.5,
                    "cpu_usage": 8.5,
                },
                "Rust": {
                    "throughput": 9.5,
                    "latency": 9.5,
                    "memory_efficiency": 9.5,
                    "cpu_usage": 9,
                },
                "Java": {
                    "throughput": 8.5,
                    "latency": 8,
                    "memory_efficiency": 7,
                    "cpu_usage": 7.5,
                },
                "Python": {
                    "throughput": 6,
                    "latency": 6,
                    "memory_efficiency": 6.5,
                    "cpu_usage": 6,
                },
                "Node.js": {
                    "throughput": 7.5,
                    "latency": 7.5,
                    "memory_efficiency": 7,
                    "cpu_usage": 7.5,
                },
            },
            "databases": {
                "PostgreSQL": {
                    "read_performance": 8.5,
                    "write_performance": 8,
                    "scalability": 8.5,
                },
                "MySQL": {
                    "read_performance": 8,
                    "write_performance": 7.5,
                    "scalability": 8,
                },
                "MongoDB": {
                    "read_performance": 7.5,
                    "write_performance": 8.5,
                    "scalability": 9,
                },
                "Redis": {
                    "read_performance": 10,
                    "write_performance": 9.5,
                    "scalability": 8.5,
                },
            },
        }

        # 成本模型 (1-10, 1=最便宜, 10=最贵)
        self.cost_analysis = {
            "development_cost": {
                "React": 6,
                "Vue": 5,
                "Angular": 7,
                "Svelte": 7,
                "Java": 7,
                "Python": 5,
                "Go": 6,
                "Node.js": 5,
                "Rust": 8,
            },
            "maintenance_cost": {
                "React": 6,
                "Vue": 5,
                "Angular": 8,
                "Java": 6,
                "Python": 5,
                "Go": 4,
                "Rust": 6,
            },
            "hosting_cost": {"serverless": 3, "container": 5, "vm": 7, "bare_metal": 8},
            "talent_acquisition": {  # 人才获取难度
                "JavaScript": 3,
                "Python": 3,
                "Java": 4,
                "Go": 6,
                "Rust": 8,
                "Svelte": 7,
            },
        }

        # 专业系统提示词
        self.system_prompt = """你是一名顶级的技术选型专家，拥有15年以上的大型项目经验，专精于：

## 核心专业能力
1. **技术趋势洞察**：深度理解2024-2025年技术发展趋势，准确预判技术生命周期
2. **性能工程**：基于真实benchmark数据进行量化性能分析和对比
3. **成本效益分析**：全面评估开发成本、运维成本、人才成本、时间成本
4. **风险工程**：识别技术风险、供应商风险、团队风险、时间风险
5. **架构模式**：深度理解微服务、Serverless、边缘计算等现代架构模式

## 分析方法论
### 1. 需求分解
- 功能性需求分析：核心业务逻辑、数据处理量、并发需求
- 非功能性需求量化：性能指标、安全等级、可用性要求
- 约束条件识别：预算上限、时间窗口、团队技能、合规要求

### 2. 技术评估框架
- **技术成熟度评估**：生态完整性、社区活跃度、长期支持
- **性能基准测试**：吞吐量、延迟、资源消耗、扩展性
- **开发效率分析**：学习曲线、开发速度、调试体验、工具链
- **运维复杂度**：部署难度、监控体系、故障排查、扩容方案

### 3. 风险评估模型
- **技术风险**：技术债务、版本迁移、安全漏洞、性能瓶颈
- **团队风险**：技能gap、学习成本、人员流动、培训周期
- **商业风险**：供应商锁定、授权费用、合规风险、市场变化

### 4. 成本优化策略
- **TCO分析**：开发成本、运维成本、人力成本、机会成本
- **ROI评估**：性能收益、开发效率提升、维护成本节约
- **资源配置优化**：CPU/内存使用率、存储成本、网络开销

## 输出标准
1. **量化分析**：所有评估都要有具体数据支撑，避免主观判断
2. **多方案对比**：至少提供2-3个技术方案的详细对比
3. **风险缓解**：每个风险点都要有具体的缓解措施
4. **实施路径**：提供分阶段的技术实施计划和里程碑

## 决策原则
1. **业务优先**：技术服务于业务，不为技术而技术
2. **渐进演进**：支持技术栈的平滑升级和迁移
3. **团队匹配**：充分考虑团队现有技能和学习能力
4. **长期视角**：考虑3-5年的技术发展和维护需求

务实、专业、数据驱动是你的核心特质。"""

    async def analyze_tech_requirements(
        self, requirements_doc: str, project_constraints: Optional[Dict] = None
    ) -> str:
        """专业技术选型分析"""
        logger.info("🔍 开始专业技术选型分析")

        # 解析项目约束
        constraints = project_constraints or {}
        budget = constraints.get("budget", "未指定")
        timeline = constraints.get("timeline", "未指定")
        team_size = constraints.get("team_size", "未指定")
        tech_constraints = constraints.get("technology_constraints", "无特殊约束")

        # 构建专业分析提示词
        analysis_prompt = f"""请对以下项目进行专业的技术选型分析：

## 项目需求文档
{requirements_doc}

## 项目约束条件
- **预算约束**: {budget}
- **时间约束**: {timeline}
- **团队规模**: {team_size}
- **技术约束**: {tech_constraints}
- **分析时间**: {datetime.now().strftime('%Y年%m月')} (请考虑最新技术趋势)

请基于以上信息，运用你的专业知识和分析框架，输出一份详实的技术选型报告。

# 技术选型专业分析报告

## 1. 执行摘要 (Executive Summary)
- **项目类型定位**: [根据需求分析项目类型]
- **技术选型策略**: [保守/平衡/激进]
- **核心技术推荐**: [3-5个关键技术决策]
- **预估技术风险等级**: [低/中/高] 及主要风险点
- **预估开发时间影响**: [相比行业平均水平的时间倍数]

## 2. 需求分析与技术映射

### 2.1 功能性需求分析
- **核心业务功能**: [列出3-5个核心功能模块]
- **数据处理需求**: [数据量级、处理复杂度]
- **用户并发需求**: [预估并发用户数、峰值QPS]
- **集成需求**: [第三方服务、API集成需求]

### 2.2 非功能性需求量化
- **性能要求**: [响应时间≤Xms, 吞吐量≥X QPS]
- **可用性要求**: [SLA要求, 如99.9%]
- **安全等级**: [数据敏感度、合规要求]
- **扩展性要求**: [用户增长预期、数据增长预期]

## 3. 技术栈深度分析

### 3.1 前端技术栈
**主推方案**: [技术栈名称]
- **技术组合**: [具体技术及版本]
- **选型理由**:
  - 生态成熟度: X/10分
  - 开发效率: X/10分
  - 性能表现: X/10分
  - 团队匹配度: X/10分
- **性能基准**: [Bundle大小、首屏加载时间、运行时性能]
- **开发成本**: [学习成本、开发周期、维护成本]

**备选方案**: [备选技术栈及简要对比]

### 3.2 后端技术栈
**主推方案**: [技术栈名称]
- **技术组合**: [编程语言+框架+运行时]
- **性能分析**:
  - 吞吐量: X QPS (benchmark数据)
  - 响应延迟: Xms (P99)
  - 内存效率: X MB/1000请求
  - CPU使用率: X% (负载测试)
- **生态优势**: [框架生态、第三方库、社区支持]
- **开发效率**: [代码简洁度、调试体验、热重载]

**性能对比表**:
| 技术栈 | 吞吐量(QPS) | 延迟(ms) | 内存效率 | 开发效率 | 生态成熟度 |
|--------|-------------|----------|----------|----------|------------|
| [方案A] | X | X | X/10 | X/10 | X/10 |
| [方案B] | X | X | X/10 | X/10 | X/10 |

### 3.3 数据存储方案
**主数据库**: [数据库类型及产品]
- **选型理由**: [数据结构特点、查询模式、一致性要求]
- **性能指标**: [读写QPS、存储容量、查询延迟]
- **扩展策略**: [分库分表、读写分离、集群方案]

**缓存策略**: [缓存技术及架构]
**数据备份**: [备份策略、恢复方案]

### 3.4 基础设施与部署
**部署架构**: [单体/微服务/Serverless]
- **选型理由**: [基于团队规模、系统复杂度、运维能力]
- **容器化策略**: [Docker配置、K8s部署]
- **云服务选择**: [云厂商、服务类型、成本分析]

## 4. 成本效益分析 (TCO Analysis)

### 4.1 开发成本分析
- **人力成本**: [开发人员工资 × 开发周期]
  - 前端开发: X人 × X月 = X万
  - 后端开发: X人 × X月 = X万
  - 测试调优: X人 × X月 = X万
- **学习成本**: [新技术学习时间和培训费用]
- **工具授权成本**: [IDE、云服务、第三方库授权费]

### 4.2 运维成本分析
- **服务器成本**: [云服务器、存储、网络费用/月]
- **运维人力**: [DevOps工程师、监控运维成本]
- **第三方服务**: [CDN、监控、日志服务费用]

### 4.3 总成本对比
| 成本项目 | 方案A | 方案B | 差异分析 |
|----------|-------|-------|----------|
| 开发成本 | X万 | X万 | [差异原因] |
| 第一年运维成本 | X万 | X万 | [差异原因] |
| 三年总成本 | X万 | X万 | [推荐原因] |

## 5. 风险评估与缓解策略

### 5.1 技术风险 (概率 × 影响度)
1. **[风险名称]** - 风险等级: [高/中/低]
   - 风险描述: [具体风险内容]
   - 可能影响: [时间延期X周、成本增加X万]
   - 缓解措施: [具体应对方案]
   - 应急预案: [worst-case scenario的处理]

2. **技术债务风险** - 风险等级: [X]
   - 新技术引入的学习成本和调试复杂度
   - 缓解: 分阶段引入、充分测试、技术预研

3. **性能风险** - 风险等级: [X]
   - 高并发场景下的性能瓶颈
   - 缓解: 性能压测、架构优化、缓存策略

### 5.2 团队风险
- **技能Gap**: [团队当前技能 vs 所需技能的差距]
- **人员风险**: [关键人员离职风险、知识传承]
- **协作风险**: [跨团队协作、沟通成本]

### 5.3 商业风险
- **供应商锁定风险**: [云厂商、第三方服务依赖]
- **授权风险**: [开源协议、商业授权变更]
- **合规风险**: [数据安全、行业监管要求]

## 6. 实施路线图

### 6.1 技术栈引入策略
**阶段1 (第1-2周)**: 基础框架搭建
- [ ] [具体任务1]
- [ ] [具体任务2]

**阶段2 (第3-6周)**: 核心功能开发
- [ ] [具体任务1]
- [ ] [具体任务2]

**阶段3 (第7-8周)**: 性能优化与测试
- [ ] [具体任务1]
- [ ] [具体任务2]

### 6.2 团队技能建设
- **必需技能培训**: [关键技术的培训计划]
- **技术分享计划**: [内部技术分享、最佳实践]
- **外部资源**: [技术咨询、专家指导]

### 6.3 质量保障措施
- **代码质量**: [代码规范、Review流程、静态分析]
- **测试策略**: [单元测试、集成测试、性能测试]
- **监控体系**: [APM监控、日志分析、告警机制]

## 7. 决策建议

### 7.1 推荐方案
基于以上全面分析，推荐采用 **[技术栈组合]**：
- **核心理由**: [3个最重要的理由]
- **适用场景**: [最适合的项目特征]
- **预期收益**: [性能提升X%、开发效率提升X%、成本节约X万]

### 7.2 决策要点
1. **立即决策点**: [需要马上决定的技术选择]
2. **可延迟决策点**: [可以在开发过程中调整的选择]
3. **关键节点**: [技术选型的重要时间节点]

### 7.3 长期技术演进
- **1年内技术升级计划**: [版本升级、功能增强]
- **2-3年技术路线图**: [架构演进、技术栈升级]
- **技术债务管理**: [定期重构、性能优化]

---
**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析师**: 资深技术选型专家 AI
**报告有效期**: 3个月 (考虑技术快速发展)
"""

        # 执行专业分析
        self.update_memory("user", analysis_prompt)
        result = await self.run()

        # 保存分析结果
        self._save_tech_analysis_result(result)

        logger.info("✅ 专业技术选型分析完成")
        return result

    def _save_tech_analysis_result(self, analysis_result: str):
        """保存技术选型分析结果到内存"""
        try:
            # 提取关键技术决策
            tech_stack = self._extract_tech_stack(analysis_result)
            risk_level = self._extract_risk_level(analysis_result)

            self.analysis_summary = {
                "timestamp": datetime.now().isoformat(),
                "recommended_stack": tech_stack,
                "risk_level": risk_level,
                "analysis_quality": "professional",
                "full_report": analysis_result,
            }

        except Exception as e:
            logger.warning(f"保存技术选型结果时出错: {e}")

    def _extract_tech_stack(self, analysis: str) -> Dict:
        """从分析结果中提取推荐的技术栈"""
        try:
            # 简单的正则提取，实际可以用更复杂的NLP
            tech_stack = {
                "frontend": "未识别",
                "backend": "未识别",
                "database": "未识别",
                "infrastructure": "未识别",
            }

            # 提取前端技术
            frontend_match = re.search(
                r"前端.*?(\w+(?:\s+\d+)?)", analysis, re.IGNORECASE
            )
            if frontend_match:
                tech_stack["frontend"] = frontend_match.group(1)

            # 提取后端技术
            backend_match = re.search(
                r"后端.*?(\w+(?:\s+\w+)?)", analysis, re.IGNORECASE
            )
            if backend_match:
                tech_stack["backend"] = backend_match.group(1)

            return tech_stack

        except Exception:
            return {"error": "技术栈提取失败"}

    def _extract_risk_level(self, analysis: str) -> str:
        """提取风险等级"""
        try:
            if "高风险" in analysis or "高" in analysis:
                return "高"
            elif "中风险" in analysis or "中等" in analysis:
                return "中"
            else:
                return "低"
        except Exception:
            return "未知"

    def get_tech_selection_summary(self) -> Dict:
        """获取技术选型摘要"""
        base_summary = {
            "selector": self.name,
            "status": self.state.value,
            "analysis_complete": self.state.value == "FINISHED",
            "analysis_type": "professional_deep_analysis",
        }

        if hasattr(self, "analysis_summary"):
            base_summary.update(self.analysis_summary)

        return base_summary

    async def step(self) -> str:
        """执行单步技术选型分析"""
        try:
            # 检查内存中是否有用户请求
            if not self.memory.messages:
                self.state = self.state.FINISHED
                return "没有技术选型请求"

            # 获取最新的用户消息
            user_message = None
            for msg in reversed(self.memory.messages):
                if msg.role == "user":
                    user_message = msg
                    break

            if not user_message:
                self.state = self.state.FINISHED
                return "没有找到有效的用户请求"

            # 使用LLM进行分析
            messages = []
            if self.system_prompt:
                messages.append(Message.system_message(self.system_prompt))

            # 添加所有相关消息
            messages.extend(self.memory.messages)

            # 调用LLM
            result = await self.llm.ask(messages, stream=False)

            # 更新内存
            self.update_memory("assistant", result)

            # 标记完成
            self.state = self.state.FINISHED

            return result

        except Exception as e:
            logger.error(f"技术选型分析失败: {e}")
            self.state = self.state.ERROR
            return f"分析失败: {str(e)}"

    async def compare_technology_options(
        self, tech_options: List[str], criteria: Dict
    ) -> str:
        """专业技术方案对比分析"""
        logger.info(f"开始对比技术方案: {tech_options}")

        comparison_prompt = f"""请对以下技术方案进行专业对比分析：

## 候选技术方案
{', '.join(tech_options)}

## 对比维度权重
{json.dumps(criteria, indent=2, ensure_ascii=False)}

请从以下维度进行量化对比：
1. **性能表现** (基于benchmark数据)
2. **开发效率** (学习曲线、开发速度)
3. **生态成熟度** (社区、工具链、文档)
4. **运维复杂度** (部署、监控、扩展)
5. **成本分析** (开发成本、运维成本、人才成本)
6. **风险评估** (技术风险、商业风险)

输出格式要求：
- 每个方案给出1-10分的量化评分
- 提供详细的评分理由
- 给出最终推荐及决策建议
"""

        self.update_memory("user", comparison_prompt)
        result = await self.run()

        logger.info("技术方案对比分析完成")
        return result

    def get_performance_benchmark(
        self, tech_name: str, category: str
    ) -> Optional[Dict]:
        """获取技术性能基准数据"""
        try:
            if category in self.performance_benchmarks:
                return self.performance_benchmarks[category].get(tech_name)
            return None
        except Exception as e:
            logger.warning(f"获取性能基准数据失败: {e}")
            return None

    def get_cost_analysis(self, tech_name: str) -> Dict:
        """获取技术成本分析"""
        try:
            costs = {}
            for cost_type, cost_data in self.cost_analysis.items():
                if tech_name in cost_data:
                    costs[cost_type] = cost_data[tech_name]
            return costs
        except Exception as e:
            logger.warning(f"获取成本分析失败: {e}")
            return {}

    def get_tech_trends_insight(self, tech_name: str) -> Dict:
        """获取技术趋势洞察"""
        try:
            insights = {
                "trend_status": "未知",
                "maturity_score": 0,
                "recommendation": "需要进一步分析",
            }

            # 检查各个技术领域
            for domain, domain_data in self.tech_trends_2024_2025.items():
                if tech_name in domain_data.get("trending", []):
                    insights["trend_status"] = "上升趋势"
                elif tech_name in domain_data.get("stable", []):
                    insights["trend_status"] = "稳定"
                elif tech_name in domain_data.get("declining", []):
                    insights["trend_status"] = "下降趋势"

                # 获取生态成熟度评分
                if (
                    "ecosystem_maturity" in domain_data
                    and tech_name in domain_data["ecosystem_maturity"]
                ):
                    insights["maturity_score"] = domain_data["ecosystem_maturity"][
                        tech_name
                    ]

            return insights

        except Exception as e:
            logger.warning(f"获取技术趋势洞察失败: {e}")
            return {"error": str(e)}
