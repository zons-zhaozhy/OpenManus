# OpenManus 保守重构策略

## 🎯 核心原则

### 1. 保护现有优秀架构
- ✅ **完全保留** `app/assistants/` 目录的多智能体架构
- ✅ **完全保留** BaseFlow + BaseAgent 设计模式
- ✅ **完全保留** Think-Act-Reflect 核心逻辑
- ✅ **充分复用** 现有的知识库、代码分析、上下文管理等组件

### 2. 渐进式改进目标
- 🎯 **仅重构API层**：将`app/api/requirements.py` (2143行) 拆分成职责清晰的模块
- 🎯 **前端组件化**：拆分`RequirementsPage.tsx`，但保持API兼容性
- 🎯 **适度规范化**：建立实用的编码规范，避免过度严苛

## 📋 具体重构计划

### 阶段1：API层模块化（保持功能完全一致）
```
app/api/requirements/
├── __init__.py           # 主入口，保持现有API接口
├── routes/
│   ├── analysis.py       # /analyze 相关路由
│   ├── clarification.py  # /clarify 相关路由
│   ├── workflow.py       # /workflow 相关路由
│   └── session.py        # session管理路由
├── handlers/
│   ├── analysis_handler.py    # 分析业务逻辑
│   ├── clarification_handler.py # 澄清业务逻辑
│   └── workflow_handler.py     # 工作流业务逻辑
└── utils/
    ├── response_builder.py     # 响应构建工具
    ├── validation.py           # 数据验证
    └── extraction.py           # 数据提取工具
```

### 阶段2：前端组件化（保持功能完全一致）
```
components/RequirementsPage/
├── RequirementsPage.tsx        # 主组件(50行内)
├── hooks/
│   ├── useRequirementsAPI.ts   # API调用逻辑
│   ├── useAnalysisState.ts     # 分析状态管理
│   └── useClarificationFlow.ts # 澄清流程管理
├── components/
│   ├── AnalysisPanel.tsx       # 分析结果展示
│   ├── ClarificationPanel.tsx  # 澄清问答界面
│   ├── ProgressIndicator.tsx   # 进度指示器
│   └── ResultViewer.tsx        # 结果查看器
└── context/
    └── RequirementsContext.tsx # 状态共享
```

### 阶段3：编码规范优化
- 文件大小建议（非强制）：Python ≤ 500行，React ≤ 400行
- 职责清晰：一个文件一个主要职责
- 适度重构：只在明显问题时触发重构

## ⚠️ 重构红线

### 绝对不能改动的部分
1. `app/assistants/requirements/flow.py` - 核心多智能体流程
2. `app/assistants/requirements/agents/` - 智能体实现
3. `app/flow/base.py` - BaseFlow基础架构
4. `app/agent/base.py` - BaseAgent基础架构
5. 现有API接口定义和响应格式

### 改动前必须确认
1. 是否有现成的实现可以复用？
2. 是否会破坏现有的API兼容性？
3. 是否真的有必要创建新文件？
4. 是否充分理解了现有代码的设计意图？

## 🔄 验证机制

### 重构前检查清单
- [ ] 理解现有实现的完整逻辑
- [ ] 确认没有重复造轮子
- [ ] 保证API接口完全兼容
- [ ] 验证现有测试仍然通过
- [ ] 确认性能不会退化

### 成功标准
- 代码更容易维护
- 职责更加清晰
- **功能完全一致**
- **性能不下降**
- **API向后兼容**

## 💡 实施原则

1. **理解优先**：充分理解现有实现再动手
2. **复用优先**：优先使用现有组件和架构
3. **兼容优先**：保证向后兼容，不破坏现有功能
4. **渐进优先**：小步快跑，避免大规模重写
5. **验证优先**：每一步都要验证功能正确性
