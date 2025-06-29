"""
需求建模工具 - 专业需求分析工具集合

包含：
1. 用例图生成
2. 需求矩阵生成
3. 用户故事模板
4. 验收标准生成
5. 需求追溯矩阵
"""

import json
import os
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.tool.base import BaseTool


class RequirementModelingTool(BaseTool):
    """需求建模工具 - 生成专业的需求分析产物"""

    name: str = "requirement_modeling"
    description: str = "生成用例图、需求矩阵、用户故事等专业需求分析产物"

    parameters: Optional[dict] = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "use_case_diagram",
                    "use_case_diagram_mermaid",
                    "requirement_matrix",
                    "user_stories",
                    "acceptance_criteria",
                    "traceability_matrix",
                ],
                "description": "需求建模操作类型",
            },
            "requirements_text": {"type": "string", "description": "需求描述文本"},
            "actors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "系统参与者列表",
            },
            "functional_requirements": {
                "type": "array",
                "items": {"type": "string"},
                "description": "功能需求列表",
            },
            "non_functional_requirements": {
                "type": "array",
                "items": {"type": "string"},
                "description": "非功能需求列表",
            },
            "priority": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "需求优先级",
                "default": "medium",
            },
        },
        "required": ["action", "requirements_text"],
    }

    async def execute(self, **kwargs) -> str:
        """执行需求建模操作"""
        action = kwargs.get("action")
        requirements_text = kwargs.get("requirements_text", "")

        if action == "use_case_diagram":
            return await self._generate_use_case_diagram(kwargs)
        elif action == "use_case_diagram_mermaid":
            return await self._generate_use_case_diagram_mermaid(kwargs)
        elif action == "requirement_matrix":
            return await self._generate_requirement_matrix(kwargs)
        elif action == "user_stories":
            return await self._generate_user_stories(kwargs)
        elif action == "acceptance_criteria":
            return await self._generate_acceptance_criteria(kwargs)
        elif action == "traceability_matrix":
            return await self._generate_traceability_matrix(kwargs)
        else:
            return f"不支持的操作类型: {action}"

    async def _generate_use_case_diagram(self, params: Dict) -> str:
        """生成用例图（PlantUML格式）"""
        requirements_text = params.get("requirements_text", "")
        actors = params.get("actors", [])

        # 如果没有提供参与者，尝试从需求文本中提取
        if not actors:
            actors = self._extract_actors(requirements_text)

        use_cases = self._extract_use_cases(requirements_text)

        # 生成PlantUML用例图
        plantuml_code = "@startuml\n"
        plantuml_code += "left to right direction\n"
        plantuml_code += "skinparam packageStyle rectangle\n\n"

        # 添加参与者
        for actor in actors:
            plantuml_code += f"actor {actor}\n"

        plantuml_code += "\nrectangle 系统 {\n"

        # 添加用例
        for use_case in use_cases:
            safe_name = use_case.replace(" ", "_").replace("（", "").replace("）", "")
            plantuml_code += f'  usecase "{use_case}" as {safe_name}\n'

        plantuml_code += "}\n\n"

        # 添加关联关系
        for actor in actors:
            for use_case in use_cases:
                safe_name = (
                    use_case.replace(" ", "_").replace("（", "").replace("）", "")
                )
                # 简化处理，可根据关键词进一步分析关系类型
                if "登录" in use_case or "注册" in use_case:
                    plantuml_code += f"{actor} -- {safe_name}\n"
                elif "管理" in use_case and "管理员" in actor:
                    plantuml_code += f"{actor} -- {safe_name}\n"
                else:
                    plantuml_code += f"{actor} --> {safe_name}\n"


        plantuml_code += "@enduml"

        # 保存到文件
        output_path = self._save_diagram(plantuml_code, "use_case_diagram.puml")

        return f"""✅ 用例图生成完成

📋 识别的参与者: {', '.join(actors)}
🎯 识别的用例: {', '.join(use_cases)}

📁 PlantUML文件已保存: {output_path}

🔗 PlantUML代码:
```plantuml
{plantuml_code}
```

💡 使用说明:
1. 可以在PlantUML编辑器中查看图形化结果
2. 建议进一步细化用例之间的关系（扩展、包含等）
3. 添加系统边界和更详细的用例描述"""

    async def _generate_use_case_diagram_mermaid(self, params: Dict) -> str:
        """生成用例图（Mermaid.js格式）"""
        requirements_text = params.get("requirements_text", "")
        actors = params.get("actors", [])

        # 如果没有提供参与者，尝试从需求文本中提取
        if not actors:
            actors = self._extract_actors(requirements_text)

        use_cases = self._extract_use_cases(requirements_text)

        # 生成Mermaid.js用例图
        mermaid_code = "graph TD\n"
        mermaid_code += "    subgraph 系统用例图\n"

        # 添加参与者
        for i, actor in enumerate(actors):
            mermaid_code += f"        actor{i}[{actor}]\n"

        mermaid_code += "\n"

        # 添加用例
        for i, use_case in enumerate(use_cases):
            safe_name = use_case.replace(" ", "_").replace("（", "").replace("）", "")
            mermaid_code += f'        uc{i}({use_case})\n'

        mermaid_code += "\n"

        # 添加关联关系（简化处理）
        for i, actor in enumerate(actors):
            for j, use_case in enumerate(use_cases):
                mermaid_code += f"        actor{i} --> uc{j}\n"

        mermaid_code += "    end"

        # 保存到文件
        output_path = self._save_diagram(mermaid_code, "use_case_diagram.md")

        return f"""✅ 用例图生成完成 (Mermaid.js)

📋 识别的参与者: {', '.join(actors)}
🎯 识别的用例: {', '.join(use_cases)}

📁 Mermaid文件已保存: {output_path}

🔗 Mermaid代码:
```mermaid
{mermaid_code}
```

💡 使用说明:
1. 可以在支持Mermaid.js的Markdown编辑器中查看图形化结果
2. 建议进一步细化用例之间的关系（扩展、包含等）
3. 添加系统边界和更详细的用例描述"""

    async def _generate_requirement_matrix(self, params: Dict) -> str:
        """生成需求矩阵"""
        functional_reqs = params.get("functional_requirements", [])
        non_functional_reqs = params.get("non_functional_requirements", [])
        priority = params.get("priority", "medium")

        # 如果没有提供需求列表，从文本中提取
        if not functional_reqs and not non_functional_reqs:
            requirements_text = params.get("requirements_text", "")
            functional_reqs, non_functional_reqs = self._extract_requirements(
                requirements_text
            )

        matrix = {
            "项目名称": "系统需求",
            "生成时间": self._get_timestamp(),
            "功能需求": [],
            "非功能需求": [],
            "需求统计": {
                "功能需求数量": len(functional_reqs),
                "非功能需求数量": len(non_functional_reqs),
                "总需求数量": len(functional_reqs) + len(non_functional_reqs),
            },
        }

        # 处理功能需求
        for i, req in enumerate(functional_reqs, 1):
            matrix["功能需求"].append(
                {
                    "编号": f"FR-{i:03d}",
                    "描述": req,
                    "优先级": priority,
                    "类型": "功能需求",
                    "状态": "已识别",
                    "来源": "需求分析",
                    "验证方法": "功能测试",
                }
            )

        # 处理非功能需求
        for i, req in enumerate(non_functional_reqs, 1):
            matrix["非功能需求"].append(
                {
                    "编号": f"NFR-{i:03d}",
                    "描述": req,
                    "优先级": priority,
                    "类型": "非功能需求",
                    "状态": "已识别",
                    "来源": "需求分析",
                    "验证方法": "性能测试",
                }
            )

        # 保存为JSON文件
        output_path = self._save_json(matrix, "requirements_matrix.json")

        # 生成表格形式的报告
        report = f"""✅ 需求矩阵生成完成

📊 需求统计:
- 功能需求: {len(functional_reqs)}项
- 非功能需求: {len(non_functional_reqs)}项
- 总计: {len(functional_reqs) + len(non_functional_reqs)}项

📋 功能需求:
"""
        for req in matrix["功能需求"]:
            report += f"  {req['编号']}: {req['描述']}\n"

        report += f"\n📋 非功能需求:\n"
        for req in matrix["非功能需求"]:
            report += f"  {req['编号']}: {req['描述']}\n"

        report += f"\n📁 详细矩阵已保存: {output_path}"

        return report

    async def _generate_user_stories(self, params: Dict) -> str:
        """生成用户故事"""
        requirements_text = params.get("requirements_text", "")
        actors = params.get("actors", [])
        functional_reqs = params.get("functional_requirements", [])

        if not actors:
            actors = self._extract_actors(requirements_text)

        if not functional_reqs:
            functional_reqs, _ = self._extract_requirements(requirements_text)

        user_stories = []

        # 为每个功能需求生成用户故事
        for i, req in enumerate(functional_reqs, 1):
            # 选择最相关的角色（简化处理，选择第一个）
            actor = actors[0] if actors else "用户"

            story = {
                "编号": f"US-{i:03d}",
                "标题": req,
                "用户故事": f"作为{actor}，我希望{req}，以便我能够提高工作效率和用户体验。",
                "验收标准": [
                    f"✅ 系统能够{req}",
                    "✅ 操作界面友好易用",
                    "✅ 功能响应时间 < 3秒",
                    "✅ 错误处理机制完善",
                ],
                "优先级": params.get("priority", "medium"),
                "估算点数": "待评估",
                "状态": "待开发",
            }
            user_stories.append(story)

        # 保存用户故事
        output_data = {
            "项目": "系统开发",
            "生成时间": self._get_timestamp(),
            "用户故事": user_stories,
        }

        output_path = self._save_json(output_data, "user_stories.json")

        # 生成报告
        report = f"""✅ 用户故事生成完成

👥 识别的用户角色: {', '.join(actors)}
📝 生成的用户故事: {len(user_stories)}个

📋 用户故事列表:
"""
        for story in user_stories:
            report += f"\n{story['编号']}: {story['标题']}\n"
            report += f"  📖 {story['用户故事']}\n"
            report += f"  ✅ 验收标准: {len(story['验收标准'])}项\n"

        report += f"\n📁 详细文档已保存: {output_path}"

        return report

    async def _generate_acceptance_criteria(self, params: Dict) -> str:
        """生成验收标准"""
        requirements_text = params.get("requirements_text", "")
        functional_reqs = params.get("functional_requirements", [])

        if not functional_reqs:
            functional_reqs, _ = self._extract_requirements(requirements_text)

        acceptance_criteria = {
            "项目": "系统开发",
            "生成时间": self._get_timestamp(),
            "验收标准": [],
        }

        for i, req in enumerate(functional_reqs, 1):
            criteria = {
                "需求编号": f"AC-{i:03d}",
                "需求描述": req,
                "验收标准": [
                    f"给定：用户已登录系统",
                    f"当：用户执行{req}操作",
                    f"那么：系统应该正确处理并返回预期结果",
                    "并且：操作过程中没有错误",
                    "并且：用户体验良好",
                ],
                "测试场景": ["正常流程测试", "异常情况处理", "边界值测试", "性能测试"],
            }
            acceptance_criteria["验收标准"].append(criteria)

        output_path = self._save_json(acceptance_criteria, "acceptance_criteria.json")

        report = f"""✅ 验收标准生成完成

📋 覆盖需求: {len(functional_reqs)}项
🧪 测试场景: 4类/需求

📝 验收标准概览:
"""
        for criteria in acceptance_criteria["验收标准"]:
            report += f"\n{criteria['需求编号']}: {criteria['需求描述']}\n"
            report += f"  📋 标准数量: {len(criteria['验收标准'])}项\n"
            report += f"  🧪 测试场景: {len(criteria['测试场景'])}类\n"

        report += f"\n📁 详细文档已保存: {output_path}"

        return report

    async def _generate_traceability_matrix(self, params: Dict) -> str:
        """生成需求追溯矩阵"""
        requirements_text = params.get("requirements_text", "")
        functional_reqs = params.get("functional_requirements", [])
        non_functional_reqs = params.get("non_functional_requirements", [])

        if not functional_reqs and not non_functional_reqs:
            functional_reqs, non_functional_reqs = self._extract_requirements(
                requirements_text
            )

        traceability = {
            "项目": "系统开发",
            "生成时间": self._get_timestamp(),
            "追溯关系": [],
        }

        # 功能需求追溯
        for i, req in enumerate(functional_reqs, 1):
            trace = {
                "需求ID": f"FR-{i:03d}",
                "需求描述": req,
                "需求类型": "功能需求",
                "设计文档": f"设计规格书第{i}章",
                "实现模块": f"模块_{i}",
                "测试用例": f"TC_FR_{i:03d}",
                "状态": "待实现",
            }
            traceability["追溯关系"].append(trace)

        # 非功能需求追溯
        for i, req in enumerate(non_functional_reqs, 1):
            trace = {
                "需求ID": f"NFR-{i:03d}",
                "需求描述": req,
                "需求类型": "非功能需求",
                "设计文档": f"架构设计文档第{i}节",
                "实现模块": "系统架构层",
                "测试用例": f"TC_NFR_{i:03d}",
                "状态": "待实现",
            }
            traceability["追溯关系"].append(trace)

        output_path = self._save_json(traceability, "traceability_matrix.json")

        report = f"""✅ 需求追溯矩阵生成完成

🔗 建立追溯关系: {len(traceability['追溯关系'])}项
📋 功能需求: {len(functional_reqs)}项
📋 非功能需求: {len(non_functional_reqs)}项

📊 追溯关系:
需求ID | 类型 | 设计文档 | 实现模块 | 测试用例
"""
        for trace in traceability["追溯关系"]:
            report += f"{trace['需求ID']} | {trace['需求类型']} | {trace['设计文档']} | {trace['实现模块']} | {trace['测试用例']}\n"

        report += f"\n📁 详细矩阵已保存: {output_path}"

        return report

    def _extract_actors(self, text: str) -> List[str]:
        """从需求文本中提取参与者"""
        actors = []

        # 常见的参与者关键词
        actor_keywords = [
            "用户",
            "管理员",
            "客户",
            "访客",
            "学生",
            "老师",
            "员工",
            "操作员",
            "系统管理员",
            "游客",
            "会员",
            "顾客",
        ]

        for keyword in actor_keywords:
            if keyword in text:
                actors.append(keyword)

        # 如果没有找到，使用默认参与者
        if not actors:
            actors = ["用户", "管理员"]

        return list(set(actors))  # 去重

    def _extract_use_cases(self, text: str) -> List[str]:
        """从需求文本中提取用例"""
        use_cases = []

        # 简单的用例提取（基于动词+名词模式）
        import re

        # 查找"能够"、"可以"、"需要"等后面的功能描述
        patterns = [
            r"能够([^，。,!！]*)",
            r"可以([^，。,!！]*)",
            r"需要([^，。,!！]*)",
            r"实现([^，。,!！]*)",
            r"提供([^，。,!！]*)",
            r"支持([^，。,!！]*)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            use_cases.extend(matches)

        # 清理和格式化
        use_cases = [uc.strip() for uc in use_cases if uc.strip()]
        use_cases = list(set(use_cases))  # 去重

        # 如果没有找到，使用默认用例
        if not use_cases:
            use_cases = ["登录系统", "查看信息", "管理数据"]

        return use_cases

    def _extract_requirements(self, text: str) -> tuple:
        """从文本中提取功能需求和非功能需求"""
        functional_reqs = []
        non_functional_reqs = []

        # 功能需求关键词
        func_keywords = [
            "功能",
            "能够",
            "可以",
            "实现",
            "提供",
            "支持",
            "操作",
            "管理",
            "查询",
            "添加",
            "删除",
            "修改",
        ]

        # 非功能需求关键词
        non_func_keywords = [
            "性能",
            "安全",
            "可用性",
            "可靠性",
            "兼容性",
            "扩展性",
            "响应时间",
            "并发",
            "稳定性",
        ]

        # 简单分句
        sentences = (
            text.replace("。", "\n").replace("；", "\n").replace("!", "\n").split("\n")
        )

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 判断是否为功能需求
            if any(keyword in sentence for keyword in func_keywords):
                functional_reqs.append(sentence)
            # 判断是否为非功能需求
            elif any(keyword in sentence for keyword in non_func_keywords):
                non_functional_reqs.append(sentence)
            # 默认归类为功能需求
            elif len(sentence) > 5:  # 过滤太短的句子
                functional_reqs.append(sentence)

        return functional_reqs, non_functional_reqs

    def _save_diagram(self, content: str, filename: str) -> str:
        """保存图表文件"""
        output_dir = "data/requirements_analysis"
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path

    def _save_json(self, data: Dict, filename: str) -> str:
        """保存JSON文件"""
        output_dir = "data/requirements_analysis"
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return output_path

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
