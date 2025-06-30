"""
OpenManus CLI交互式界面
"""

import json
import sys
from typing import Dict, List, Optional, Union

from app.agent.manus import Manus
from app.logger import logger
from app.schema import (
    ChoiceQuestion,
    ConfirmQuestion,
    MultiChoiceQuestion,
    Question,
    QuestionResponse,
    QuestionType,
    QuestionUnion,
    ScaleQuestion,
    ShortTextQuestion,
    YesNoQuestion,
)


class CLIInterface:
    """命令行交互界面"""

    def __init__(self):
        self.conversation_history: List[Dict] = []
        self.session_active = True
        self.waiting_for_answer = False  # 是否在等待用户回答
        self.current_question: Optional[QuestionUnion] = None  # 当前待回答的问题
        self.current_context = None  # 当前对话上下文

    def print_welcome(self):
        """打印欢迎信息"""
        print("\n" + "=" * 60)
        print("🎯 OpenManus 需求分析助手 - CLI模式")
        print("=" * 60)
        print("我将帮助您进行软件需求的深度分析和澄清。")
        print("请描述您的项目想法，我会通过多轮对话来完善需求。")
        print("\n📋 可用命令：")
        print("  /help     - 查看帮助信息")
        print("  /summary  - 显示对话总结")
        print("  /document - 生成需求文档")
        print("  /new      - 开始新对话")
        print("  /exit     - 退出程序")
        print("=" * 60)

    def print_help(self):
        """打印帮助信息"""
        print("\n📖 帮助信息:")
        print("1. 描述您的项目想法或需求")
        print("2. 回答我提出的澄清问题")
        print("3. 我会逐步完善和分析您的需求")
        print("4. 最终生成结构化的需求文档")
        print("\n💡 示例输入:")
        print("- '我想要一个图书管理系统'")
        print("- '需要一个在线购物网站'")
        print("- '开发一个员工考勤管理应用'")
        print("\n🔧 高级命令:")
        print("- /summary  查看对话历史摘要")
        print("- /document 生成完整需求文档")
        print("- /new      重新开始新的需求分析")

    def parse_question(self, response: str) -> Optional[QuestionUnion]:
        """尝试从回复中解析结构化问题"""
        try:
            # 尝试找到JSON格式的问题定义
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                question_json = response[start:end]
                question_dict = json.loads(question_json)

                # 根据问题类型创建对应的Question对象
                question_type = QuestionType(question_dict.get("type", "choice"))
                question_class = {
                    QuestionType.CHOICE: ChoiceQuestion,
                    QuestionType.MULTI_CHOICE: MultiChoiceQuestion,
                    QuestionType.YES_NO: YesNoQuestion,
                    QuestionType.SCALE: ScaleQuestion,
                    QuestionType.SHORT_TEXT: ShortTextQuestion,
                    QuestionType.CONFIRM: ConfirmQuestion,
                }[question_type]

                return question_class(**question_dict)
        except Exception as e:
            logger.debug(f"Failed to parse question: {e}")
        return None

    def format_question(self, question: QuestionUnion) -> str:
        """格式化问题显示"""
        output = ["\n📝 " + question.question]
        if question.description:
            output.append(f"💡 {question.description}")

        if isinstance(question, ChoiceQuestion):
            output.append("\n请选择一个选项：")
            for i, option in enumerate(question.options, 1):
                default_mark = " (默认)" if question.default == i - 1 else ""
                output.append(f"{i}. {option}{default_mark}")
            output.append("\n输入选项编号：")

        elif isinstance(question, MultiChoiceQuestion):
            output.append("\n请选择一个或多个选项（用逗号分隔）：")
            for i, option in enumerate(question.options, 1):
                default_mark = (
                    " (默认)"
                    if question.defaults and i - 1 in question.defaults
                    else ""
                )
                output.append(f"{i}. {option}{default_mark}")
            output.append("\n输入选项编号（如：1,3）：")

        elif isinstance(question, YesNoQuestion):
            default_text = (
                " (默认是)"
                if question.default
                else " (默认否)" if question.default is not None else ""
            )
            output.append(f"\n请回答是/否{default_text}：")

        elif isinstance(question, ScaleQuestion):
            output.append(
                f"\n请选择评分（{question.min_value}-{question.max_value}）："
            )
            if question.labels:
                for i, label in enumerate(question.labels):
                    output.append(f"{question.min_value + i}: {label}")
            default_mark = (
                f" (默认: {question.default})" if question.default is not None else ""
            )
            output.append(f"\n输入评分{default_mark}：")

        elif isinstance(question, ShortTextQuestion):
            max_len = f"（最多{question.max_length}字）" if question.max_length else ""
            placeholder = (
                f"\n提示：{question.placeholder}" if question.placeholder else ""
            )
            default = f" (默认: {question.default})" if question.default else ""
            output.append(f"\n请输入{max_len}{default}：{placeholder}")

        elif isinstance(question, ConfirmQuestion):
            output.append(f"\n默认值：{question.default_value}")
            output.append("\n是否使用该默认值？(Y/n)：")

        return "\n".join(output)

    def parse_answer(
        self, question: QuestionUnion, answer: str
    ) -> Optional[QuestionResponse]:
        """解析用户回答"""
        try:
            answer = answer.strip()

            if isinstance(question, ChoiceQuestion):
                if not answer and question.default is not None:
                    return QuestionResponse(
                        question_type=question.type,
                        response=question.default,
                        raw_input=answer,
                    )
                try:
                    idx = int(answer) - 1
                    if 0 <= idx < len(question.options):
                        return QuestionResponse(
                            question_type=question.type, response=idx, raw_input=answer
                        )
                except ValueError:
                    pass

            elif isinstance(question, MultiChoiceQuestion):
                if not answer and question.defaults:
                    return QuestionResponse(
                        question_type=question.type,
                        response=question.defaults,
                        raw_input=answer,
                    )
                try:
                    indices = [int(i.strip()) - 1 for i in answer.split(",")]
                    if all(0 <= i < len(question.options) for i in indices):
                        return QuestionResponse(
                            question_type=question.type,
                            response=indices,
                            raw_input=answer,
                        )
                except ValueError:
                    pass

            elif isinstance(question, YesNoQuestion):
                if not answer and question.default is not None:
                    return QuestionResponse(
                        question_type=question.type,
                        response=question.default,
                        raw_input=answer,
                    )
                if answer.lower() in ["y", "yes", "是", "1", "true"]:
                    return QuestionResponse(
                        question_type=question.type, response=True, raw_input=answer
                    )
                elif answer.lower() in ["n", "no", "否", "0", "false"]:
                    return QuestionResponse(
                        question_type=question.type, response=False, raw_input=answer
                    )

            elif isinstance(question, ScaleQuestion):
                if not answer and question.default is not None:
                    return QuestionResponse(
                        question_type=question.type,
                        response=question.default,
                        raw_input=answer,
                    )
                try:
                    value = int(answer)
                    if question.min_value <= value <= question.max_value:
                        return QuestionResponse(
                            question_type=question.type,
                            response=value,
                            raw_input=answer,
                        )
                except ValueError:
                    pass

            elif isinstance(question, ShortTextQuestion):
                if not answer and question.default:
                    return QuestionResponse(
                        question_type=question.type,
                        response=question.default,
                        raw_input=answer,
                    )
                if question.max_length and len(answer) > question.max_length:
                    print(f"\n⚠️ 输入超过最大长度限制（{question.max_length}字）")
                    return None
                return QuestionResponse(
                    question_type=question.type, response=answer, raw_input=answer
                )

            elif isinstance(question, ConfirmQuestion):
                if not answer or answer.lower() in ["y", "yes", "是"]:
                    return QuestionResponse(
                        question_type=question.type, response=True, raw_input=answer
                    )
                elif answer.lower() in ["n", "no", "否"]:
                    return QuestionResponse(
                        question_type=question.type, response=False, raw_input=answer
                    )

        except Exception as e:
            logger.error(f"解析答案时出错: {e}")

        return None

    async def process_user_input(self, agent: Manus, user_input: str) -> bool:
        """处理用户输入"""
        try:
            # 添加到对话历史
            self.conversation_history.append({"role": "user", "content": user_input})

            print("\n🤔 分析中...")

            # 如果在等待回答，将用户输入作为答案处理
            if self.waiting_for_answer and self.current_question:
                # 解析用户回答
                answer = self.parse_answer(self.current_question, user_input)
                if answer is None:
                    print("\n❌ 无效的回答格式，请重试")
                    print(self.format_question(self.current_question))
                    return True

                # 构建回答上下文
                context = (
                    f"用户对问题「{self.current_question.question}」的回答是：{answer.response}\n"
                    "请继续分析并提出下一个问题或给出总结。"
                )
                response = await agent.run(context)
            else:
                # 新的需求输入
                response = await agent.run(user_input)

            # 添加回复到历史
            self.conversation_history.append({"role": "assistant", "content": response})

            # 尝试解析问题
            question = self.parse_question(response)
            if question:
                self.waiting_for_answer = True
                self.current_question = question
                # 显示格式化的问题
                print(self.format_question(question))
            else:
                # 显示普通回复
                print(f"\n🎯 需求分析助手:")
                print(response)
                self.waiting_for_answer = False
                self.current_question = None

            return True

        except Exception as e:
            logger.error(f"处理输入时出错: {e}")
            print(f"\n❌ 处理出错: {e}")
            return False

    def show_conversation_summary(self):
        """显示对话总结"""
        if not self.conversation_history:
            print("\n📋 暂无对话历史")
            return

        print("\n📋 对话总结:")
        print("-" * 50)
        for i, msg in enumerate(self.conversation_history, 1):
            role = "👤 用户" if msg["role"] == "user" else "🤖 助手"
            content = msg["content"]
            # 限制显示长度
            display_content = content[:100] + "..." if len(content) > 100 else content
            print(f"{i}. {role}: {display_content}")
        print("-" * 50)
        print(f"总计 {len(self.conversation_history)} 条消息")

    async def generate_document(self, agent: Manus):
        """生成需求文档"""
        if not self.conversation_history:
            print("\n📝 暂无对话内容，无法生成文档")
            return

        if self.waiting_for_answer:
            print("\n⚠️ 当前还有未回答的问题，请先完成当前对话")
            return

        try:
            print("\n📝 正在生成需求文档...")

            # 构建文档生成请求
            doc_prompt = "基于我们的对话历史，请生成一份完整的需求文档，包括功能需求、非功能需求、验收标准等。"
            doc_response = await agent.run(doc_prompt)

            print(f"\n📄 需求文档:")
            print("=" * 60)
            print(doc_response)
            print("=" * 60)

        except Exception as e:
            logger.error(f"生成文档时出错: {e}")
            print(f"\n❌ 文档生成出错: {e}")

    def start_new_conversation(self):
        """开始新对话"""
        if self.waiting_for_answer:
            confirm = (
                input("\n⚠️ 当前对话尚未完成，确定要开始新对话吗？(y/N): ")
                .strip()
                .lower()
            )
            if confirm not in ["y", "yes", "是"]:
                print("继续当前对话...")
                return

        self.conversation_history.clear()
        self.waiting_for_answer = False
        self.current_question = None
        self.current_context = None
        print("\n🆕 已开始新的对话会话")
        print("请描述您的新项目需求...")

    async def run(self, agent: Manus):
        """运行CLI界面"""
        self.print_welcome()

        while self.session_active:
            try:
                # 获取用户输入
                prompt = "\n💬 请回答: " if self.waiting_for_answer else "\n💬 请输入: "
                user_input = input(prompt).strip()

                if not user_input:
                    continue

                # 处理命令
                if user_input.lower() in ["/exit", "/quit", "exit", "quit"]:
                    if self.waiting_for_answer:
                        confirm = (
                            input("\n⚠️ 当前对话尚未完成，确定要退出吗？(y/N): ")
                            .strip()
                            .lower()
                        )
                        if confirm not in ["y", "yes", "是"]:
                            print("继续对话...")
                            continue
                    print("\n👋 谢谢使用，再见！")
                    break

                elif user_input.lower() in ["/help", "/h", "help"]:
                    self.print_help()
                    continue

                elif user_input.lower() in ["/summary", "/s", "summary"]:
                    self.show_conversation_summary()
                    continue

                elif user_input.lower() in ["/document", "/doc", "/d", "document"]:
                    await self.generate_document(agent)
                    continue

                elif user_input.lower() in ["/new", "/n", "new"]:
                    self.start_new_conversation()
                    continue

                # 处理需求输入
                success = await self.process_user_input(agent, user_input)

                if not success:
                    print("\n🔄 请重试输入")

            except KeyboardInterrupt:
                print("\n\n⚠️  检测到中断信号...")
                confirm = input("确定要退出吗？(y/N): ").strip().lower()
                if confirm in ["y", "yes", "是"]:
                    break
                else:
                    print("继续对话...")

            except EOFError:
                print("\n👋 会话结束，再见！")
                break

            except Exception as e:
                logger.error(f"CLI运行出错: {e}")
                print(f"\n❌ 出现错误: {e}")
                print("请重试或输入 /exit 退出")

        print("\n🧹 CLI会话结束")
