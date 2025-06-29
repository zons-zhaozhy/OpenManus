import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { requirementsApi } from '../../utils/api';

interface ClarificationQuestion {
    id: string;
    text: string;
    category: string;
    priority: string;
}

interface ClarificationSession {
    id: string;
    questions: ClarificationQuestion[];
    answers: { [key: string]: string };
    status: string;
}

interface Message {
    type: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
    agent?: string;
    isAnswer?: boolean;
}

interface Agent {
    id: string;
    name: string;
    icon: string;
    color: string;
    status: string;
    description: string;
}

interface RequirementsContextType {
    // 基础状态
    currentInput: string;
    setCurrentInput: (input: string) => void;
    session: ClarificationSession | null;
    setSession: (session: ClarificationSession | null) => void;
    chatHistory: Message[];
    setChatHistory: React.Dispatch<React.SetStateAction<Message[]>>;
    activeTab: string;
    setActiveTab: (tab: string) => void;
    analysisMetrics: any;
    setAnalysisMetrics: (metrics: any) => void;

    // 显示控制
    showScientificPanel: boolean;
    setShowScientificPanel: (show: boolean) => void;
    showThinkActReflect: boolean;
    setShowThinkActReflect: (show: boolean) => void;
    showSSETest: boolean;
    setShowSSETest: (show: boolean) => void;
    showTaskLifecycle: boolean;
    setShowTaskLifecycle: (show: boolean) => void;

    // 分析相关
    analysisMode: 'quick' | 'standard' | 'deep' | 'workflow';
    setAnalysisMode: (mode: 'quick' | 'standard' | 'deep' | 'workflow') => void;
    thinkActReflectData: any;
    setThinkActReflectData: (data: any) => void;

    // 工作流程状态
    currentWorkflowStage: string;
    setCurrentWorkflowStage: (stage: string) => void;
    workflowProgress: number;
    setWorkflowProgress: (progress: number) => void;
    workflowInsights: string[];
    setWorkflowInsights: React.Dispatch<React.SetStateAction<string[]>>;
    workflowSummary: any;
    setWorkflowSummary: (summary: any) => void;
    taskTree: any;
    setTaskTree: (tree: any) => void;

    // 智能体状态
    agents: Agent[];
    setAgents: React.Dispatch<React.SetStateAction<Agent[]>>;

    // 计算属性
    totalQuestions: number;
    answeredQuestions: number;
    completionRate: number;
    isLoading: boolean;

    // 操作方法
    handleSubmit: (e: React.FormEvent) => void;
    clearSession: () => void;
    startWorkflowAnalysisMutation: any;
    startAnalysisMutation: any;

    // 人工输入相关
    isWaitingForHumanInput: boolean;
    setIsWaitingForHumanInput: (waiting: boolean) => void;
    currentQuestion: string | null;
    setCurrentQuestion: (question: string | null) => void;
    handleHumanInput: (input: string) => void;

    // 消息相关
    messages: Message[];
    sendMessage: (text: string) => Promise<void>;
    isProcessing: boolean;
    currentAgent: string | null;
    progress: number;
    error: string | null;
    clearError: () => void;
}

const RequirementsContext = createContext<RequirementsContextType | null>(null);

// 在文件开头添加一个辅助函数来创建类型安全的消息对象
function createMessage(type: 'user' | 'assistant' | 'system', content: string, agent?: string): Message {
    return {
        type,
        content,
        timestamp: new Date(),
        agent
    };
}

export function RequirementsPageProvider({ children }: { children: React.ReactNode }) {
    // 基础状态
    const [currentInput, setCurrentInput] = useState(() => localStorage.getItem('reqPage_currentInput') || '');
    const [session, setSession] = useState<ClarificationSession | null>(() => {
        const savedSession = localStorage.getItem('reqPage_session');
        return savedSession ? JSON.parse(savedSession) : null;
    });
    const [chatHistory, setChatHistory] = useState<Message[]>(() => {
        const savedChatHistory = localStorage.getItem('reqPage_chatHistory');
        return savedChatHistory ? JSON.parse(savedChatHistory).map((msg: any) => ({ ...msg, timestamp: new Date(msg.timestamp) })) : [];
    });
    const [activeTab, setActiveTab] = useState(() => localStorage.getItem('reqPage_activeTab') || 'clarifier');
    const [analysisMetrics, setAnalysisMetrics] = useState<any>(() => {
        const savedMetrics = localStorage.getItem('reqPage_analysisMetrics');
        return savedMetrics ? JSON.parse(savedMetrics) : null;
    });

    // 显示控制
    const [showScientificPanel, setShowScientificPanel] = useState(() => localStorage.getItem('reqPage_showScientificPanel') === 'true');
    const [showThinkActReflect, setShowThinkActReflect] = useState(() => localStorage.getItem('reqPage_showThinkActReflect') === 'true');
    const [showSSETest, setShowSSETest] = useState(() => localStorage.getItem('dev_showSSETest') === 'true');
    const [showTaskLifecycle, setShowTaskLifecycle] = useState(false);

    // 分析相关
    const [analysisMode, setAnalysisMode] = useState<'quick' | 'standard' | 'deep' | 'workflow'>(() => {
        const savedMode = localStorage.getItem('reqPage_analysisMode');
        return (savedMode as 'quick' | 'standard' | 'deep' | 'workflow') || 'standard';
    });
    const [thinkActReflectData, setThinkActReflectData] = useState<any>(() => {
        const savedTarData = localStorage.getItem('reqPage_thinkActReflectData');
        return savedTarData ? JSON.parse(savedTarData) : null;
    });

    // 工作流程状态
    const [currentWorkflowStage, setCurrentWorkflowStage] = useState<string>('');
    const [workflowProgress, setWorkflowProgress] = useState<number>(0);
    const [workflowInsights, setWorkflowInsights] = useState<string[]>([]);
    const [workflowSummary, setWorkflowSummary] = useState<any>(null);
    const [taskTree, setTaskTree] = useState<any>(null);

    // 智能体状态 - 与后端任务流程保持一致
    const [agents, setAgents] = useState<Agent[]>(() => [
        {
            id: 'business_analyst',
            name: '业务分析师',
            icon: '📊',
            color: 'purple',
            status: 'waiting',
            description: '需求理解和业务建模'
        },
        {
            id: 'requirement_clarifier',
            name: '需求澄清专家',
            icon: '🔍',
            color: 'blue',
            status: 'waiting',
            description: '识别模糊点，生成澄清问题'
        },
        {
            id: 'technical_writer',
            name: '技术文档编写师',
            icon: '📝',
            color: 'green',
            status: 'waiting',
            description: '生成需求规格说明书'
        },
        {
            id: 'quality_reviewer',
            name: '质量评审员',
            icon: '✅',
            color: 'yellow',
            status: 'waiting',
            description: '评审需求分析质量和完整性'
        }
    ]);

    // 人工输入状态
    const [isWaitingForHumanInput, setIsWaitingForHumanInput] = useState(false);
    const [currentQuestion, setCurrentQuestion] = useState<string | null>(null);

    // 持久化状态
    useEffect(() => {
        localStorage.setItem('reqPage_currentInput', currentInput);
    }, [currentInput]);

    useEffect(() => {
        localStorage.setItem('reqPage_session', JSON.stringify(session));
    }, [session]);

    useEffect(() => {
        localStorage.setItem('reqPage_chatHistory', JSON.stringify(chatHistory));
    }, [chatHistory]);

    useEffect(() => {
        localStorage.setItem('reqPage_activeTab', activeTab);
    }, [activeTab]);

    useEffect(() => {
        localStorage.setItem('reqPage_analysisMetrics', JSON.stringify(analysisMetrics));
    }, [analysisMetrics]);

    useEffect(() => {
        localStorage.setItem('reqPage_showScientificPanel', String(showScientificPanel));
    }, [showScientificPanel]);

    useEffect(() => {
        localStorage.setItem('reqPage_showThinkActReflect', String(showThinkActReflect));
    }, [showThinkActReflect]);

    useEffect(() => {
        localStorage.setItem('dev_showSSETest', String(showSSETest));
    }, [showSSETest]);

    useEffect(() => {
        localStorage.setItem('reqPage_analysisMode', analysisMode);
    }, [analysisMode]);

    useEffect(() => {
        localStorage.setItem('reqPage_thinkActReflectData', JSON.stringify(thinkActReflectData));
    }, [thinkActReflectData]);

    // 新增的处理状态字段，放到所有 useMutation 之前
    const [messages, setMessages] = useState<Message[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [currentAgent, setCurrentAgent] = useState<string | null>(null);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);

    // 清除错误
    const clearError = useCallback(() => {
        setError(null);
    }, []);

    // 错误自动清除机制
    useEffect(() => {
        if (error) {
            const timer = setTimeout(() => {
                clearError();
            }, 5000); // 5秒后自动清除错误
            return () => clearTimeout(timer);
        }
    }, [error, clearError]);

    // 开始需求分析
    const startAnalysisMutation = useMutation({
        mutationFn: async (content: string) => {
            setError(null); // Clear previous errors
            setIsProcessing(true);
            setCurrentAgent(null); // Reset agent on new analysis start
            setProgress(0);

            try {
                const response = await requirementsApi.analyzeRequirement(content);
                // 假设后端会返回一个包含消息和状态的结构
                if (response.message) {
                    const newMessages = [{
                        type: 'assistant' as const,
                        content: response.message,
                        agent: '系统',
                        timestamp: new Date()
                    }];
                    setMessages(prev => [...prev, ...newMessages]);
                }
                setProgress(100);
                return response;
            } catch (error: any) {
                console.error('需求分析请求失败:', error);
                const errorMessage = error.response?.data?.message || error.message || '需求分析失败，请重试';
                setError(errorMessage);
                throw error; // Re-throw to propagate error to useMutation's onError
            } finally {
                setIsProcessing(false);
                setCurrentAgent(null);
            }
        }
    });

    const startWorkflowAnalysisMutation = useMutation({
        mutationFn: async (content: string) => {
            setError(null); // Clear previous errors
            setIsProcessing(true);
            setCurrentAgent(null); // Reset agent on new analysis start
            setProgress(0);

            try {
                const response = await requirementsApi.analyzeWorkflow(content);
                if (response.status === 'success') {
                    const successMessage: Message = {
                        type: 'system',
                        content: response.message || '工作流分析完成！',
                        timestamp: new Date(),
                        agent: '系统'
                    };
                    setChatHistory(prev => [...prev, successMessage]);

                    if (response.result) {
                        const analysisContent = response.result.final_result || response.result.analysis || JSON.stringify(response.result, null, 2);
                        const analysisMessage: Message = {
                            type: 'system',
                            content: `详细工作流分析结果：\n\`\`\`json\n${analysisContent}\n\`\`\``,
                            timestamp: new Date(),
                            agent: '最终报告'
                        };
                        setChatHistory(prev => [...prev, analysisMessage]);
                    }
                } else if (response.status === 'processing') {
                    const processingUpdateMessage: Message = {
                        type: 'system',
                        content: response.message || `工作流分析正在进行中... (${response.progress?.current_stage || ''}`,
                        timestamp: new Date(),
                        agent: '系统'
                    };
                    setChatHistory(prev => [...prev, processingUpdateMessage]);
                } else if (response.status === 'error') {
                    const errorMessage: Message = {
                        type: 'system',
                        content: response.message || `工作流分析失败：${response.result?.error || '未知错误'}`,
                        timestamp: new Date(),
                        agent: '系统'
                    };
                    setChatHistory(prev => [...prev, errorMessage]);
                }

                // 更新会话状态
                if (response.session) {
                    setSession(response.session);
                }
                setProgress(100);
                return response;
            } catch (error: any) {
                console.error('工作流分析请求失败:', error);
                const errorMessage = error.response?.data?.message || error.message || '工作流分析失败，请重试';
                setError(errorMessage);
                const detailedErrorMessage: Message = {
                    type: 'system',
                    content: `工作流分析请求失败。错误信息: ${error.message || '未知错误'}. 请检查后端服务或稍后重试。`,
                    timestamp: new Date(),
                    agent: '系统'
                };
                setChatHistory(prev => [...prev, detailedErrorMessage]);
                throw error; // Re-throw to propagate error to useMutation's onError
            } finally {
                setIsProcessing(false);
                setCurrentAgent(null);
            }
        }
    });

    const isLoading = startWorkflowAnalysisMutation.isPending || startAnalysisMutation.isPending;

    // 发送消息 - 此函数现在是触发分析的主要入口，接收文本内容
    const sendMessage = useCallback(async (text: string) => {
        try {
            clearError(); // Clear previous errors
            setIsProcessing(true); // Set processing state
            setCurrentAgent(null); // Reset agent on new analysis start
            setProgress(0); // Reset progress

            // Add user message to chat history and messages state
            const userMessage: Message = {
                type: 'user',
                content: text,
                timestamp: new Date()
            };
            setChatHistory(prev => [...prev, userMessage]);
            setMessages(prev => [...prev, userMessage]);

            // 根据分析模式选择不同的处理方式
            if (analysisMode === 'workflow') {
                await startWorkflowAnalysisMutation.mutateAsync(text); // Use mutateAsync to await completion
            } else {
                await startAnalysisMutation.mutateAsync(text); // Use mutateAsync to await completion
            }
        } catch (err: any) {
            console.error('需求分析失败:', err);
            const errorMessage = err.response?.data?.message || err.message || '需求分析失败，请重试';
            setError(errorMessage);
            // Add error message to messages state for display in ChatInterface
            const errorMsg: Message = {
                type: 'system',
                content: `分析失败：${errorMessage}`,
                timestamp: new Date(),
                agent: '系统'
            };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            // The processing state and current agent are already managed within mutationFn or onError callbacks
            // But explicitly set them to false/null here as a fallback or for final state if not already done by mutation
            setIsProcessing(false);
            setCurrentAgent(null);
            // Progress should be 100 on success, or remain at error state if failed
            // No need to set progress here if it's managed by mutation callbacks
        }
    }, [clearError, analysisMode, startWorkflowAnalysisMutation, startAnalysisMutation]);

    // handleSubmit 现在只处理表单提交事件，并调用 sendMessage
    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!currentInput.trim() || isLoading) return;

        // Call sendMessage with the current input value
        sendMessage(currentInput.trim());

        setCurrentInput(''); // Clear input after submission
    };

    // 新建会话功能
    const clearSession = () => {
        // 清理状态
        setSession(null);
        setChatHistory([]);
        setCurrentInput('');
        setAnalysisMetrics(null);
        setThinkActReflectData(null);
        setWorkflowSummary(null);
        setTaskTree(null);
        setCurrentWorkflowStage('初始化');
        setWorkflowProgress(0);
        setWorkflowInsights([]);

        // 重置智能体状态
        setAgents([
            {
                id: 'business_analyst',
                name: '业务分析师',
                icon: '📊',
                color: 'purple',
                status: 'waiting',
                description: '需求理解和业务建模'
            },
            {
                id: 'requirement_clarifier',
                name: '需求澄清专家',
                icon: '🔍',
                color: 'blue',
                status: 'waiting',
                description: '识别模糊点，生成澄清问题'
            },
            {
                id: 'technical_writer',
                name: '技术文档编写师',
                icon: '📝',
                color: 'green',
                status: 'waiting',
                description: '生成需求规格说明书'
            },
            {
                id: 'quality_reviewer',
                name: '质量评审员',
                icon: '✅',
                color: 'yellow',
                status: 'waiting',
                description: '评审需求分析质量和完整性'
            }
        ]);

        // 清理本地存储
        localStorage.removeItem('reqPage_session');
        localStorage.removeItem('reqPage_chatHistory');
        localStorage.removeItem('reqPage_currentInput');
        localStorage.removeItem('reqPage_analysisMetrics');
        localStorage.removeItem('reqPage_thinkActReflectData');

        console.log('🔄 新建会话：所有状态已重置');
    };

    // 处理人工输入
    const handleHumanInput = async (input: string) => {
        if (!isWaitingForHumanInput || isLoading) return; // Add isLoading check

        // 添加用户回答到聊天历史
        const userMessage: Message = {
            type: 'user',
            content: input,
            timestamp: new Date(), // Keep as Date object
            isAnswer: true
        };
        setChatHistory(prev => [...prev, userMessage]);
        setMessages(prev => [...prev, userMessage]); // Also update 'messages' state

        // 发送用户回答到后端
        setIsProcessing(true); // Set processing state
        setError(null); // Clear previous errors
        setCurrentAgent('系统处理中'); // Indicate system is processing user input
        setProgress(0); // Reset progress

        try {
            const response = await requirementsApi.processAnswer(input);

            // 更新会话状态
            if (response.session) {
                setSession(response.session);
            }

            // 添加系统回复到聊天历史 (assuming response.message is the main system reply)
            if (response.message) {
                const systemMessage: Message = {
                    type: 'system',
                    content: response.message,
                    timestamp: new Date()
                };
                setChatHistory(prev => [...prev, systemMessage]);
                setMessages(prev => [...prev, systemMessage]); // Also update 'messages' state
            }

            // If the response contains further questions, update currentQuestion and isWaitingForHumanInput
            if (response.next_question) { // Assuming backend returns next_question if more input is needed
                setCurrentQuestion(response.next_question);
                setIsWaitingForHumanInput(true);
                setProgress(50); // Mid-progress for waiting for next input
            } else {
                // 重置等待状态
                setIsWaitingForHumanInput(false);
                setCurrentQuestion(null);
                setProgress(100); // Complete progress if no more questions
            }

        } catch (error: any) {
            console.error('处理用户回答时出错:', error);
            const errorMessageText = error.response?.data?.message || error.message || '处理回答时出现错误，请重试';
            setError(errorMessageText); // Use centralized error state
            // 添加错误消息到聊天历史
            const errorMessage: Message = {
                type: 'system',
                content: `处理回答时出现错误: ${errorMessageText}`,
                timestamp: new Date()
            };
            setChatHistory(prev => [...prev, errorMessage]);
            setMessages(prev => [...prev, errorMessage]); // Also update 'messages' state
        } finally {
            // Only set processing to false if no more human input is expected
            if (!isWaitingForHumanInput) {
                setIsProcessing(false);
                setCurrentAgent(null);
            }
        }
    };

    return (
        <RequirementsContext.Provider value={{
            currentInput,
            setCurrentInput,
            session,
            setSession,
            chatHistory,
            setChatHistory,
            activeTab,
            setActiveTab,
            analysisMetrics,
            setAnalysisMetrics,
            showScientificPanel,
            setShowScientificPanel,
            showThinkActReflect,
            setShowThinkActReflect,
            showSSETest,
            setShowSSETest,
            showTaskLifecycle,
            setShowTaskLifecycle,
            analysisMode,
            setAnalysisMode,
            thinkActReflectData,
            setThinkActReflectData,
            currentWorkflowStage,
            setCurrentWorkflowStage,
            workflowProgress,
            setWorkflowProgress,
            workflowInsights,
            setWorkflowInsights,
            workflowSummary,
            setWorkflowSummary,
            taskTree,
            setTaskTree,
            agents,
            setAgents,
            totalQuestions: session?.questions?.length || 0,
            answeredQuestions: session ? Object.keys(session.answers).length : 0,
            completionRate: session ? Math.round((Object.keys(session.answers).length / session.questions.length) * 100) : 0,
            isLoading,
            handleSubmit,
            clearSession,
            startWorkflowAnalysisMutation,
            startAnalysisMutation,
            isWaitingForHumanInput,
            setIsWaitingForHumanInput,
            currentQuestion,
            setCurrentQuestion,
            handleHumanInput,
            messages,
            sendMessage,
            isProcessing,
            currentAgent,
            progress,
            error,
            clearError
        }}>
            {children}
        </RequirementsContext.Provider>
    );
}

export function useRequirementsContext() {
    const context = useContext(RequirementsContext);
    if (context === undefined) {
        throw new Error('useRequirementsContext must be used within a RequirementsPageProvider');
    }
    return context;
}
