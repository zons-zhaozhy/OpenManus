import React from 'react';

interface ClarificationQuestion {
    id: string;
    text: string;
    category: string;
    priority: string;
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
}

export const RequirementChat: React.FC<RequirementChatProps> = ({
    messages,
    questions,
    onAnswerQuestion
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

    return (
        <div className="space-y-4">
            {/* 聊天历史 */}
            {messages.map((message, index) => (
                <div
                    key={index}
                    className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                    <div
                        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${message.type === 'user'
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-200 text-gray-800'
                            }`}
                    >
                        <p className="text-sm">{message.content}</p>
                        <p className="text-xs mt-1 opacity-70">
                            {message.timestamp.toLocaleTimeString()}
                        </p>
                    </div>
                </div>
            ))}

            {/* 澄清问题 */}
            {questions.length > 0 && (
                <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-medium text-gray-900 mb-3">澄清问题</h3>
                    <div className="space-y-3">
                        {questions.map(question => (
                            <div key={question.id} className="bg-white p-3 rounded border">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-xs text-gray-500 uppercase tracking-wide">
                                        {question.category}
                                    </span>
                                    <span className={`text-xs px-2 py-1 rounded ${question.priority === 'high'
                                        ? 'bg-red-100 text-red-800'
                                        : question.priority === 'medium'
                                            ? 'bg-yellow-100 text-yellow-800'
                                            : 'bg-green-100 text-green-800'
                                        }`}>
                                        {question.priority}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-700 mb-3">{question.text}</p>
                                <div className="flex space-x-2">
                                    <input
                                        type="text"
                                        value={currentAnswers[question.id] || ''}
                                        onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                                        placeholder="请输入您的回答..."
                                        className="flex-1 text-sm border border-gray-300 rounded px-2 py-1 focus:border-blue-500 focus:outline-none"
                                    />
                                    <button
                                        onClick={() => handleSubmitAnswer(question.id)}
                                        disabled={!currentAnswers[question.id]?.trim()}
                                        className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                                    >
                                        回答
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* 空状态 */}
            {messages.length === 0 && questions.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                    <p>请开始描述您的需求，我会帮您分析和澄清</p>
                </div>
            )}
        </div>
    );
};
