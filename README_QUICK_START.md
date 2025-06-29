# OpenManus 快速启动指南

## 🚀 让需求分析助手快速活起来

### 1. API配置选择

当前配置文件(`config/config.toml`)已包含以下选项：

**当前使用：DeepSeek官方API**
```toml
[llm]
model = "deepseek-reasoner"
base_url = "https://api.deepseek.com"
api_key = "sk-824c18bc2f7249bb8847622f7de02957"
```

### 2. 其他API选项

如果您想使用其他LLM提供商，可以修改配置：

#### 选项A: PPIO聚合平台（性价比推荐）
```toml
[llm]
model = "deepseek/deepseek-v3-0324"
base_url = "https://api.ppinfra.com/v3/openai"
api_key = "your_ppio_api_key"
api_type = "ppio"
```

#### 选项B: OpenAI
```toml
[llm]
model = "gpt-4o-mini"
base_url = "https://api.openai.com/v1"
api_key = "your_openai_api_key"
api_type = "openai"
```

#### 选项C: Anthropic Claude
```toml
[llm]
model = "claude-3-7-sonnet-20250219"
base_url = "https://api.anthropic.com/v1"
api_key = "your_anthropic_api_key"
api_type = "anthropic"
```

### 3. 快速启动

1. **启动后端服务**
```bash
cd app
python main.py
```

2. **启动前端服务**
```bash
cd app/web
npm run dev
```

3. **访问系统**
- 前端: http://localhost:5173
- 后端API: http://localhost:8000

### 4. 核心功能验证

#### 4.1 基础需求分析
1. 打开前端页面
2. 在输入框输入：`我想开发一个在线教育平台`
3. 按Ctrl+Enter发送
4. 系统将启动四大智能体协作分析

#### 4.2 知识库功能
1. 访问设置页面：http://localhost:5173/settings
2. 查看预装的知识库（需求分析模板、最佳实践）
3. 可以上传文档或添加代码库

#### 4.3 智能体协作
系统包含四个专业智能体：
- 🔍 **需求澄清师**：澄清模糊需求
- 📊 **业务分析师**：深度业务分析
- 📝 **技术文档师**：编写规格文档
- ✅ **质量评审师**：专业质量把关

### 5. 关键路径说明

**科学的工作流程：**
```
用户输入 → 知识库增强 → 需求澄清 → 业务分析 → 文档编写 → 质量评审
```

**并行处理优化：**
- 预处理阶段：知识库搜索 + 代码分析 并行执行
- 分析阶段：多智能体协作，减少用户等待时间
- 支持串行/并行两种模式切换

### 6. 知识库技术说明

**知识提取技术：**
- **相关性计算**：标题(40%) + 内容(30%) + 标签(20%) + 类型(10%)
- **多维度匹配**：语义匹配 + 关键词匹配 + 模式识别
- **质量保证**：可信度权重 + 使用统计 + 效果反馈

**支持格式：**
- 文档：PDF, DOC, DOCX, TXT, MD, JSON, XML, YAML
- 代码：Python, JavaScript, TypeScript, Java, Go, Rust
- 目录：自动分析代码结构，提取技术模式

**多知识库支持：**
- 需求分析知识库：模板、最佳实践
- 代码模式库：可复用组件、架构模式
- 领域知识库：业务规则、行业标准
- 用户自定义库：上传的文档和代码

### 7. 故障排除

**常见问题：**

1. **API调用失败**
   - 检查API密钥是否正确
   - 确认网络连接正常
   - 查看后端日志：`tail -f app/logs/app.log`

2. **前端无法访问**
   - 确认端口5173未被占用
   - 检查npm依赖：`npm install`

3. **知识库为空**
   - 系统会自动加载默认知识库
   - 可在设置页面手动添加内容

### 8. 性能优化

**并行处理配置：**
```toml
[workflow]
enable_parallel_processing = true  # 启用并行
max_parallel_agents = 4           # 最大并行数
default_timeout = 300             # 超时时间
```

**知识库优化：**
```toml
[knowledge]
default_search_limit = 10         # 搜索结果限制
min_confidence_threshold = 0.5    # 最小可信度
```

---

## 🎯 让助手立即活起来的核心路径

1. ✅ **配置验证**：API密钥已配置
2. ✅ **知识库就绪**：默认知识已加载
3. ✅ **智能体团队**：四大专业角色准备就绪
4. ✅ **并行处理**：优化用户等待体验
5. ✅ **前端界面**：现代化交互体验

**现在就可以开始使用！** 🚀
