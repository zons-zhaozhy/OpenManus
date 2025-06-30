# OpenManus - AI需求分析助手

> 🎯 **专注需求分析，而非直接编程实现**
> 高仿OpenHands界面，提供专业的需求澄清和分析服务

## ✨ 特性

- 🎨 **高仿OpenHands界面** - 现代化React前端，熟悉的用户体验
- 🔄 **多模式交互** - Web GUI / 交互式CLI / 单次执行
- 🤖 **智能需求分析** - 深度澄清，结构化文档生成
- 🌏 **中文友好** - 英文思考，中文交流
- 📊 **实时状态** - WebSocket通信，状态实时更新
- ⚙️ **灵活配置** - 支持多种LLM提供商

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置API密钥
编辑 `config/config.toml`：
```toml
[llm]
api_key = "your-deepseek-api-key"
model = "deepseek-reasoner"
```

### 启动应用

#### 🖥️ Web界面模式（推荐）
```bash
python main.py
```
访问：http://localhost:3000

#### 💻 交互式CLI模式
```bash
python main.py --mode cli
```

#### ⚡ 单次执行模式
```bash
python main.py --mode once "我想要一个图书管理系统"
```

## 🎯 使用方式

### Web界面使用
1. 打开浏览器访问 http://localhost:3000
2. 在设置页面配置LLM提供商和API密钥
3. 描述您的项目想法
4. 回答系统的澄清问题
5. 获得结构化需求文档

### CLI使用
```bash
$ python main.py --mode cli

🎯 OpenManus 需求分析助手 - CLI模式
========================================================
我将帮助您进行软件需求的深度分析和澄清。

📋 可用命令：
  /help     - 查看帮助信息
  /summary  - 显示对话总结
  /document - 生成需求文档
  /new      - 开始新对话
  /exit     - 退出程序

💬 请输入: 我想要一个图书管理系统

🤔 分析中...

🎯 需求分析助手:
感谢您提出图书管理系统的需求！为了更好地理解您的具体需求，我需要了解一些细节：

1. 请问这是为个人使用、学校图书馆还是公司内部文档管理？
2. 预计需要管理多少册图书？
3. 需要支持多少名用户同时使用？
4. 是否需要借阅和归还功能？
5. 对移动端支持有什么要求？
```

## 🏗️ 架构设计

### 统一入口架构
- **单一入口点** - `main.py` 支持多种运行模式
- **模式切换** - 通过 `--mode` 参数选择交互方式
- **逻辑一致** - 所有模式使用相同的Agent和配置

### 组件结构
```
OpenManus/
├── main.py                    # 统一入口点
├── app/
│   ├── agent/manus.py        # 核心Agent
│   ├── interfaces/           # 界面接口
│   │   ├── cli_interface.py  # CLI交互
│   │   └── web_interface.py  # Web服务
│   ├── tool/
│   │   └── requirements_analyzer.py  # 需求分析工具
│   └── prompt/manus.py       # 系统提示词
├── frontend/
│   └── index.html           # React前端界面
└── config/
    └── config.toml          # 配置文件
```

## ⚙️ 配置选项

### 全局提示词配置
```toml
[global_prompts]
meta_prompt = "你可以用英文思考，但请尽量用中文与用户交流。"
language_preference = "zh_CN"
thinking_language = "en"
response_language = "zh_CN"
global_instructions = [
    "保持专业和友好的语调",
    "当不确定时，主动询问澄清",
    "专注于当前阶段的核心目标：需求分析"
]
```

### LLM配置
```toml
[llm]
api_type = "deepseek"
model = "deepseek-reasoner"
base_url = "https://api.deepseek.com/v1/"
api_key = "your-api-key"
max_tokens = 8192
temperature = 0.0
```

## 🎨 界面特性

### Web界面
- ✅ 类似OpenHands的现代化设计
- ✅ 侧边栏导航（需求分析、设置、新对话）
- ✅ 实时状态指示器
- ✅ 建议问题快速选择
- ✅ 响应式设计，支持移动端
- ✅ 设置页面，支持LLM配置

### 状态指示
- 🟢 **就绪** - 等待用户输入
- 🟡 **思考中** - 正在分析需求
- 🔴 **错误** - 处理出现问题

## 📋 命令参考

### 主命令
```bash
python main.py [options] [prompt]

选项:
  --mode {cli,web,once}    运行模式（默认: web）
  --host HOST             Web模式主机地址（默认: 0.0.0.0）
  --port PORT             Web模式端口号（默认: 3000）
  --verbose               显示详细日志
  -h, --help              显示帮助信息

示例:
  python main.py                                    # Web GUI模式
  python main.py --mode cli                         # 交互式CLI
  python main.py --mode once "电商系统需求"          # 单次执行
  python main.py --mode web --port 8080             # 自定义端口
```

### CLI命令
- `/help` - 查看帮助信息
- `/summary` - 显示对话总结
- `/document` - 生成需求文档
- `/new` - 开始新对话
- `/exit` - 退出程序

## 🔧 开发

### 环境要求
- Python 3.11-3.13
- 有效的DeepSeek API密钥
- 现代浏览器（Web模式）

### 开发模式
```bash
# 启动开发服务器（自动重载）
python main.py --mode web --verbose

# 运行CLI进行调试
python main.py --mode cli --verbose
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

---

## 🆚 与OpenHands的区别

| 特性     | OpenHands       | OpenManus        |
| -------- | --------------- | ---------------- |
| 主要用途 | 代码生成和编程  | 需求分析和澄清   |
| 交互重点 | 直接实现        | 深度分析         |
| 输出结果 | 可运行代码      | 结构化需求文档   |
| 适用阶段 | 开发阶段        | 需求分析阶段     |
| 界面风格 | ✅ 高仿OpenHands | ✅ 现代化专业设计 |

---

🎯 **OpenManus专注于项目前期的需求分析阶段，帮助您充分理解和完善需求，为后续开发奠定坚实基础。**
