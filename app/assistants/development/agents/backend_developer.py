"""
后端开发智能体 - 基于架构设计实现后端代码
"""

from typing import Dict, List, Optional

from app.agent.base import BaseAgent
from app.logger import logger


class BackendDeveloperAgent(BaseAgent):
    """后端开发师 - 基于系统架构实现后端功能"""

    def __init__(
        self,
        name: str = "后端开发师",
        description: str = "基于架构设计实现后端代码",
        **kwargs,
    ):
        super().__init__(name=name, description=description, **kwargs)

        self.system_prompt = """你是一名资深的后端开发工程师，负责基于系统架构设计实现高质量的后端代码。

## 工作职责
1. 基于系统架构设计实现后端服务
2. 实现API接口和业务逻辑
3. 集成数据库和第三方服务
4. 确保代码质量和性能优化
5. 编写单元测试和集成测试

## 开发原则
- **代码规范**：遵循编程语言最佳实践
- **架构一致性**：严格按照架构设计实现
- **性能优化**：考虑并发、缓存、数据库优化
- **安全性**：实现认证、授权、数据验证
- **可测试性**：编写可测试的代码

## 输出要求
生成可运行的后端代码，包含：
1. 完整的项目结构
2. 核心业务逻辑实现
3. API接口实现
4. 数据库集成代码
5. 配置文件和部署脚本

始终编写高质量、可维护、可扩展的代码。"""

    async def implement_backend_service(
        self, architecture_doc: str, database_doc: str
    ) -> str:
        """实现后端服务"""
        logger.info("开始后端服务实现")

        implementation_prompt = f"""请基于以下架构设计实现后端服务：

## 系统架构设计
{architecture_doc}

## 数据库设计
{database_doc}

请按以下结构实现后端代码：

# 后端服务实现

## 1. 项目结构
```
backend/
├── src/
│   ├── controllers/     # 控制器层
│   ├── services/        # 业务逻辑层
│   ├── models/          # 数据模型
│   ├── utils/           # 工具类
│   └── config/          # 配置文件
├── tests/               # 测试代码
├── docs/                # API文档
└── deployment/          # 部署文件
```

## 2. 核心代码实现

### 2.1 数据模型实现
[基于数据库设计实现数据模型]

### 2.2 业务服务实现
[实现核心业务逻辑服务]

### 2.3 API控制器实现
[实现RESTful API接口]

### 2.4 数据库集成
[实现数据访问层]

## 3. 配置和部署
[配置文件和部署脚本]

请提供完整可运行的代码实现。"""

        self.update_memory("user", implementation_prompt)
        result = await self.run()

        logger.info("后端服务实现完成")
        return result

    def get_development_summary(self) -> Dict:
        """获取开发摘要"""
        return {
            "developer": self.name,
            "status": self.state.value,
            "implementation_complete": self.state.value == "FINISHED",
            "code_quality": "基于最新实现结果",
        }
