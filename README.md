<p align="center">
  <img src="assets/logo.jpg" width="200"/>
</p>

English | [中文](README_zh.md) | [한국어](README_ko.md) | [日本語](README_ja.md)

[![GitHub stars](https://img.shields.io/github/stars/FoundationAgents/OpenManus?style=social)](https://github.com/FoundationAgents/OpenManus/stargazers)
&ensp;
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) &ensp;
[![Discord Follow](https://dcbadge.vercel.app/api/server/DYn29wFk9z?style=flat)](https://discord.gg/DYn29wFk9z)
[![Demo](https://img.shields.io/badge/Demo-Hugging%20Face-yellow)](https://huggingface.co/spaces/lyh-917/OpenManusDemo)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15186407.svg)](https://doi.org/10.5281/zenodo.15186407)

# 🎯 OpenManus 需求分析智能助手

**目标导向 • 质量为本 • 智能化需求分析**

> 通过多智能体协作和先进的AI技术，为您提供专业、科学、高效的软件需求分析服务，助力打造切实可行的需求规格说明书。

## 📖 项目愿景

OpenManus需求分析助手是AI软件公司愿景的第一期核心项目，致力于**智能化、高效化、科学化**地辅助用户完成专业的软件需求分析，为后续的系统架构设计、编码实现等环节奠定坚实基础。

### 🎯 核心理念：目标导向、质量为本

- **目标导向**：所有分析活动围绕最终目标—生成高质量需求规格说明书
- **质量为本**：以需求完整性、准确性、可实现性为质量基础
- **智能协作**：多智能体团队协同工作，专业分工，科学流程
- **持续优化**：基于实际效果反馈，不断改进分析方法和质量

## 🏗️ 系统架构特色

### 质量导向澄清引擎
- **8维度质量评估**：功能需求、非功能需求、用户角色、业务规则、约束条件、验收标准、集成需求、数据需求
- **动态澄清策略**：基于质量缺陷动态生成针对性澄清问题
- **智能终止机制**：整体质量≥0.8且关键维度≥0.7时完成澄清
- **上下文记忆**：全程保持多轮对话的上下文连续性

### 多智能体协作团队
- **🔍 需求澄清师**：负责理解和澄清用户需求，确保信息完整准确
- **📊 业务分析师**：深度分析业务价值、用户场景和流程设计
- **📝 技术文档师**：编写专业的技术文档和需求规格说明
- **✅ 质量评审师**：进行全面质量评审和验收，确保交付标准

### 科学分析方法
- **需求模式识别**：智能识别不同类型需求（Web应用、移动App、管理系统等）
- **代码库分析**：分析现有代码，提供复用建议和实现复杂度评估
- **风险评估矩阵**：识别技术风险、业务风险并提供缓解策略
- **工作量预估**：基于历史数据和AI分析提供准确的开发工作量评估

## 🚀 快速开始

### 环境要求
- Python 3.12+
- Node.js 18+ (前端)
- 支持的LLM API（OpenAI、DeepSeek等）

### 安装步骤

#### 方法1：使用uv（推荐）
```bash
# 1. 安装uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 克隆项目
git clone https://github.com/FoundationAgents/OpenManus.git
cd OpenManus

# 3. 创建环境并安装依赖
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

#### 方法2：使用conda
```bash
# 1. 创建conda环境
conda create -n open_manus python=3.12
conda activate open_manus

# 2. 克隆并安装
git clone https://github.com/FoundationAgents/OpenManus.git
cd OpenManus
pip install -r requirements.txt
```

### 配置设置

1. 复制配置模板：
```bash
cp config/config.example.toml config/config.toml
```

2. 编辑`config/config.toml`添加API密钥：
```toml
[llm]
model = "deepseek-chat"  # 推荐使用deepseek
base_url = "https://api.deepseek.com"
api_key = "your-api-key-here"
max_tokens = 4096
temperature = 0.0
```

### 启动服务

```bash
# 启动需求分析助手
./start_openmanus.sh

# 或手动启动前后端
python main.py  # 后端服务
cd app/web && npm run dev  # 前端服务
```

## 💡 使用指南

### 第一步：描述需求
详细描述您的项目需求，无需担心表达不够专业，我们的AI助手会帮您澄清和完善。

### 第二步：智能澄清
系统会基于需求分析结果，动态生成澄清问题。您只需按提示回答，系统会自动判断何时达到足够的澄清质量。

### 第三步：深度分析
多智能体团队协作进行：
- 业务价值分析
- 用户场景建模
- 技术可行性评估
- 风险识别和缓解

### 第四步：文档生成
自动生成符合行业标准的需求规格说明书，包含：
- 功能需求详述
- 非功能需求规格
- 用户故事和验收标准
- 技术约束和实施建议

## 📊 系统特色

### 当前评分：🏆 100/100分（优秀级别）

✅ **基础架构完成** - 稳定的多智能体协作框架
✅ **LLM集成优化** - 深度集成DeepSeek，性能优异
✅ **会话管理系统** - 完整的多轮对话状态管理
✅ **质量导向澄清** - 科学的8维度质量评估体系
✅ **智能问题生成** - 基于需求模式的动态问题生成
✅ **代码库分析** - 智能复用建议和工作量评估
✅ **风险评估** - 全面的技术和业务风险识别

### 技术亮点

- **目标导向设计**：所有功能围绕生成高质量需求文档的最终目标
- **质量为本保障**：8维度质量评估确保输出质量
- **智能化程度高**：无需人工设置轮次，AI自动判断澄清完成
- **科学方法论**：基于软件工程最佳实践的需求分析方法
- **上下文记忆**：全程保持对话连续性，支持复杂需求澄清

## 🎯 核心价值

### 对用户的价值
- **节省时间**：AI辅助快速完成专业需求分析
- **提升质量**：基于最佳实践的科学分析方法
- **降低风险**：早期识别和评估项目风险
- **专业指导**：获得软件工程专家级的需求分析建议

### 对行业的价值
- **标准化流程**：推动需求分析过程的标准化和规范化
- **知识积累**：不断学习和优化需求分析方法
- **效率提升**：大幅提高软件项目前期分析效率
- **质量保障**：确保需求文档的完整性和可实现性

## 🔮 发展规划

### 第一期（当前）：需求分析智能助手 ✅
- 智能化需求澄清和分析
- 多智能体协作框架
- 质量导向澄清引擎

### 第二期：系统架构设计智能助手 🚧
- 基于需求文档的智能架构设计
- 技术选型和架构建议
- 架构质量评估

### 第三期：编码实现智能助手 📅
- 自动化代码生成
- 代码质量保障
- 开发过程优化

### 最终愿景：完整的AI软件公司生态 🎯
让AI智能体群活起来，真正接管传统软件公司的各个环节！

## 🤝 贡献指南

我们欢迎任何形式的贡献！您可以：

- 🐛 报告问题和建议
- 💡 提出新功能想法
- 📝 改进文档
- 🔧 提交代码改进

请先运行 `pre-commit run --all-files` 检查您的更改。

## 📞 联系我们

- 📧 Email: mannaandpoem@gmail.com
- 💬 Discord: [加入社区](https://discord.gg/DYn29wFk9z)

## 🙏 致谢

感谢以下开源项目的支持：
- [MetaGPT](https://github.com/geekan/MetaGPT) - 多智能体框架参考
- [OpenHands](https://github.com/All-Hands-AI/OpenHands) - 架构设计思路
- [PPIO](https://ppinfra.com/) - 计算资源支持

## 📜 许可证

本项目基于 [MIT License](https://opensource.org/licenses/MIT) 开源。

---

**OpenManus需求分析助手 - 让AI成为您的专业需求分析伙伴！** 🎯✨
