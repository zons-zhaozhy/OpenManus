"""
系统架构师智能体 - 专业级系统架构设计与优化
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.agent.toolcall import ToolCallAgent
from app.logger import logger
from app.schema import Message
from app.tool import ToolCollection
from app.tool.architecture_modeling import ArchitectureModelingTool

# from app.tool.file_operators import FileOperatorTool  # 暂时移除
from app.tool.str_replace_editor import StrReplaceEditor


class SystemArchitectAgent(ToolCallAgent):
    """首席系统架构师 - 基于现代架构模式设计可扩展的系统架构"""

    def __init__(
        self,
        name: str = "首席系统架构师",
        description: str = "基于现代架构模式和最佳实践设计企业级系统架构",
        **kwargs,
    ):
        # 配置架构设计工具集
        tools = ToolCollection()
        tools.add_tool(ArchitectureModelingTool())
        tools.add_tool(StrReplaceEditor())
        # tools.add_tool(FileOperatorTool())  # 暂时移除

        super().__init__(
            name=name,
            description=description,
            available_tools=tools,
            max_steps=15,  # 增加步数支持工具调用
            **kwargs,
        )

        # 现代架构模式知识库
        self.architecture_patterns = {
            "微服务架构": {
                "适用场景": ["大型应用", "团队分工明确", "高可扩展性需求"],
                "优势": ["独立部署", "技术栈灵活", "故障隔离"],
                "劣势": ["复杂性增加", "分布式挑战", "运维成本高"],
                "最佳实践": ["领域驱动设计", "API网关", "服务网格", "熔断器"],
            },
            "分层架构": {
                "适用场景": ["中小型应用", "传统企业应用", "团队技能统一"],
                "优势": ["结构清晰", "开发简单", "易于理解"],
                "劣势": ["耦合度高", "扩展性有限", "性能瓶颈"],
                "最佳实践": ["依赖注入", "接口抽象", "数据传输对象"],
            },
            "事件驱动架构": {
                "适用场景": ["实时性要求高", "异步处理", "松耦合系统"],
                "优势": ["高度解耦", "实时响应", "易于扩展"],
                "劣势": ["复杂性高", "调试困难", "一致性挑战"],
                "最佳实践": ["事件溯源", "CQRS", "消息队列", "幂等性设计"],
            },
            "Serverless架构": {
                "适用场景": ["轻量级应用", "成本敏感", "快速开发"],
                "优势": ["运维成本低", "自动扩展", "按需付费"],
                "劣势": ["冷启动延迟", "供应商锁定", "调试限制"],
                "最佳实践": ["函数拆分", "状态外置", "异步通信"],
            },
        }

        # 性能优化策略库
        self.performance_strategies = {
            "缓存策略": {
                "Redis": "高性能内存缓存，支持数据结构",
                "Memcached": "简单快速的键值缓存",
                "CDN": "静态资源全球分发",
                "数据库缓存": "查询结果缓存，减少数据库负载",
            },
            "数据库优化": {
                "读写分离": "主库写入，从库读取，提升并发能力",
                "分库分表": "水平分割，突破单库性能限制",
                "索引优化": "合理设计索引，提升查询性能",
                "连接池": "复用数据库连接，减少连接开销",
            },
            "架构优化": {
                "负载均衡": "分散请求压力，提高可用性",
                "异步处理": "非阻塞处理，提升系统吞吐量",
                "消息队列": "削峰填谷，提高系统稳定性",
                "API网关": "统一入口，限流、认证、监控",
            },
        }

        # 安全架构框架
        self.security_framework = {
            "认证授权": {
                "JWT": "无状态令牌认证",
                "OAuth2.0": "第三方授权标准",
                "RBAC": "基于角色的访问控制",
                "ABAC": "基于属性的访问控制",
            },
            "数据安全": {
                "传输加密": "HTTPS/TLS加密传输",
                "存储加密": "敏感数据加密存储",
                "脱敏处理": "日志和展示数据脱敏",
                "备份加密": "数据备份加密保护",
            },
            "防护机制": {
                "SQL注入防护": "参数化查询，输入验证",
                "XSS防护": "输出编码，CSP策略",
                "CSRF防护": "Token验证，同源检查",
                "DDoS防护": "流量限制，异常检测",
            },
        }

        # 专业系统架构师提示词
        self.system_prompt = """你是一名拥有20年经验的首席系统架构师，专精于现代企业级系统架构设计，擅长：

## 核心专业能力
1. **架构模式精通**：深度理解微服务、分层、事件驱动、Serverless等现代架构模式
2. **性能工程**：基于真实负载设计高性能、可扩展的系统架构
3. **安全架构**：设计纵深防御的安全体系，保障系统和数据安全
4. **云原生设计**：基于容器、K8s、云服务的现代化架构设计
5. **领域建模**：运用DDD方法进行业务领域分析和架构设计

## 设计方法论
### 1. 架构决策框架
- **业务驱动**：架构服务于业务目标，不为技术而技术
- **演进式设计**：支持架构的平滑演进和技术债务管理
- **约束导向**：在技术、成本、时间约束下做最优设计
- **数据驱动**：基于性能数据和业务指标进行架构决策

### 2. 质量属性权衡
- **性能 vs 复杂性**：在性能需求和系统复杂性间找平衡
- **可扩展性 vs 成本**：平衡扩展能力和建设运维成本
- **安全性 vs 易用性**：在安全要求和用户体验间权衡
- **一致性 vs 可用性**：根据CAP定理进行合理取舍

### 3. 风险管控
- **技术风险**：新技术引入、性能瓶颈、单点故障
- **业务风险**：需求变更、扩展性不足、数据丢失
- **运维风险**：部署复杂、监控盲点、故障恢复

## 现代架构最佳实践
### 微服务架构
- **服务拆分原则**：按业务能力和数据边界拆分
- **服务治理**：API网关、服务注册发现、配置中心
- **数据管理**：每个服务独立数据库，事件驱动数据一致性
- **运维自动化**：CI/CD、容器化、服务网格

### 云原生设计
- **容器化**：Docker镜像、不可变基础设施
- **编排管理**：Kubernetes集群管理和自动扩缩容
- **服务网格**：Istio/Linkerd流量管理和安全通信
- **可观测性**：分布式链路追踪、指标监控、日志聚合

### 性能架构
- **缓存体系**：多级缓存，Redis集群，CDN分发
- **数据库优化**：读写分离、分库分表、索引优化
- **异步处理**：消息队列、事件驱动、流处理
- **负载均衡**：多层负载均衡、健康检查、故障转移

### 安全架构
- **零信任模型**：永远验证，从不信任，最小权限
- **深度防御**：多层安全机制，纵深防护
- **数据保护**：加密传输、加密存储、脱敏处理
- **威胁建模**：识别威胁，评估风险，设计对策

## 输出标准
1. **业务对齐**：架构设计完全对应业务需求和发展规划
2. **技术前瞻**：采用成熟稳定的技术，保留演进空间
3. **量化设计**：所有架构决策都有性能、成本、风险的量化分析
4. **实施可行**：提供详细的实施路径和里程碑规划
5. **质量保障**：内建质量属性，支持测试、监控、运维

## 架构交付物
1. **架构总览图**：系统全貌、核心组件、数据流向
2. **模块设计图**：详细模块拆分、接口定义、依赖关系
3. **部署架构图**：环境规划、容器编排、网络拓扑
4. **技术选型说明**：架构相关的技术决策和选型理由
5. **性能设计**：性能目标、优化策略、瓶颈预测
6. **安全设计**：安全机制、威胁应对、合规保障
7. **运维设计**：监控体系、故障处理、扩容策略

专业、务实、前瞻是你的核心特质。"""

    async def design_system_architecture(
        self,
        requirements_doc: str,
        tech_stack: str,
        project_constraints: Optional[Dict] = None,
    ) -> str:
        """专业系统架构设计"""
        logger.info("🏗️ 开始专业系统架构设计")

        # 解析项目约束
        constraints = project_constraints or {}
        budget = constraints.get("budget", "未指定")
        timeline = constraints.get("timeline", "未指定")
        team_size = constraints.get("team_size", "未指定")
        performance_requirements = constraints.get(
            "performance_requirements", "标准性能要求"
        )

        # 构建专业架构设计提示词
        design_prompt = f"""请基于以下信息进行企业级系统架构设计：

## 项目输入
### 需求规格说明书
{requirements_doc}

### 技术选型报告
{tech_stack}

### 项目约束条件
- **预算约束**: {budget}
- **时间约束**: {timeline}
- **团队规模**: {team_size}
- **性能要求**: {performance_requirements}
- **设计时间**: {datetime.now().strftime('%Y年%m月')} (请考虑最新架构趋势)

请运用你的专业知识和架构最佳实践，输出一份详实的系统架构设计文档。

# 企业级系统架构设计文档

## 1. 架构执行摘要
- **系统类型定位**: [根据需求分析确定系统类型]
- **架构策略选择**: [单体/微服务/混合，并说明选择理由]
- **核心架构决策**: [3-5个关键架构决策]
- **预估系统复杂度**: [低/中/高] 及复杂度来源
- **架构风险等级**: [低/中/高] 及主要风险点

## 2. 业务架构分析

### 2.1 业务域分解
- **核心业务域**: [识别3-5个核心业务域]
- **支撑业务域**: [识别支撑业务域]
- **业务流程**: [关键业务流程分析]
- **业务规则**: [重要业务规则识别]

### 2.2 领域模型设计
- **聚合根设计**: [核心业务实体]
- **值对象**: [业务概念抽象]
- **领域服务**: [业务逻辑封装]
- **领域边界**: [上下文边界划分]

## 3. 应用架构设计

### 3.1 架构风格选择
**选定架构**: [具体架构风格]
- **选择理由**: [基于项目特征的选择依据]
- **架构优势**: [对本项目的具体优势]
- **架构风险**: [需要关注的架构风险]
- **替代方案**: [备选架构方案]

### 3.2 系统分层设计
**表现层 (Presentation Layer)**
- **Web前端**: [前端架构设计]
- **移动端**: [如有需要]
- **API网关**: [统一入口设计]
- **负载均衡**: [流量分发策略]

**应用层 (Application Layer)**
- **应用服务**: [业务用例协调]
- **工作流引擎**: [如需要]
- **任务调度**: [定时任务设计]
- **事件处理**: [事件驱动架构]

**领域层 (Domain Layer)**
- **领域服务**: [核心业务逻辑]
- **领域模型**: [业务实体设计]
- **业务规则**: [规则引擎设计]
- **领域事件**: [业务事件定义]

**基础设施层 (Infrastructure Layer)**
- **数据持久化**: [数据访问设计]
- **外部服务**: [第三方集成]
- **消息中间件**: [异步通信]
- **缓存服务**: [缓存策略设计]

### 3.3 模块划分与依赖关系
**核心模块列表**:
| 模块名称 | 主要职责 | 依赖关系 | 接口定义 |
|----------|----------|----------|----------|
| [模块A] | [职责描述] | [依赖模块] | [关键接口] |
| [模块B] | [职责描述] | [依赖模块] | [关键接口] |

**模块交互图**:
```
[用ASCII绘制模块依赖关系]
┌──────────┐    ┌──────────┐
│  前端应用  │────│ API网关  │
└──────────┘    └─────┬────┘
                      │
               ┌──────┴──────┐
               │   业务服务   │
               └──────┬──────┘
                      │
               ┌──────┴──────┐
               │   数据服务   │
               └─────────────┘
```

## 4. 技术架构设计

### 4.1 技术栈映射
**前端技术栈**:
- **框架选择**: [基于技术选型的具体框架]
- **状态管理**: [状态管理方案]
- **构建工具**: [构建和打包工具]
- **UI组件库**: [UI框架选择]

**后端技术栈**:
- **开发框架**: [后端框架选择]
- **API设计**: [RESTful/GraphQL]
- **数据访问**: [ORM/查询构建器]
- **测试框架**: [单元测试/集成测试]

**数据存储**:
- **主数据库**: [主数据库选择和配置]
- **缓存系统**: [缓存架构设计]
- **消息队列**: [异步处理方案]
- **文件存储**: [文件管理方案]

### 4.2 集成架构
**API设计**:
- **API风格**: [RESTful/GraphQL设计原则]
- **版本管理**: [API版本控制策略]
- **文档规范**: [API文档和测试]
- **限流策略**: [流量控制和防护]

**数据集成**:
- **数据同步**: [数据一致性保障]
- **ETL流程**: [数据处理流程]
- **数据质量**: [数据验证和清洗]
- **备份恢复**: [数据保护策略]

## 5. 部署架构设计

### 5.1 环境规划
**环境分离**:
- **开发环境**: [开发环境配置]
- **测试环境**: [测试环境设计]
- **预生产环境**: [预发布环境]
- **生产环境**: [生产环境架构]

### 5.2 容器化设计
**Docker化策略**:
- **镜像设计**: [Docker镜像构建策略]
- **容器编排**: [K8s/Docker Compose]
- **服务发现**: [服务注册和发现]
- **配置管理**: [环境配置外化]

**部署拓扑**:
```
[生产环境部署图]
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   负载均衡   │  │   Web服务   │  │  API服务   │
│    (LB)     │  │  (Frontend) │  │ (Backend)   │
└─────────────┘  └─────────────┘  └─────────────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
              ┌─────────┴─────────┐
              │     数据库集群     │
              │    (Master/Slave) │
              └───────────────────┘
```

## 6. 性能架构设计

### 6.1 性能目标设定
| 性能指标 | 目标值 | 监控方法 | 优化策略 |
|----------|--------|----------|----------|
| 响应时间 | ≤300ms | APM监控 | 缓存优化 |
| 吞吐量 | ≥1000 QPS | 压力测试 | 负载均衡 |
| 并发用户 | ≥5000 | 用户监控 | 水平扩展 |
| 可用性 | ≥99.9% | 健康检查 | 故障转移 |

### 6.2 性能优化策略
**缓存架构**:
- **L1缓存**: [应用内存缓存]
- **L2缓存**: [分布式缓存Redis]
- **L3缓存**: [CDN内容分发]
- **缓存策略**: [失效策略和一致性]

**数据库优化**:
- **索引设计**: [查询优化索引]
- **读写分离**: [读写负载分离]
- **分库分表**: [水平扩展策略]
- **连接池**: [连接资源管理]

**异步处理**:
- **消息队列**: [异步任务处理]
- **事件驱动**: [事件处理机制]
- **批处理**: [大量数据处理]
- **流处理**: [实时数据处理]

## 7. 安全架构设计

### 7.1 安全威胁模型
**威胁识别**:
- **认证威胁**: [身份伪造、密码破解]
- **授权威胁**: [权限提升、越权访问]
- **数据威胁**: [数据泄露、数据篡改]
- **网络威胁**: [DDoS攻击、中间人攻击]

### 7.2 安全防护机制
**认证授权**:
- **认证方案**: [JWT/OAuth2.0]
- **权限模型**: [RBAC/ABAC]
- **会话管理**: [会话安全策略]
- **多因素认证**: [2FA/MFA支持]

**数据保护**:
- **传输加密**: [HTTPS/TLS配置]
- **存储加密**: [敏感数据加密]
- **脱敏处理**: [数据脱敏策略]
- **访问审计**: [操作日志记录]

**网络安全**:
- **防火墙**: [网络访问控制]
- **WAF防护**: [Web应用防火墙]
- **DDoS防护**: [流量清洗]
- **安全扫描**: [漏洞扫描和修复]

## 8. 可观测性设计

### 8.1 监控体系
**指标监控**:
- **业务指标**: [用户活跃度、交易量等]
- **技术指标**: [CPU、内存、网络等]
- **性能指标**: [响应时间、吞吐量等]
- **错误指标**: [错误率、异常统计]

**日志管理**:
- **日志收集**: [ELK/EFK技术栈]
- **日志分析**: [日志分析和告警]
- **日志存储**: [日志保留策略]
- **日志安全**: [日志脱敏和审计]

**链路追踪**:
- **分布式追踪**: [Jaeger/Zipkin]
- **调用链分析**: [性能瓶颈识别]
- **错误追踪**: [异常链路分析]
- **依赖分析**: [服务依赖关系]

### 8.2 告警机制
- **告警规则**: [阈值设定和告警条件]
- **告警渠道**: [邮件、短信、钉钉等]
- **告警升级**: [告警升级机制]
- **故障自愈**: [自动恢复机制]

## 9. 质量保障体系

### 9.1 架构质量属性
| 质量属性 | 目标值 | 设计策略 | 验证方法 |
|----------|--------|----------|----------|
| 可维护性 | ≥8/10 | 模块化设计 | 代码质量审查 |
| 可扩展性 | ≥8/10 | 松耦合架构 | 扩展性测试 |
| 可用性 | ≥99.9% | 冗余设计 | 可用性测试 |
| 安全性 | ≥9/10 | 安全架构 | 安全测试 |

### 9.2 质量保障措施
**代码质量**:
- **编码规范**: [统一编码标准]
- **代码审查**: [Code Review流程]
- **静态分析**: [代码质量检测]
- **测试覆盖**: [单元测试覆盖率]

**架构治理**:
- **架构评审**: [架构决策评审]
- **技术债务**: [技术债务管理]
- **架构演进**: [架构升级规划]
- **最佳实践**: [架构最佳实践推广]

## 10. 实施路线图

### 10.1 分阶段实施
**第一阶段 (第1-4周)**: 基础架构搭建
- [ ] 技术栈环境搭建
- [ ] 基础框架配置
- [ ] 核心模块骨架
- [ ] CI/CD流水线

**第二阶段 (第5-8周)**: 核心功能实现
- [ ] 用户认证授权
- [ ] 核心业务逻辑
- [ ] 数据访问层
- [ ] API接口开发

**第三阶段 (第9-12周)**: 完善与优化
- [ ] 性能优化
- [ ] 安全加固
- [ ] 监控告警
- [ ] 测试完善

### 10.2 关键里程碑
- **架构原型验证**: [第2周]
- **核心功能演示**: [第6周]
- **性能基准测试**: [第10周]
- **安全评估完成**: [第11周]
- **上线准备就绪**: [第12周]

### 10.3 风险管控
- **技术风险**: [新技术学习曲线、性能不达标]
- **进度风险**: [需求变更、开发延期]
- **质量风险**: [测试不充分、Bug率高]
- **团队风险**: [人员流动、技能不匹配]

## 11. 投资回报分析

### 11.1 架构价值评估
- **开发效率提升**: [预计提升X%的开发效率]
- **运维成本节约**: [自动化运维减少X%成本]
- **系统稳定性**: [故障率降低X%，可用性提升]
- **扩展性收益**: [支持X倍业务增长无需重构]

### 11.2 技术债务管理
- **当前技术债务**: [识别现有技术债务]
- **新增债务控制**: [债务预防措施]
- **债务偿还计划**: [分阶段债务清理]
- **债务监控**: [技术债务跟踪指标]

---
**文档版本**: v1.0
**设计时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**架构师**: 首席系统架构师 AI
**审核状态**: 待评审
**有效期**: 6个月 (建议定期更新)
"""

        # 执行专业架构设计
        self.update_memory("user", design_prompt)
        result = await self.run()

        # 保存架构设计结果
        self._save_architecture_result(result)

        logger.info("✅ 专业系统架构设计完成")
        return result

    def _save_architecture_result(self, architecture_result: str):
        """保存架构设计结果到内存"""
        try:
            # 提取关键架构决策
            architecture_style = self._extract_architecture_style(architecture_result)
            complexity_level = self._extract_complexity_level(architecture_result)

            self.architecture_summary = {
                "timestamp": datetime.now().isoformat(),
                "architecture_style": architecture_style,
                "complexity_level": complexity_level,
                "design_quality": "professional",
                "full_design": architecture_result,
            }

        except Exception as e:
            logger.warning(f"保存架构设计结果时出错: {e}")

    def _extract_architecture_style(self, design: str) -> str:
        """从设计结果中提取架构风格"""
        try:
            # 检查常见架构模式
            if "微服务" in design:
                return "微服务架构"
            elif "分层" in design:
                return "分层架构"
            elif "事件驱动" in design:
                return "事件驱动架构"
            elif "Serverless" in design:
                return "Serverless架构"
            else:
                return "混合架构"
        except Exception:
            return "未识别"

    def _extract_complexity_level(self, design: str) -> str:
        """提取系统复杂度等级"""
        try:
            if "高复杂度" in design or "复杂" in design:
                return "高"
            elif "中复杂度" in design or "中等" in design:
                return "中"
            else:
                return "低"
        except Exception:
            return "未知"

    async def step(self) -> str:
        """执行单步架构设计"""
        try:
            # 检查内存中是否有用户请求
            if not self.memory.messages:
                self.state = self.state.FINISHED
                return "没有架构设计请求"

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
            logger.error(f"系统架构设计失败: {e}")
            self.state = self.state.ERROR
            return f"设计失败: {str(e)}"

    def get_architecture_summary(self) -> Dict:
        """获取架构设计摘要"""
        base_summary = {
            "architect": self.name,
            "status": self.state.value,
            "design_complete": self.state.value == "FINISHED",
            "design_type": "enterprise_level_architecture",
        }

        if hasattr(self, "architecture_summary"):
            base_summary.update(self.architecture_summary)

        return base_summary

    def get_architecture_pattern_info(self, pattern_name: str) -> Optional[Dict]:
        """获取架构模式信息"""
        return self.architecture_patterns.get(pattern_name)

    def get_performance_strategy(self, category: str) -> Optional[Dict]:
        """获取性能优化策略"""
        return self.performance_strategies.get(category)

    def get_security_framework_info(self, category: str) -> Optional[Dict]:
        """获取安全架构框架信息"""
        return self.security_framework.get(category)

    async def evaluate_architecture_quality(self, architecture_design: str) -> Dict:
        """评估架构设计质量"""
        logger.info("开始架构质量评估")

        evaluation_prompt = f"""请对以下架构设计进行专业评估：

{architecture_design}

请从以下维度进行评估(1-10分)：
1. **业务对齐度**: 架构是否完全满足业务需求
2. **技术先进性**: 技术选择是否合理且具前瞻性
3. **可扩展性**: 架构的扩展能力和适应性
4. **可维护性**: 架构的可维护和可理解程度
5. **安全性**: 安全架构的完整性和有效性
6. **性能设计**: 性能优化策略的合理性
7. **实施可行性**: 实施的难度和可行性

输出格式：
- 各维度评分及理由
- 整体评分
- 主要优势
- 改进建议
- 风险提醒
"""

        self.update_memory("user", evaluation_prompt)
        result = await self.run()

        logger.info("架构质量评估完成")
        return {
            "evaluation_result": result,
            "evaluation_time": datetime.now().isoformat(),
            "evaluator": self.name,
        }
