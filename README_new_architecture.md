# OpenManus AI软件公司 - 新架构文档

## 🎯 项目愿景

打造真正的AI软件公司，通过五大核心助手实现从需求分析到部署的完整软件开发生命周期自动化。

## 🏗️ 系统架构

### 五大核心助手

1. **需求分析助手** (Requirements Assistant) - 第一期已完成 ✅
2. **架构设计助手** (Architecture Assistant) - 第二期开发
3. **编码开发助手** (Development Assistant) - 第三期开发
4. **系统测试助手** (Testing Assistant) - 第四期开发
5. **部署安装助手** (Deployment Assistant) - 第五期开发

## 📁 目录结构

```
OpenManus/
├── app/
│   ├── assistants/          # 五大助手总目录
│   │   ├── requirements/    # 需求分析助手 ✅
│   │   ├── architecture/    # 架构设计助手
│   │   ├── development/     # 编码开发助手
│   │   ├── testing/         # 系统测试助手
│   │   └── deployment/      # 部署安装助手
│   ├── api/                 # API路由层
│   ├── web/                 # 前端React应用
│   └── [原有模块保持不变]
├── run_web_server.py        # Web服务器启动文件
└── README_new_architecture.md
```

## 🚀 快速开始

### 启动后端服务

```bash
python run_web_server.py
```

---

**OpenManus AI软件公司 - 让AI接管传统软件开发！** 🚀
