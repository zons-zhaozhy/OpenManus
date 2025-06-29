# OpenManus 模块化重构计划

## 🎯 重构目标

解决当前系统中的模块化问题，实现单一职责、组件化、模块化的系统架构。

## 🚨 当前问题

### 超大文件问题
- `app/api/requirements.py` (2142行) - 包含路由、业务逻辑、数据模型等多重职责
- `app/core/quality_driven_clarification_engine.py` (1543行) - 功能过于集中
- `app/web/src/pages/RequirementsPage.tsx` (1313行) - UI逻辑、状态管理、业务逻辑混合
- `app/llm.py` (852行) - LLM接口、配置、工具等职责混合

### 职责混乱
1. API层与业务逻辑耦合
2. 前端组件职责不清
3. 工具函数分散
4. 数据模型定义重复

## 📋 重构计划

### 阶段一：API层重构 (已开始)

#### ✅ 已完成
- [x] 创建 `app/api/requirements/models/` 模块
- [x] 提取请求/响应模型到独立文件
- [x] 创建分类工具模块

#### 🔄 进行中
- [ ] 拆分路由文件
  - [ ] `routes/analysis.py` - 分析相关路由
  - [ ] `routes/clarification.py` - 澄清相关路由
  - [ ] `routes/workflow.py` - 工作流程路由
  - [ ] `routes/session.py` - 会话管理路由

#### 📝 待完成
- [ ] 创建服务层
  - [ ] `services/analysis_service.py`
  - [ ] `services/clarification_service.py`
  - [ ] `services/document_service.py`
  - [ ] `services/session_service.py`

### 阶段二：前端组件重构

#### 目标结构
```
app/web/src/
├── pages/
│   └── RequirementsPage.tsx (减少到 < 400行)
├── components/requirements/
│   ├── RequirementInput.tsx
│   ├── AnalysisProgress.tsx
│   ├── ClarificationPanel.tsx
│   ├── ResultDisplay.tsx
│   └── SessionManager.tsx
├── hooks/
│   ├── useRequirementAnalysis.ts
│   ├── useClarification.ts
│   └── useSession.ts
└── services/
    ├── api.ts
    └── requirements.ts
```

### 阶段三：核心引擎重构

#### 质量驱动澄清引擎拆分
```
app/core/clarification/
├── __init__.py
├── engine.py (< 400行)
├── quality_assessor.py
├── question_generator.py
└── progress_tracker.py
```

#### LLM模块重构
```
app/llm/
├── __init__.py
├── client.py
├── config.py
├── tools.py
└── utils.py
```

### 阶段四：工具和配置重构

#### 工具函数重组
```
app/utils/
├── text_processing.py
├── file_operations.py
├── validation.py
└── formatting.py
```

## 🎯 重构原则

1. **单一职责原则** - 每个模块只负责一个功能
2. **依赖倒置** - 高层模块不依赖低层模块
3. **接口隔离** - 客户端不应该依赖它不需要的接口
4. **开闭原则** - 对扩展开放，对修改关闭

## 📊 成功指标

- [ ] 单个文件行数 < 400行
- [ ] 模块职责清晰，依赖关系明确
- [ ] 代码重复率 < 5%
- [ ] 测试覆盖率 > 80%
- [ ] API响应时间不变
- [ ] 前端页面加载性能提升

## ⚡ 执行顺序

1. **第一优先级**: API层重构 (影响最大，风险可控)
2. **第二优先级**: 前端组件重构 (提升用户体验)
3. **第三优先级**: 核心引擎重构 (技术债务清理)
4. **第四优先级**: 工具配置重构 (代码质量提升)

## 🔒 风险控制

- 保持向后兼容性
- 渐进式重构，避免大爆炸式改动
- 每个阶段完成后进行充分测试
- 保留原文件作为备份直到验证完成
