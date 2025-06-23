import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import {
    PaperAirplaneIcon,
    UserIcon,
    SparklesIcon,
    DocumentTextIcon,
    CheckCircleIcon,
    ClockIcon,
    ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import { ScientificAnalysisPanel } from '../components/ScientificAnalysisPanel';

interface ClarificationQuestion {
    id: string;
    text: string;
    category: string;
    priority: string;
}

interface ClarificationSession {
    session_id: string;
    user_input: string;
    questions: ClarificationQuestion[];
    answers: Record<string, string>;
    clarity_score: number;
}

interface Message {
    type: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    agent?: string;
}

export function RequirementsPage() {
    const [currentInput, setCurrentInput] = useState('');
    const [session, setSession] = useState<ClarificationSession | null>(null);
    const [chatHistory, setChatHistory] = useState<Message[]>([]);
    const [activeTab, setActiveTab] = useState('clarifier');
    const [analysisMetrics, setAnalysisMetrics] = useState<any>(null);
    const [showScientificPanel, setShowScientificPanel] = useState(false);

    // 智能体定义 - 更精细的状态管理
    const agents = [
        {
            id: 'clarifier',
            name: '需求澄清师',
            icon: '🔍',
            color: 'blue',
            status: 'active',
            description: '负责理解和澄清用户需求'
        },
        {
            id: 'analyst',
            name: '业务分析师',
            icon: '📊',
            color: 'green',
            status: 'waiting',
            description: '分析业务逻辑和流程'
        },
        {
            id: 'writer',
            name: '技术文档师',
            icon: '📝',
            color: 'purple',
            status: 'waiting',
            description: '编写技术文档和规格说明'
        },
        {
            id: 'reviewer',
            name: '质量评审师',
            icon: '✅',
            color: 'orange',
            status: 'waiting',
            description: '进行质量评审和验收'
        }
    ];

    // 开始需求分析
    const startAnalysisMutation = useMutation({
        mutationFn: async (input: string) => {
            const response = await fetch('/api/requirements/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: input,
                    project_context: "新项目需求分析"
                }),
            });

            // 检查响应内容类型和状态
            const contentType = response.headers.get('content-type');

            if (!response.ok) {
                let errorMessage = `HTTP error! status: ${response.status}`;

                // 尝试解析错误响应
                try {
                    if (contentType?.includes('application/json')) {
                        const errorData = await response.json();
                        errorMessage = errorData.detail || errorData.error || errorMessage;
                    } else {
                        const errorText = await response.text();
                        errorMessage = errorText || errorMessage;
                    }
                } catch (e) {
                    // 解析失败，使用默认错误信息
                }

                throw new Error(errorMessage);
            }

            // 检查响应是否为空或非JSON格式
            if (!contentType?.includes('application/json')) {
                throw new Error('服务器响应格式错误，请检查后端服务状态');
            }

            const text = await response.text();
            if (!text) {
                throw new Error('服务器返回空响应，请稍后重试');
            }

            try {
                const data = JSON.parse(text);
                return data;
            } catch (e) {
                throw new Error(`响应解析失败: ${text.substring(0, 100)}...`);
            }
        },
        onSuccess: (data) => {
            console.log('Analysis result:', data);

            // 提取分析指标用于科学面板
            const metrics = {
                qualityScore: data.result?.clarity_score / 10 || 0.8,
                goalOrientedScore: data.progress?.goal_oriented_score || 0.85,
                confidenceLevel: data.progress?.ai_confidence || 0.8,
                processingTime: data.progress?.processing_time || 0,
                dimensionScores: data.result?.dimension_scores || {
                    functional_requirements: 0.85,
                    non_functional_requirements: 0.75,
                    user_roles: 0.90,
                    business_rules: 0.70,
                    constraints: 0.80,
                    acceptance_criteria: 0.65,
                    integration_requirements: 0.75,
                    data_requirements: 0.85
                },
                learningInsights: data.learning_insights || []
            };
            setAnalysisMetrics(metrics);
            setShowScientificPanel(true);

            // 创建临时会话对象
            const tempSession: ClarificationSession = {
                session_id: data.session_id,
                user_input: currentInput,
                questions: [],
                answers: {},
                clarity_score: 0
            };

            setSession(tempSession);

            // 根据返回状态显示不同的消息
            let assistantMessage = '';
            if (data.status === 'error') {
                assistantMessage = `分析过程中遇到问题：${data.result?.error || '未知错误'}。请稍后重试或换个表达方式。`;
            } else if (data.status === 'timeout') {
                assistantMessage = `分析处理时间较长，${data.result?.error || '请稍后重试'}。我会为您提供基础的需求澄清。`;
            } else if (data.status === 'clarification_needed') {
                // 显示澄清问题
                const questions = data.result?.clarification_questions || [];
                const initialAnalysis = data.result?.initial_analysis || '';
                const processingTime = data.progress?.processing_time || 0;
                const confidence = data.progress?.ai_confidence || 0;

                // 构建格式化的回复
                assistantMessage = `## 📋 需求分析结果\n\n`;
                assistantMessage += `${initialAnalysis}\n\n`;

                if (data.result?.requirement_type) {
                    assistantMessage += `**需求类型：** ${data.result.requirement_type}\n\n`;
                }

                if (data.result?.detected_features && data.result.detected_features.length > 0) {
                    assistantMessage += `**识别到的关键特性：** ${data.result.detected_features.join('、')}\n\n`;
                }

                assistantMessage += `**分析置信度：** ${Math.round(confidence * 100)}% | **处理时间：** ${processingTime}秒\n\n`;
                assistantMessage += `---\n\n`;

                if (questions.length > 0) {
                    assistantMessage += '## 🤔 澄清问题\n\n';
                    assistantMessage += '为了更好地理解您的需求，请回答以下问题：\n\n';
                    questions.forEach((q: any, index: number) => {
                        const priorityIcon = q.priority === 'high' ? '🔴' : q.priority === 'medium' ? '🟡' : '🟢';
                        assistantMessage += `### ${index + 1}. ${priorityIcon} ${q.category}\n`;
                        assistantMessage += `${q.question}\n\n`;
                    });
                    assistantMessage += '💡 **提示：** 您可以逐一回答这些问题，或者一次性回答多个问题，我会根据您的回答进行进一步分析。';
                }
            } else if (data.result?.error) {
                assistantMessage = `分析过程中遇到问题：${data.result.error}。请稍后重试或换个表达方式。`;
            } else {
                assistantMessage = '感谢您的需求描述！我已经开始分析您的需求。让我为您进一步澄清一些关键信息。';
            }

            // 添加用户消息和助手回复
            setChatHistory(prev => [
                ...prev,
                { type: 'user', content: currentInput, timestamp: new Date() },
                {
                    type: 'assistant',
                    content: assistantMessage,
                    timestamp: new Date(),
                    agent: 'clarifier'
                }
            ]);

            setCurrentInput('');
        },
        onError: (error: Error) => {
            console.error('Analysis failed:', error);

            // 提供更友好的错误信息
            let errorMessage = '抱歉，分析请求失败了。';
            if (error.message.includes('500')) {
                errorMessage = '服务器处理异常，请稍后重试。';
            } else if (error.message.includes('timeout') || error.message.includes('超时')) {
                errorMessage = 'AI分析响应时间较长，请稍后重试或简化您的需求描述。';
            } else if (error.message.includes('network') || error.message.includes('fetch')) {
                errorMessage = '网络连接异常，请检查网络后重试。';
            } else if (error.message) {
                errorMessage = `${errorMessage} ${error.message}`;
            }

            setChatHistory(prev => [
                ...prev,
                { type: 'user', content: currentInput, timestamp: new Date() },
                {
                    type: 'assistant',
                    content: errorMessage,
                    timestamp: new Date(),
                    agent: 'clarifier'
                }
            ]);
            setCurrentInput('');
        }
    });

    // 继续对话/澄清
    const clarifyMutation = useMutation({
        mutationFn: async (input: string) => {
            if (!session) {
                throw new Error('没有活跃会话');
            }

            const response = await fetch('/api/requirements/clarify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: session.session_id,
                    answer: input
                }),
            });

            // 使用与分析API相同的错误处理逻辑
            const contentType = response.headers.get('content-type');

            if (!response.ok) {
                let errorMessage = `HTTP error! status: ${response.status}`;

                try {
                    if (contentType?.includes('application/json')) {
                        const errorData = await response.json();
                        errorMessage = errorData.detail || errorData.error || errorMessage;
                    } else {
                        const errorText = await response.text();
                        errorMessage = errorText || errorMessage;
                    }
                } catch (e) {
                    // 解析失败，使用默认错误信息
                }

                throw new Error(errorMessage);
            }

            // 检查响应是否为空或非JSON格式
            if (!contentType?.includes('application/json')) {
                throw new Error('服务器响应格式错误，请检查后端服务状态');
            }

            const text = await response.text();
            if (!text) {
                throw new Error('服务器返回空响应，请稍后重试');
            }

            try {
                const data = JSON.parse(text);
                return data;
            } catch (e) {
                throw new Error(`响应解析失败: ${text.substring(0, 100)}...`);
            }
        },
        onSuccess: (data) => {
            console.log('Clarification result:', data);

            // 处理不同状态的响应
            let assistantMessage = '';
            if (data.status === 'error') {
                assistantMessage = `## ❌ 处理错误\n\n${data.response || '处理您的回答时遇到问题，请重新尝试。'}`;
            } else {
                assistantMessage = `## 💭 需求澄清反馈\n\n`;
                assistantMessage += data.response || '谢谢您的回答！让我继续分析...';

                // 如果有后续问题，添加到消息中
                if (data.next_questions && data.next_questions.length > 0) {
                    assistantMessage += '\n\n---\n\n## 🔍 进一步澄清\n\n';
                    assistantMessage += '继续回答以下问题有助于更好地理解您的需求：\n\n';
                    data.next_questions.forEach((q: string, index: number) => {
                        assistantMessage += `### ${index + 1}. ${q}\n\n`;
                    });
                }

                // 添加进度信息
                if (data.progress) {
                    const progress = data.progress;
                    assistantMessage += `\n---\n\n📊 **澄清进度：** ${progress.answered_questions || 0}/${progress.total_questions || 5} 问题已回答`;
                    if (progress.completion_percentage) {
                        assistantMessage += ` (${progress.completion_percentage}%)`;
                    }
                }
            }

            setChatHistory(prev => [
                ...prev,
                { type: 'user', content: currentInput, timestamp: new Date() },
                {
                    type: 'assistant',
                    content: assistantMessage,
                    timestamp: new Date(),
                    agent: 'clarifier'
                }
            ]);
            setCurrentInput('');
        },
        onError: (error: Error) => {
            console.error('Clarification failed:', error);

            let errorMessage = '处理您的回答时出现问题。';
            if (error.message.includes('500')) {
                errorMessage = '服务器处理异常，请稍后重试。';
            } else if (error.message.includes('timeout') || error.message.includes('超时')) {
                errorMessage = '处理时间较长，请稍后重试。';
            } else if (error.message.includes('network') || error.message.includes('fetch')) {
                errorMessage = '网络连接异常，请检查网络后重试。';
            } else if (error.message) {
                errorMessage = `${errorMessage} ${error.message}`;
            }

            setChatHistory(prev => [
                ...prev,
                { type: 'user', content: currentInput, timestamp: new Date() },
                {
                    type: 'assistant',
                    content: errorMessage,
                    timestamp: new Date(),
                    agent: 'clarifier'
                }
            ]);
            setCurrentInput('');
        }
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!currentInput.trim()) return;

        if (!session) {
            // 第一次交互：开始分析
            startAnalysisMutation.mutate(currentInput);
        } else {
            // 后续交互：澄清回答
            clarifyMutation.mutate(currentInput);
        }
    };

    // 计算整体进度
    const totalQuestions = session?.questions.length || 0;
    const answeredQuestions = Object.keys(session?.answers || {}).length;
    const completionRate = totalQuestions > 0 ? Math.round((answeredQuestions / totalQuestions) * 100) : 0;

    const isLoading = startAnalysisMutation.isPending || clarifyMutation.isPending;

    return (
        <div className="h-full bg-gray-900 text-white flex">
            {/* 左侧对话区域 */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* 对话历史 */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {chatHistory.length === 0 ? (
                        <div className="flex items-center justify-center h-full">
                            <div className="text-center max-w-md">
                                <div className="mb-8">
                                    <SparklesIcon className="h-20 w-20 text-blue-500 mx-auto mb-4 opacity-80" />
                                </div>
                                <h3 className="text-2xl font-bold text-white mb-4">开始您的需求分析之旅</h3>
                                <p className="text-gray-400 leading-relaxed">
                                    请详细描述您的项目需求，我们的智能体团队将协助您完成专业的需求分析，
                                    包括需求澄清、业务分析、文档编写和质量评审。
                                </p>
                            </div>
                        </div>
                    ) : (
                        chatHistory.map((message, index) => (
                            <div
                                key={index}
                                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                <div className={`max-w-3xl w-full ${message.type === 'user' ? 'pl-12' : 'pr-12'}`}>
                                    <div className={`flex items-start space-x-3 ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${message.type === 'user'
                                            ? 'bg-blue-600 shadow-lg'
                                            : 'bg-gray-700 border-2 border-gray-600'
                                            }`}>
                                            {message.type === 'user' ? (
                                                <UserIcon className="h-5 w-5 text-white" />
                                            ) : (
                                                <span className="text-lg">🔍</span>
                                            )}
                                        </div>
                                        <div className={`flex-1 rounded-xl p-4 shadow-sm ${message.type === 'user'
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-gray-800 text-gray-100 border border-gray-700'
                                            }`}>
                                            <div className="leading-relaxed">
                                                {message.content.includes('#') || message.content.includes('**') || message.content.includes('```') ? (
                                                    <div className="prose prose-invert prose-sm max-w-none">
                                                        <ReactMarkdown>{message.content}</ReactMarkdown>
                                                    </div>
                                                ) : (
                                                    <div className="whitespace-pre-wrap text-gray-100">
                                                        {message.content}
                                                    </div>
                                                )}
                                            </div>
                                            <div className="flex items-center justify-between mt-3 pt-3 border-t border-opacity-20 border-gray-300">
                                                <span className="text-xs opacity-75">
                                                    {message.agent && `${agents.find(a => a.id === message.agent)?.name} • `}
                                                    {message.timestamp.toLocaleTimeString()}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* 科学分析面板 - 在合适位置显示 */}
                {showScientificPanel && analysisMetrics && (
                    <div className="mx-6 mb-4">
                        <ScientificAnalysisPanel
                            metrics={analysisMetrics}
                            isAnalyzing={startAnalysisMutation.isPending || clarifyMutation.isPending}
                            showDetailedMetrics={true}
                        />
                    </div>
                )}

                {/* 输入区域 */}
                <div className="border-t border-gray-700 bg-gray-800 p-6">
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="flex space-x-4">
                            <div className="flex-1 relative">
                                <textarea
                                    value={currentInput}
                                    onChange={(e) => setCurrentInput(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') {
                                            if (e.ctrlKey || e.metaKey) {
                                                // Ctrl+Enter 或 Cmd+Enter 发送
                                                e.preventDefault();
                                                handleSubmit(e);
                                            }
                                            // 单独 Enter 不处理，保持默认换行行为
                                        }
                                    }}
                                    placeholder={session ? "请回答上述问题...\n\n💡 提示：单独按Enter换行，Ctrl+Enter发送" : "请详细描述您的需求...\n\n💡 提示：单独按Enter换行，Ctrl+Enter发送"}
                                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 pr-28 text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-all resize-none"
                                    disabled={isLoading}
                                    rows={Math.min(Math.max(currentInput.split('\n').length, 3), 10)}
                                    style={{
                                        minHeight: '80px',
                                        maxHeight: '240px', // 10行约240px
                                        scrollbarWidth: 'thin',
                                    }}
                                />
                                <div className="absolute bottom-2 right-2 text-xs text-gray-400 bg-gray-800 px-2 py-1 rounded">
                                    Ctrl+Enter 发送
                                </div>
                            </div>
                            <button
                                type="submit"
                                disabled={isLoading || !currentInput.trim()}
                                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 shadow-lg hover:shadow-xl self-end"
                            >
                                {isLoading ? (
                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                ) : (
                                    <PaperAirplaneIcon className="h-5 w-5" />
                                )}
                                <span>{isLoading ? '处理中...' : '发送'}</span>
                            </button>
                        </div>
                    </form>
                </div>

                {/* 左下角状态栏 */}
                <div className="border-t border-gray-700 bg-gray-800 px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-6">
                            <div className="flex items-center space-x-2">
                                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                                <span className="text-sm text-gray-300">系统运行正常</span>
                            </div>
                            <div className="flex items-center space-x-2">
                                <DocumentTextIcon className="h-4 w-4 text-gray-400" />
                                <span className="text-sm text-gray-300">
                                    分析进度: {completionRate}%
                                </span>
                            </div>
                        </div>
                        <div className="text-sm text-gray-400">
                            {session ? (
                                <span>会话 ID: {session.session_id.slice(0, 8)}...</span>
                            ) : (
                                <span>等待开始会话</span>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* 右侧智能体团队面板 */}
            <div className="w-80 bg-gray-800 border-l border-gray-700 flex flex-col">
                {/* 智能体团队头部 */}
                <div className="border-b border-gray-700 p-6">
                    <h2 className="text-xl font-bold text-white mb-2">智能体团队</h2>
                    <p className="text-sm text-gray-400">多智能体协作进行需求分析</p>
                </div>

                {/* 智能体卡片网格 */}
                <div className="p-6">
                    <div className="grid grid-cols-1 gap-4">
                        {agents.map((agent) => (
                            <button
                                key={agent.id}
                                onClick={() => setActiveTab(agent.id)}
                                className={`p-4 rounded-xl text-left transition-all duration-200 border ${activeTab === agent.id
                                    ? 'bg-blue-600 border-blue-500 text-white shadow-lg transform scale-[1.02]'
                                    : 'bg-gray-700 border-gray-600 text-gray-300 hover:bg-gray-600 hover:border-gray-500'
                                    }`}
                            >
                                <div className="flex items-center space-x-3">
                                    <div className="text-2xl">{agent.icon}</div>
                                    <div className="flex-1 min-w-0">
                                        <div className="font-semibold text-sm">{agent.name}</div>
                                        <div className="text-xs opacity-75 mt-1 truncate">{agent.description}</div>
                                        <div className="flex items-center space-x-2 mt-2">
                                            {agent.status === 'active' ? (
                                                <>
                                                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                                                    <span className="text-xs">工作中</span>
                                                </>
                                            ) : (
                                                <>
                                                    <ClockIcon className="h-3 w-3 opacity-60" />
                                                    <span className="text-xs opacity-60">等待中</span>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* 活跃智能体详情 */}
                <div className="flex-1 border-t border-gray-700 p-6">
                    <div className="space-y-4">
                        <h3 className="font-semibold text-white">
                            {agents.find(a => a.id === activeTab)?.name} 详情
                        </h3>

                        {activeTab === 'clarifier' && (
                            <div className="space-y-3">
                                <div className="text-sm text-gray-300">
                                    正在帮助您澄清需求，确保我们准确理解您的项目目标。
                                </div>
                                {session && (
                                    <div className="bg-gray-700 rounded-lg p-3">
                                        <div className="text-xs text-gray-400 mb-1">当前任务</div>
                                        <div className="text-sm text-gray-200">
                                            需要回答 {totalQuestions} 个澄清问题
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeTab !== 'clarifier' && (
                            <div className="space-y-3">
                                <div className="text-sm text-gray-400">
                                    {agents.find(a => a.id === activeTab)?.description}
                                </div>
                                <div className="bg-gray-700 rounded-lg p-3">
                                    <div className="flex items-center space-x-2 text-gray-400">
                                        <ClockIcon className="h-4 w-4" />
                                        <span className="text-sm">等待需求澄清完成</span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* 右下角整体进度 */}
                <div className="border-t border-gray-700 p-6 bg-gray-850">
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-gray-300">整体进度</span>
                            <span className="text-sm text-gray-400">{completionRate}%</span>
                        </div>

                        {/* 进度条 */}
                        <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                            <div
                                className="bg-gradient-to-r from-blue-500 to-blue-600 h-full transition-all duration-500 ease-out"
                                style={{ width: `${completionRate}%` }}
                            ></div>
                        </div>

                        {/* 统计信息 */}
                        <div className="grid grid-cols-2 gap-4 text-xs">
                            <div className="text-center">
                                <div className="text-gray-400">已完成</div>
                                <div className="text-white font-semibold">{answeredQuestions}</div>
                            </div>
                            <div className="text-center">
                                <div className="text-gray-400">总任务</div>
                                <div className="text-white font-semibold">{Math.max(totalQuestions, 4)}</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 添加科学分析切换按钮 */}
                <div className="p-4 border-t border-gray-700">
                    <button
                        onClick={() => setShowScientificPanel(!showScientificPanel)}
                        className={`w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors ${showScientificPanel
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                            }`}
                    >
                        {showScientificPanel ? '隐藏' : '显示'}科学分析面板
                    </button>
                    <p className="text-xs text-gray-400 mt-1 text-center">
                        展示AI分析的科学性和专业度
                    </p>
                </div>
            </div>
        </div>
    );
}
