### 实施计划：交互式需求工程流程

#### 1. 核心架构设计

-   **后端 (FastAPI):**
    -   `InteractiveFlowManager`: 一个新的服务，负责创建和管理每个用户会话的交互式流程。
    -   `WebSocket` 端点: 在 FastAPI 中增加 `/ws/requirements/{session_id}` 端点，用于处理与前端的实时双向通信。
    -   `EventPublisher`: 一个事件发布器，负责将后端流程中的关键事件（如任务开始、生成日志、任务结束）通过 WebSocket 推送给前端。
    -   异步 Agent: 将现有的分析服务改造为异步 Agent（`ClarificationAgent`, `AnalysisAgent`, `DocumentationAgent`），并由 `InteractiveFlowManager` 编排调用。
    -   状态持久化: 扩展现有的 `SQLiteStorage`，增加对长流程会话状态的存储和恢复功能，以应对连接中断等异常情况。

-   **前端 (React + Ant Design):**
    -   `AnalysisPage`: 新建一个主页面，作为用户与需求分析助手交互的界面。
    -   `WebSocketService`: 一个专门处理 WebSocket 连接、消息收发的服务。
    -   `LogView` 组件: 实时显示后端推送的日志和进度信息，模仿 OpenHands 的风格。
    -   `StatusIndicator` 组件: 清晰地展示当前流程处于哪个阶段（如：澄清中、分析中、生成文档中）。

-   **通信协议 (JSON):**
    -   定义一套标准化的事件格式，用于前后端通信。

#### 2. 分阶段实施计划

**阶段一：后端核心流程与通信搭建 (预计2天)**
1.  创建 `InteractiveFlowManager`: 在 `app/flow/` 目录下创建 `interactive_flow.py`，定义核心流程管理逻辑。
2.  实现 `WebSocketEventPublisher`: 创建一个具体的事件发布器实现，用于通过 WebSocket 发送消息。
3.  添加 WebSocket 端点: 在 `main.py` 或相关路由文件中，集成 FastAPI 的 WebSocket 端点。
4.  改造 `RequirementAnalyzer`: 将其改造为异步服务，并在关键步骤通过 `EventPublisher` 发布进度事件。

**阶段二：前端原型开发与对接 (预计2天)**
1.  初始化前端项目: 在 `frontend/requirements-analyzer/` 目录下，使用 `create-react-app` 快速搭建项目。
2.  开发核心组件: 实现 `AnalysisPage`, `LogView` 和 `WebSocketService`。
3.  实现前后端连接: 让前端能够成功连接到后端的 WebSocket 端点，并能实时显示后端发送的事件。

**阶段三：端到端功能集成 (预计3天)**
1.  实现 `DocumentationAgent`: 开发一个新的 Agent，负责调用 LLM 将结构化的分析结果转换成格式化的 Markdown 文档。
2.  集成完整流程: 在 `InteractiveFlowManager` 中，将 `ClarificationAgent` -> `AnalysisAgent` -> `DocumentationAgent` 的流程完整串联起来。
3.  实现文档展示: 在前端增加文档预览或下载功能。

**阶段四：健壮性与体验优化 (预计2天)**
1.  实现状态持久化: 扩展 `SQLiteStorage`，确保 `InteractiveFlowManager` 的状态可以被保存和恢复。
2.  优化 LLM 调用: 对 LLM 的调用采用流式（Streaming）API，以减少前端等待时间。
3.  完善错误处理与重连: 增加 WebSocket 的自动重连机制和后端的异常处理逻辑。
4.  前端体验对标: 优化 `LogView` 的样式和交互，使其更接近 OpenHands 的用户体验。

#### 3. 潜在风险与应对策略

-   **长连接稳定性**: 后端实现状态持久化，前端实现自动重连和会话恢复机制。
-   **LLM 响应延迟**: 后端采用异步处理和流式 API，并持续向前端发送心跳或进度更新事件。
-   **状态同步复杂性**: 设计幂等的事件协议，并对关键状态变更进行确认。
