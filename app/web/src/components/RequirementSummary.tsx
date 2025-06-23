import React from 'react';
import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

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

interface RequirementSummaryProps {
    session: ClarificationSession | null;
}

export const RequirementSummary: React.FC<RequirementSummaryProps> = ({ session }) => {
    if (!session) {
        return (
            <div className="bg-white rounded-lg shadow border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">需求摘要</h2>
                <div className="text-center py-8 text-gray-500">
                    <p>开始对话后将显示需求摘要</p>
                </div>
            </div>
        );
    }

    const totalQuestions = session.questions.length;
    const answeredQuestions = Object.keys(session.answers).length;
    const completionRate = totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0;

    return (
        <div className="bg-white rounded-lg shadow border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">需求摘要</h2>

            {/* 清晰度评分 */}
            <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">清晰度评分</span>
                    <span className="text-sm text-gray-600">{Math.round(session.clarity_score)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                        className={`h-2 rounded-full ${session.clarity_score >= 80
                            ? 'bg-green-500'
                            : session.clarity_score >= 60
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                            }`}
                        style={{ width: `${session.clarity_score}%` }}
                    />
                </div>
            </div>

            {/* 问题完成状态 */}
            <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">问题完成进度</span>
                    <span className="text-sm text-gray-600">{answeredQuestions}/{totalQuestions}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                        className="h-2 bg-blue-500 rounded-full transition-all duration-300"
                        style={{ width: `${completionRate}%` }}
                    />
                </div>
            </div>

            {/* 原始需求 */}
            <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-700 mb-2">原始需求</h3>
                <div className="bg-gray-50 p-3 rounded text-sm text-gray-700">
                    {session.user_input}
                </div>
            </div>

            {/* 已回答的问题 */}
            {Object.keys(session.answers).length > 0 && (
                <div className="mb-6">
                    <h3 className="text-sm font-medium text-gray-700 mb-2">已澄清信息</h3>
                    <div className="space-y-2">
                        {Object.entries(session.answers).map(([questionId, answer]) => {
                            const question = session.questions.find(q => q.id === questionId);
                            return (
                                <div key={questionId} className="flex items-start space-x-2">
                                    <CheckCircleIcon className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                                    <div className="flex-1">
                                        <p className="text-xs text-gray-600">{question?.text}</p>
                                        <p className="text-sm text-gray-800 font-medium">{answer}</p>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* 待回答的问题 */}
            {session.questions.filter(q => !session.answers[q.id]).length > 0 && (
                <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">待澄清问题</h3>
                    <div className="space-y-2">
                        {session.questions
                            .filter(q => !session.answers[q.id])
                            .slice(0, 3)
                            .map(question => (
                                <div key={question.id} className="flex items-start space-x-2">
                                    <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                                    <p className="text-xs text-gray-600">{question.text}</p>
                                </div>
                            ))}
                    </div>
                </div>
            )}

            {/* 操作按钮 */}
            <div className="mt-6 pt-4 border-t border-gray-200">
                <button
                    disabled={completionRate < 80}
                    className="w-full py-2 px-4 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    生成需求文档
                </button>
                <p className="text-xs text-gray-500 mt-2 text-center">
                    完成80%以上问题后可生成文档
                </p>
            </div>
        </div>
    );
};
