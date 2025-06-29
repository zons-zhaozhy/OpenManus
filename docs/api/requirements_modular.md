# 需求分析模块 API 文档

## 概述

需求分析模块提供了一套完整的API，用于进行软件需求的分析、澄清和管理。本模块采用模块化设计，具有良好的可扩展性和可维护性。

## 核心功能

- 需求初始分析
- 智能化需求澄清
- 会话管理
- 工作流控制

## 错误处理

本模块实现了统一的错误处理机制，所有API都会返回标准化的错误响应。

### 错误响应格式

```json
{
    "error": {
        "type": "错误类型",
        "message": "错误消息",
        "status_code": 状态码,
        "details": {
            // 可选的详细错误信息
        }
    }
}
```

### 错误类型

1. 会话相关错误
- `InvalidSessionError` (404): 无效的会话ID
- `SessionExpiredError` (410): 会话已过期

2. 分析相关错误
- `AnalysisError` (500): 分析过程中的一般错误
- `AnalysisTimeoutError` (504): 分析超时
- `InvalidInputError` (400): 无效的输入数据

3. 工作流相关错误
- `WorkflowError` (500): 工作流执行错误

4. 存储相关错误
- `StorageError` (500): 存储操作错误

5. 性能相关错误
- `PerformanceError` (503): 性能问题

## API 详解

### 1. 需求分析 (AnalysisHandler)

#### 分析需求
```python
async def analyze_requirement(request_data: Dict) -> Dict:
```

**参数:**
- request_data:
  - content: str - 需求内容
  - project_id: Optional[str] - 项目ID
  - use_multi_dimensional: Optional[bool] - 是否使用多维度分析（默认True）

**返回:**
```json
{
    "session_id": "uuid",
    "result": {
        "clarity_score": 7.5,
        "clarification_questions": ["问题1", "问题2"]
    },
    "learning_insights": [
        {
            "type": "pattern_recognition",
            "description": "发现常见模式",
            "recommendation": "建议关注..."
        }
    ]
}
```

**错误处理:**
```json
{
    "error": "错误描述"
}
```

### 2. 需求澄清 (ClarificationHandler)

#### 处理澄清回答
```python
async def process_clarification(session_id: str, answer: str, question: Optional[str] = None) -> Dict:
```

**参数:**
- session_id: str - 会话ID
- answer: str - 用户的回答
- question: Optional[str] - 相关的问题

**返回:**
```json
{
    "status": "clarifying",
    "next_questions": ["问题1", "问题2"],
    "learning_insights": [
        {
            "type": "clarity_improvement",
            "description": "明确性提升",
            "recommendation": "建议进一步明确..."
        }
    ]
}
```

### 3. 会话管理 (SessionHandler)

#### 获取会话信息
```python
def get_session_info(session_id: str) -> Dict:
```

**参数:**
- session_id: str - 会话ID

**返回:**
```json
{
    "session_id": "uuid",
    "requirement_text": "需求内容",
    "clarification_history": [],
    "progress": {
        "percentage": 50,
        "current_stage": "澄清中"
    },
    "status": "active"
}
```

#### 获取活动会话列表
```python
def get_active_sessions() -> List[Dict]:
```

**返回:**
```json
[
    {
        "session_id": "uuid",
        "start_time": 1623456789.0,
        "requirement_text": "需求内容...",
        "round_count": 2,
        "quality_score": 0.75,
        "status": "active"
    }
]
```

### 4. 工作流控制 (WorkflowHandler)

#### 生成工作流事件流
```python
async def generate_workflow_stream(session_id: str) -> AsyncGenerator[Dict, None]:
```

**参数:**
- session_id: str - 会话ID

**返回事件示例:**
```json
{
    "event": "分析进行中",
    "progress": 33
}
```

#### 获取工作流状态
```python
def get_workflow_status(session_id: str) -> Dict:
```

**返回:**
```json
{
    "session_id": "uuid",
    "stage": "澄清中",
    "progress": {
        "percentage": 50,
        "current_stage": "澄清中"
    },
    "is_completed": false
}
```

## 使用示例

### 1. 初始需求分析
```python
from app.api.requirements_modular.handlers import AnalysisHandler

# 分析需求
request_data = {
    "content": "需要开发一个在线商城系统",
    "project_id": "ecommerce_001",
    "use_multi_dimensional": True
}

result = await AnalysisHandler.analyze_requirement(request_data)
session_id = result["session_id"]
```

### 2. 处理澄清问题
```python
from app.api.requirements_modular.handlers import ClarificationHandler

# 回答澄清问题
result = await ClarificationHandler.process_clarification(
    session_id=session_id,
    answer="系统需要支持100个并发用户",
    question="系统需要支持多少并发用户？"
)
```

### 3. 监控工作流进度
```python
from app.api.requirements_modular.handlers import WorkflowHandler

# 获取工作流状态
status = WorkflowHandler.get_workflow_status(session_id)

# 订阅工作流事件
async for event in WorkflowHandler.generate_workflow_stream(session_id):
    print(f"进度: {event.get('progress')}%")
```

## 最佳实践

1. 会话管理
   - 及时清理不再使用的会话
   - 定期检查会话状态
   - 处理超时情况

2. 错误处理
   - 始终检查返回结果中的error字段
   - 实现适当的重试机制
   - 记录错误日志

3. 性能优化
   - 使用异步API
   - 合理设置超时
   - 避免过度请求

## 注意事项

1. 会话超时
   - 默认会话超时时间为30分钟
   - 超时后需要重新创建会话

2. 并发限制
   - 单个会话的并发请求数限制为5
   - 超出限制会返回错误

3. 数据限制
   - 需求内容最大长度为10000字符
   - 澄清回答最大长度为1000字符

## 更新日志

### v2.0
- 添加多维度分析支持
- 集成自适应学习系统
- 优化性能控制
- 增强错误处理

### v1.0
- 初始版本发布
- 基本需求分析功能
- 会话管理支持

## 智能体协作机制

### 业务分析智能体（BusinessAnalystAgent）

业务分析智能体负责深入分析需求的业务层面，包括业务流程分析、规则提取、价值评估和风险评估。该智能体通过协作管理器（CollaborationManager）与其他智能体进行协作。

#### 核心功能

1. **业务流程分析**
   - 分析核心业务流程
   - 识别参与者和角色
   - 确定流程步骤和顺序
   - 标识关键决策点
   - 分析数据流转

2. **业务规则提取**
   - 提取业务约束
   - 识别验证规则
   - 确定计算规则
   - 定义数据规则
   - 梳理工作流规则

3. **业务价值评估**
   - 评估直接价值
   - 分析间接价值
   - 预测长期价值
   - 进行ROI分析
   - 评估市场竞争力

4. **风险评估**
   - 识别技术风险
   - 评估业务风险
   - 分析市场风险
   - 预测实施风险
   - 评估维护风险

#### 协作机制

1. **状态管理**
   ```python
   await flow.collaboration_manager.update_state(
       agent_id,
       AgentState.RUNNING,
       task="业务分析",
       progress=0.0
   )
   ```

2. **数据共享**
   ```python
   await flow.collaboration_manager.share_data(
       agent_id,
       "process_analysis",
       process_analysis
   )
   ```

3. **进度跟踪**
   - 业务流程分析: 25%
   - 业务规则提取: 50%
   - 价值评估: 75%
   - 风险评估: 90%
   - 报告生成: 100%

4. **错误处理**
   ```python
   try:
       # 执行分析
   except Exception as e:
       await flow.collaboration_manager.update_state(
           agent_id,
           AgentState.ERROR,
           task="错误"
       )
   ```

#### 使用示例

```python
# 初始化需求分析流程
flow = RequirementsFlow()
analyst = flow.get_agent("analyst")

# 执行业务分析
result = await analyst.analyze(requirement)

# 获取分析结果
process_analysis = flow.collaboration_manager.get_shared_data("process_analysis")
business_rules = flow.collaboration_manager.get_shared_data("business_rules")
value_assessment = flow.collaboration_manager.get_shared_data("value_assessment")
risk_assessment = flow.collaboration_manager.get_shared_data("risk_assessment")
```

#### 测试覆盖

1. **基本流程测试**
   - 验证完整分析流程
   - 检查状态变化
   - 验证数据共享
   - 确认进度更新

2. **错误处理测试**
   - 测试异常情况
   - 验证错误状态
   - 检查错误隔离

3. **协作测试**
   - 测试与需求澄清智能体的协作
   - 验证数据共享机制
   - 检查状态同步

4. **增量分析测试**
   - 测试需求更新场景
   - 验证分析历史记录
   - 检查数据更新

### 协作管理器（CollaborationManager）

协作管理器是智能体协作的核心组件，提供以下功能：

1. **状态管理**
   - 维护智能体状态
   - 跟踪任务进度
   - 记录执行历史

2. **数据共享**
   - 共享分析结果
   - 传递中间数据
   - 管理共享状态

3. **错误处理**
   - 异常捕获和处理
   - 状态恢复
   - 错误隔离

4. **进度跟踪**
   - 实时进度更新
   - 任务状态同步
   - 执行时间监控

## 最佳实践

1. **状态管理**
   - 及时更新智能体状态
   - 准确报告执行进度
   - 妥善处理异常情况

2. **数据共享**
   - 共享必要的分析结果
   - 避免过度共享
   - 及时清理无用数据

3. **错误处理**
   - 实现完整的错误处理
   - 保持错误状态一致性
   - 提供有意义的错误信息

4. **测试覆盖**
   - 编写完整的测试用例
   - 覆盖各种执行场景
   - 验证协作机制

## 注意事项

1. 确保状态更新的及时性和准确性
2. 避免共享过多无关数据
3. 妥善处理并发访问情况
4. 定期清理历史数据
5. 保持错误处理的一致性
