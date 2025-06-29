import React from 'react';
import {
    PaperAirplaneIcon,
    UserIcon,
    SparklesIcon,
    ArrowPathIcon
} from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';
import { useRequirementsContext } from '../RequirementsPageContext';
import { useState, useRef, useEffect } from 'react';

// 阵营配置
const CAMPS = {
    user: {
        name: '用户方',
        color: 'blue',
        bgClass: 'bg-blue-500/10 border-blue-500/20',
        textClass: 'text-blue-300',
        secondaryTextClass: 'text-blue-200',
        iconBg: 'bg-blue-600',
        icon: '👤'
    },
    system: {
        name: 'OpenManus系统',
        color: 'green',
        bgClass: 'bg-green-500/10 border-green-500/20',
        textClass: 'text-green-300',
        secondaryTextClass: 'text-green-200',
        iconBg: 'bg-green-600',
        icon: '🤖'
    },
    llm: {
        name: 'LLM引擎',
        color: 'amber',
        bgClass: 'bg-amber-500/10 border-amber-500/20',
        textClass: 'text-amber-300',
        secondaryTextClass: 'text-amber-200',
        iconBg: 'bg-amber-600',
        icon: '🧠'
    }
};

// 系统角色配置
const SYSTEM_ROLES = {
    '业务分析师': { icon: '📊', color: 'purple', team: '需求分析团队' },
    '需求澄清专家': { icon: '🔍', color: 'blue', team: '需求分析团队' },
    '技术文档编写师': { icon: '📝', color: 'green', team: '需求分析团队' },
    '质量评审员': { icon: '✅', color: 'yellow', team: '质量保证团队' },
    '系统架构师': { icon: '🏗️', color: 'cyan', team: '架构设计团队' },
    '数据库设计师': { icon: '🗄️', color: 'indigo', team: '架构设计团队' },
    '技术选型专家': { icon: '⚙️', color: 'slate', team: '架构设计团队' },
    '系统': { icon: '⚡', color: 'gray', team: '系统核心' },
    '工作流程管理器': { icon: '📋', color: 'emerald', team: '系统核心' },
    '最终报告': { icon: '📄', color: 'blue', team: '文档输出' }
};

// LLM提供者配置
const LLM_PROVIDERS = {
    'deepseek': { icon: '🌊', name: 'DeepSeek', color: 'blue' },
    'openai': { icon: '🤖', name: 'OpenAI', color: 'green' },
    'anthropic': { icon: '🔮', name: 'Anthropic', color: 'purple' },
    'default': { icon: '🧠', name: 'AI引擎', color: 'amber' }
};

// 判断消息阵营
function getMessageCamp(messageType: string, agent?: string): keyof typeof CAMPS {
    if (messageType === 'user') return 'user';

    // 如果是LLM相关的消息
    if (agent && (agent.includes('LLM') || agent.includes('AI引擎') || agent.includes('模型'))) {
        return 'llm';
    }

    // 默认系统方
    return 'system';
}

// 获取角色信息
function getRoleInfo(agent?: string) {
    if (!agent) return null;
    return SYSTEM_ROLES[agent] || { icon: '🤖', color: 'gray', team: '系统核心' };
}

// 判断是否为进度消息（应该在进度面板显示而非聊天区域）
function isProgressMessage(content: string, agent?: string): boolean {
    // 明确排除最终结果和质量检查信息，即使它们可能包含某些关键词
    if (content.includes('需求分析完成') || content.includes('最终质量分数') || content.includes('质量评估完成')) {
        return false;
    }

    if (agent && (
        agent === '系统' ||
        agent === '工作流程管理器'
    )) {
        // 检查系统或工作流程管理器发出的具体进度消息模式
        return (
            content.includes('🚀 启动') ||
            content.includes('🤖 多智能体团队') ||
            content.includes('✅ 任务完成') ||
            content.includes('🔥 任务启动') ||
            content.includes('系统初始化') ||
            content.includes('分析目标')
        );
    }
    // 默认不认为是进度消息
    return false;
}

// 消息卡片组件 - 用于美化AI消息显示
function MessageCard({ content, agent }: { content: string; agent?: string }) {
    const [isExpanded, setIsExpanded] = useState(false);

    // 检测消息类型并返回相应的卡片样式
    const getMessageType = (content: string, agent?: string) => {
        if (content.includes('🚀') && (content.includes('初始化') || content.includes('启动'))) {
            return 'system-init';
        }
        if (content.includes('🤖') && content.includes('团队')) {
            return 'team-ready';
        }
        if (content.includes('📋') && content.includes('开始分析')) {
            return 'analysis-start';
        }
        if (content.includes('🔥') && content.includes('任务启动')) {
            return 'task-start';
        }
        if (content.includes('✅') && content.includes('完成')) {
            return 'task-complete';
        }
        if (content.includes('🎯') && content.includes('质量评估')) {
            return 'quality-check';
        }
        if (content.includes('🎉') && content.includes('需求分析完成')) {
            return 'final-result';
        }
        if (agent === '最终报告' || content.length > 200) {
            return 'detailed-report';
        }
        return 'default';
    };

    const messageType = getMessageType(content, agent);
    const camp = getMessageCamp('assistant', agent);
    const roleInfo = getRoleInfo(agent);

    // 系统初始化消息
    if (messageType === 'system-init') {
        return (
            <div className={`${CAMPS.system.bgClass} border rounded-lg p-3 flex items-center space-x-3`}>
                <div className={`w-8 h-8 ${CAMPS.system.iconBg} rounded-full flex items-center justify-center`}>
                    <span className="text-white text-sm">🚀</span>
                </div>
                <div className="flex-1">
                    <div className="flex items-center space-x-2">
                        <span className={`${CAMPS.system.textClass} font-medium text-sm`}>系统启动</span>
                        <span className="px-2 py-0.5 bg-green-500/20 text-green-300 rounded-full text-xs">OpenManus核心</span>
                    </div>
                    <div className={`${CAMPS.system.secondaryTextClass} text-xs`}>AI需求分析工作流初始化完成</div>
                </div>
            </div>
        );
    }

    // 团队就绪消息
    if (messageType === 'team-ready') {
        return (
            <div className={`${CAMPS.system.bgClass} border rounded-lg p-3 flex items-center space-x-3`}>
                <div className={`w-8 h-8 ${CAMPS.system.iconBg} rounded-full flex items-center justify-center`}>
                    <span className="text-white text-sm">🤖</span>
                </div>
                <div className="flex-1">
                    <div className="flex items-center space-x-2">
                        <span className={`${CAMPS.system.textClass} font-medium text-sm`}>智能体团队</span>
                        <span className="px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded-full text-xs">多智能体协作</span>
                    </div>
                    <div className={`${CAMPS.system.secondaryTextClass} text-xs`}>需求分析团队 • 质量保证团队 就绪</div>
                </div>
            </div>
        );
    }

    // 分析开始消息
    if (messageType === 'analysis-start') {
        const requirement = content.match(/：(.+)$/)?.[1] || '需求分析';
        return (
            <div className={`${CAMPS.system.bgClass} border rounded-lg p-3`}>
                <div className="flex items-center space-x-3 mb-2">
                    <div className={`w-8 h-8 ${CAMPS.system.iconBg} rounded-full flex items-center justify-center`}>
                        <span className="text-white text-sm">📋</span>
                    </div>
                    <div className="flex-1">
                        <div className="flex items-center space-x-2">
                            <span className={`${CAMPS.system.textClass} font-medium text-sm`}>需求分析启动</span>
                            <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 rounded-full text-xs">工作流程管理器</span>
                        </div>
                        <div className={`${CAMPS.system.secondaryTextClass} text-xs`}>开始智能化需求处理</div>
                    </div>
                </div>
                <div className="bg-gray-700/50 rounded px-3 py-2">
                    <div className="text-gray-300 text-sm font-medium">分析目标</div>
                    <div className="text-gray-400 text-xs mt-1">{requirement}</div>
                </div>
            </div>
        );
    }

    // 任务启动消息
    if (messageType === 'task-start') {
        const taskName = content.match(/🔥\s*(.+?)任务启动/)?.[1] || '任务';
        return (
            <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-2 flex items-center space-x-3">
                <div className="w-6 h-6 bg-yellow-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-xs">🔥</span>
                </div>
                <div className="flex-1">
                    <div className="flex items-center space-x-2">
                        <span className="text-yellow-300 font-medium text-sm">{taskName}</span>
                        <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-300 rounded-full text-xs">执行中</span>
                    </div>
                    <div className="text-yellow-200 text-xs">任务分配给专业角色处理...</div>
                </div>
                <div className="flex space-x-1">
                    <div className="w-1 h-1 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-1 h-1 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-1 h-1 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
            </div>
        );
    }

    // 任务完成消息
    if (messageType === 'task-complete') {
        const match = content.match(/✅\s*(.+?)完成.*?(\d+\.?\d*)/);
        const taskName = match?.[1] || '任务';
        const score = match?.[2] || '未评分';
        return (
            <div className={`${CAMPS.system.bgClass} border rounded-lg p-2 flex items-center space-x-3`}>
                <div className={`w-6 h-6 ${CAMPS.system.iconBg} rounded-full flex items-center justify-center`}>
                    <span className="text-white text-xs">✅</span>
                </div>
                <div className="flex-1">
                    <div className="flex items-center space-x-2">
                        <span className={`${CAMPS.system.textClass} font-medium text-sm`}>{taskName}完成</span>
                        <span className="px-2 py-0.5 bg-green-500/20 text-green-300 rounded-full text-xs">已交付</span>
                    </div>
                    <div className={`${CAMPS.system.secondaryTextClass} text-xs`}>质量分数: {score}/10</div>
                </div>
                <div className="text-green-400 text-xs font-bold">{score}</div>
            </div>
        );
    }

    // 质量评估消息
    if (messageType === 'quality-check') {
        const score = content.match(/(\d+)/)?.[1] || '0';
        return (
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm">🎯</span>
                </div>
                <div className="flex-1">
                    <div className="flex items-center space-x-2">
                        <span className="text-blue-300 font-medium text-sm">质量评估完成</span>
                        <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-300 rounded-full text-xs">质量保证团队</span>
                    </div>
                    <div className="text-blue-200 text-xs">综合质量分析结果</div>
                </div>
                <div className="text-right">
                    <div className="text-blue-300 font-bold text-lg">{score}</div>
                    <div className="text-blue-400 text-xs">/100</div>
                </div>
            </div>
        );
    }

    // 最终完成消息
    if (messageType === 'final-result') {
        const score = content.match(/(\d+)/)?.[1] || '0';
        return (
            <div className="bg-gradient-to-r from-green-500/20 to-blue-500/20 border border-green-500/30 rounded-lg p-4">
                <div className="flex items-center space-x-3 mb-3">
                    <div className="w-10 h-10 bg-gradient-to-r from-green-600 to-blue-600 rounded-full flex items-center justify-center">
                        <span className="text-white">🎉</span>
                    </div>
                    <div className="flex-1">
                        <div className="flex items-center space-x-2">
                            <span className="text-green-300 font-bold text-base">需求分析完成</span>
                            <span className="px-2 py-0.5 bg-gradient-to-r from-green-500/20 to-blue-500/20 text-green-300 rounded-full text-xs">OpenManus团队协作</span>
                        </div>
                        <div className="text-gray-300 text-sm">多智能体 × LLM引擎 协作成功</div>
                    </div>
                </div>
                <div className="bg-gray-700/30 rounded-lg p-3 text-center">
                    <div className="text-3xl font-bold text-green-400">{score}</div>
                    <div className="text-gray-400 text-sm">最终质量分数 /100</div>
                </div>
            </div>
        );
    }

    // 详细报告消息 - 支持折叠展开
    if (messageType === 'detailed-report') {
        const previewLength = 300;
        const isLongContent = content.length > previewLength;
        const displayContent = isExpanded ? content : (isLongContent ? content.substring(0, previewLength) + '...' : content);

        return (
            <div className="bg-gray-700/30 rounded-lg border border-gray-600/50">
                <div className="bg-gray-700/50 px-4 py-2 rounded-t-lg border-b border-gray-600/50">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                            <span className="text-lg">{roleInfo?.icon || '📄'}</span>
                            <div className="flex flex-col">
                                <div className="flex items-center space-x-2">
                                    <span className="text-gray-300 font-medium text-sm">{agent || '详细报告'}</span>
                                    {roleInfo?.team && (
                                        <span className={`px-2 py-0.5 bg-${roleInfo.color}-500/20 text-${roleInfo.color}-300 rounded-full text-xs`}>
                                            {roleInfo.team}
                                        </span>
                                    )}
                                </div>
                                {isLongContent && (
                                    <span className="text-xs text-gray-500">
                                        ({content.length} 字符)
                                    </span>
                                )}
                            </div>
                        </div>
                        {isLongContent && (
                            <button
                                onClick={() => setIsExpanded(!isExpanded)}
                                className="text-blue-400 hover:text-blue-300 text-xs font-medium transition-colors"
                            >
                                {isExpanded ? '收缩 ↑' : '展开 ↓'}
                            </button>
                        )}
                    </div>
                </div>
                <div className={`p-4 ${isExpanded ? 'max-h-none' : 'max-h-96 overflow-hidden'}`}>
                    <ReactMarkdown
                        className="prose prose-sm max-w-none prose-invert"
                        components={{
                            p: ({ children }) => <p className="mb-2 last:mb-0 text-gray-300">{children}</p>,
                            ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1 text-gray-300">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1 text-gray-300">{children}</ol>,
                            li: ({ children }) => <li className="text-gray-300">{children}</li>,
                            strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
                            h1: ({ children }) => <h1 className="text-xl font-bold text-white mb-3">{children}</h1>,
                            h2: ({ children }) => <h2 className="text-lg font-bold text-white mb-2">{children}</h2>,
                            h3: ({ children }) => <h3 className="text-base font-bold text-white mb-2">{children}</h3>,
                        }}
                    >
                        {displayContent}
                    </ReactMarkdown>
                    {isLongContent && !isExpanded && (
                        <div className="mt-3 text-center">
                            <button
                                onClick={() => setIsExpanded(true)}
                                className="bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 px-4 py-2 rounded-lg text-sm transition-colors"
                            >
                                查看完整内容 ({content.length - previewLength}+ 字符)
                            </button>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    // 默认样式 - 根据阵营显示
    const campConfig = CAMPS[camp];
    return (
        <div className={`${campConfig.bgClass} border rounded-lg p-3 flex items-center space-x-3`}>
            <div className={`w-6 h-6 ${campConfig.iconBg} rounded-full flex items-center justify-center`}>
                <span className="text-white text-xs">{roleInfo?.icon || campConfig.icon}</span>
            </div>
            <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                    <span className={`${campConfig.textClass} font-medium text-sm`}>{agent || campConfig.name}</span>
                    {roleInfo?.team && (
                        <span className={`px-2 py-0.5 bg-${roleInfo.color}-500/20 text-${roleInfo.color}-300 rounded-full text-xs`}>
                            {roleInfo.team}
                        </span>
                    )}
                </div>
                <div className="text-gray-300 text-sm">{content}</div>
            </div>
        </div>
    );
}

// 添加进度指示器组件
function ProgressIndicator({ progress, status }: { progress: number; status: string }) {
    return (
        <div className="flex items-center space-x-2 my-2">
            <div className="flex-1 bg-gray-700 rounded-full h-2">
                <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${progress}%` }}
                />
            </div>
            <span className="text-gray-400 text-xs">{status}</span>
        </div>
    );
}

// 添加智能体状态指示器
function AgentStatusIndicator({ agent, status }: { agent: string; status: 'idle' | 'working' | 'done' }) {
    const roleInfo = getRoleInfo(agent);
    const statusColors = {
        idle: 'bg-gray-500',
        working: 'bg-yellow-500 animate-pulse',
        done: 'bg-green-500'
    };

    return (
        <div className="flex items-center space-x-2 text-xs">
            <span className={`w-2 h-2 rounded-full ${statusColors[status]}`} />
            <span className="text-gray-300">{agent}</span>
            <span className="text-gray-500">{roleInfo?.team}</span>
        </div>
    );
}

// 添加错误提示组件
function ErrorMessage({ message, onRetry }: { message: string; onRetry?: () => void }) {
    return (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
            <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center">
                    <span className="text-white">⚠️</span>
                </div>
                <div className="flex-1">
                    <div className="text-red-300 font-medium">出错了</div>
                    <div className="text-red-200 text-sm">{message}</div>
                </div>
                {onRetry && (
                    <button
                        onClick={onRetry}
                        className="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg text-sm transition-colors"
                    >
                        重试
                    </button>
                )}
            </div>
        </div>
    );
}

// 添加提示组件
function Tooltip({ content, children }: { content: string; children: React.ReactNode }) {
    return (
        <div className="group relative">
            {children}
            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                {content}
            </div>
        </div>
    );
}

// 修改消息输入组件
function MessageInput({ onSubmit, disabled }: { onSubmit: (text: string) => void; disabled?: boolean }) {
    const [text, setText] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // 自动调整文本框高度
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [text]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (text.trim()) {
            onSubmit(text.trim());
            setText('');
        }
    };

    return (
        <form onSubmit={handleSubmit} className="relative">
            <textarea
                ref={textareaRef}
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="请输入您的需求描述..."
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition-colors resize-none min-h-[40px] max-h-[200px]"
                rows={1}
                disabled={disabled}
            />
            <Tooltip content="发送消息">
                <button
                    type="submit"
                    className="absolute right-2 bottom-2 p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors rounded-lg"
                    disabled={disabled || !text.trim()}
                    aria-label="发送"
                >
                    <PaperAirplaneIcon className="w-5 h-5" />
                </button>
            </Tooltip>
        </form>
    );
}

// 修改主聊天界面组件
export function ChatInterface() {
    const {
        messages,
        isProcessing,
        currentAgent,
        progress,
        error,
        clearError,
        sendMessage // Use sendMessage directly from context
    } = useRequirementsContext();

    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === 'function') {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    // 局部 handleSubmit 现在直接调用 Context 提供的 sendMessage
    const handleSubmit = (text: string) => {
        sendMessage(text);
    };

    const handleRetry = () => {
        // 目前简单清除错误，实际可能需要重试上次的请求
        clearError();
        // TODO: 实现重试逻辑，例如重新触发上次的分析请求
    };

    return (
        <div className="flex flex-col h-full bg-gray-800 rounded-lg shadow-xl overflow-hidden relative">
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
                <h2 className="text-xl font-semibold text-white">需求分析助手</h2>
                {isProcessing && (
                    <div className="flex items-center space-x-2 text-gray-400 text-sm">
                        <ArrowPathIcon className="h-5 w-5 animate-spin" />
                        <span>{currentAgent || '系统处理中'}</span>
                    </div>
                )}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar" style={{ scrollBehavior: 'smooth' }}>
                {messages.map((msg, index) => (
                    <div key={index} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[70%] rounded-lg p-3 shadow-md relative ${CAMPS[getMessageCamp(msg.type, msg.agent)].bgClass} border ${msg.type === 'user' ? 'rounded-br-none' : 'rounded-bl-none'}`}>
                            <div className={`flex items-center mb-1 ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`w-6 h-6 rounded-full flex items-center justify-center mr-2 ${CAMPS[getMessageCamp(msg.type, msg.agent)].iconBg}`}>
                                    <span className="text-white text-xs">
                                        {msg.type === 'user' ? CAMPS.user.icon : (getRoleInfo(msg.agent)?.icon || CAMPS.system.icon)}
                                    </span>
                                </div>
                                <span className={`text-sm font-semibold ${CAMPS[getMessageCamp(msg.type, msg.agent)].textClass}`}>
                                    {msg.type === 'user' ? CAMPS.user.name : (msg.agent || CAMPS.system.name)}
                                </span>
                            </div>
                            <div className={`${CAMPS[getMessageCamp(msg.type, msg.agent)].secondaryTextClass} text-sm whitespace-pre-wrap markdown-content`}>
                                {msg.isAnswer ? (
                                    <span className="italic">（回答）</span>
                                ) : null}
                                <ReactMarkdown>
                                    {msg.content}
                                </ReactMarkdown>
                            </div>
                            <div className={`absolute bottom-1 ${msg.type === 'user' ? 'left-2 text-xs text-gray-400' : 'right-2 text-xs text-gray-400'}`}>
                                {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </div>
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            {error && <ErrorMessage message={error} onRetry={handleRetry} />}

            <div className="p-4 border-t border-gray-700">
                <MessageInput onSubmit={handleSubmit} disabled={isProcessing} />
            </div>

            {/* 其他辅助面板和进度/状态指示 */}
            <div className="absolute bottom-20 right-4 w-60 p-3 bg-gray-700/80 rounded-lg shadow-lg backdrop-blur-sm z-10">
                <h3 className="text-white text-sm font-semibold mb-2">处理状态</h3>
                <ProgressIndicator progress={progress} status={isProcessing ? '处理中' : '空闲'} />
                <AgentStatusIndicator agent={currentAgent || '无'} status={isProcessing ? 'working' : 'idle'} />
            </div>
        </div>
    );
}
