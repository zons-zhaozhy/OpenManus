import React from 'react';

interface ClarificationQuestion {
    id: string;
    text: string;
    category: string;
    priority: string;
    quickAnswers?: string[];
}

interface Message {
    type: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

interface RequirementChatProps {
    messages: Message[];
    questions: ClarificationQuestion[];
    onAnswerQuestion: (questionId: string, answer: string) => void;
    isLoading?: boolean;
    mode?: 'quick' | 'standard' | 'deep';
    onModeChange?: (mode: 'quick' | 'standard' | 'deep') => void;
}

export const RequirementChat: React.FC<RequirementChatProps> = ({
    messages,
    questions,
    onAnswerQuestion,
    isLoading = false,
    mode = 'standard',
    onModeChange
}) => {
    const [currentAnswers, setCurrentAnswers] = React.useState<Record<string, string>>({});

    const handleAnswerChange = (questionId: string, answer: string) => {
        setCurrentAnswers(prev => ({ ...prev, [questionId]: answer }));
    };

    const handleSubmitAnswer = (questionId: string) => {
        const answer = currentAnswers[questionId];
        if (answer?.trim()) {
            onAnswerQuestion(questionId, answer);
            setCurrentAnswers(prev => ({ ...prev, [questionId]: '' }));
        }
    };

    const handleQuickAnswer = (questionId: string, answer: string) => {
        onAnswerQuestion(questionId, answer);
        setCurrentAnswers(prev => ({ ...prev, [questionId]: '' }));
    };

    return (
        <div className="space-y-4">
            {onModeChange && (
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                    <h3 className="text-sm font-medium text-gray-700 mb-2">分析模式</h3>
                    <div className="flex space-x-2">
                        <button
                            onClick={() => onModeChange('quick')}
                            className={`px-3 py-1 text-sm rounded-full ${mode === 'quick'
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            快速模式
                        </button>
                        <button
                            onClick={() => onModeChange('standard')}
                            className={`px-3 py-1 text-sm rounded-full ${mode === 'standard'
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            标准模式
                        </button>
                        <button
                            onClick={() => onModeChange('deep')}
                            className={`px-3 py-1 text-sm rounded-full ${mode === 'deep'
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            深度模式
                        </button>
                    </div>
                    <div className="mt-2 text-xs text-gray-500">
                        {mode === 'quick' && '快速模式：5秒内完成分析，适合简单需求'}
                        {mode === 'standard' && '标准模式：10秒内完成分析，平衡效率和深度'}
                        {mode === 'deep' && '深度模式：15秒内完成全面分析，适合复杂需求'}
                    </div>
                </div>
            )}

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div className="space-y-4 max-h-96 overflow-y-auto">
                    {messages.map((message, index) => (
                        <div
                            key={index}
                            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${message.type === 'user'
                                    ? 'bg-blue-500 text-white'
                                    : 'bg-gray-100 text-gray-800'
                                    }`}
                            >
                                <p className="text-sm">{message.content}</p>
                                <p className="text-xs mt-1 opacity-70">
                                    {message.timestamp.toLocaleTimeString()}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {isLoading && (
                <div className="flex justify-center items-center py-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                    <span className="ml-2 text-sm text-gray-600">正在分析您的需求...</span>
                </div>
            )}

            {questions.length > 0 && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                    <h3 className="font-medium text-gray-900 mb-3">需要澄清的问题</h3>
                    <div className="space-y-4">
                        {questions.map(question => (
                            <div key={question.id} className="bg-gray-50 p-4 rounded-lg">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                                        {question.category}
                                    </span>
                                    <span
                                        className={`text-xs px-2 py-1 rounded-full font-medium ${question.priority === 'high'
                                            ? 'bg-red-100 text-red-800'
                                            : question.priority === 'medium'
                                                ? 'bg-yellow-100 text-yellow-800'
                                                : 'bg-green-100 text-green-800'
                                            }`}
                                    >
                                        {question.priority === 'high' ? '重要' : question.priority === 'medium' ? '普通' : '可选'}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-700 mb-3">{question.text}</p>

                                {question.quickAnswers && question.quickAnswers.length > 0 && (
                                    <div className="mb-3 flex flex-wrap gap-2">
                                        {question.quickAnswers.map((answer, index) => (
                                            <button
                                                key={index}
                                                onClick={() => handleQuickAnswer(question.id, answer)}
                                                className="text-xs px-3 py-1 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200"
                                            >
                                                {answer}
                                            </button>
                                        ))}
                                    </div>
                                )}

                                <div className="flex space-x-2">
                                    <input
                                        type="text"
                                        value={currentAnswers[question.id] || ''}
                                        onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                                        onKeyPress={(e) => e.key === 'Enter' && handleSubmitAnswer(question.id)}
                                        placeholder="请输入您的回答..."
                                        className="flex-1 text-sm border border-gray-300 rounded-lg px-3 py-2 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                                    />
                                    <button
                                        onClick={() => handleSubmitAnswer(question.id)}
                                        disabled={!currentAnswers[question.id]?.trim()}
                                        className="px-4 py-2 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                    >
                                        回答
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {messages.length === 0 && questions.length === 0 && !isLoading && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
                    <div className="text-gray-400 mb-4">
                        <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                        </svg>
                    </div>
                    <p className="text-gray-500 text-sm">请开始描述您的需求，我会帮您分析和澄清</p>
                    <p className="text-gray-400 text-xs mt-2">支持多轮对话，帮助您更好地表达需求</p>
                </div>
            )}
        </div>
    );
};
