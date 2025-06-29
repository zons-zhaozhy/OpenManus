import React from 'react';
import {
    ChevronUpIcon,
    ChevronDownIcon,
    CogIcon,
    ClockIcon
} from '@heroicons/react/24/outline';
import { useRequirementsContext } from '../RequirementsPageContext';

interface WorkflowPanelProps {
    isCollapsed: boolean;
    onToggleCollapse: () => void;
}

export function WorkflowPanel({ isCollapsed, onToggleCollapse }: WorkflowPanelProps) {
    const {
        workflowSummary,
        currentWorkflowStage,
        workflowProgress,
        workflowInsights,
        analysisMode,
        setAnalysisMode
    } = useRequirementsContext();

    return (
        <div className={`bg-gray-800 border-b border-gray-700 transition-all duration-300 ${isCollapsed ? 'h-16' : 'h-96'
            }`}>
            {/* 工作流头部 - 始终可见 */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
                <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                        <CogIcon className="h-5 w-5 text-white" />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-white">AI需求分析工作流</h2>
                        <p className="text-sm text-gray-400">
                            {isCollapsed
                                ? currentWorkflowStage || '智能需求分析与多智能体协作'
                                : '智能需求分析与多智能体协作'
                            }
                        </p>
                    </div>
                </div>

                <div className="flex items-center space-x-4">
                    {/* 进度指示器 - 折叠时显示 */}
                    {isCollapsed && workflowProgress > 0 && (
                        <div className="flex items-center space-x-2">
                            <div className="w-20 bg-gray-700 rounded-full h-2">
                                <div
                                    className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                                    style={{ width: `${workflowProgress * 100}%` }}
                                />
                            </div>
                            <span className="text-xs text-gray-400">
                                {Math.round(workflowProgress * 100)}%
                            </span>
                        </div>
                    )}

                    {/* 折叠/展开按钮 */}
                    <button
                        onClick={onToggleCollapse}
                        className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                        title={isCollapsed ? "展开工作流" : "折叠工作流"}
                    >
                        {isCollapsed ? (
                            <ChevronDownIcon className="h-5 w-5 text-gray-400" />
                        ) : (
                            <ChevronUpIcon className="h-5 w-5 text-gray-400" />
                        )}
                    </button>
                </div>
            </div>

            {/* 工作流内容 - 可折叠 */}
            {!isCollapsed && (
                <div className="flex-1 overflow-hidden">
                    {/* 分析模式切换 */}
                    <div className="p-4 border-b border-gray-700">
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-gray-300">分析模式</span>
                            <div className="flex space-x-2">
                                <button
                                    onClick={() => setAnalysisMode('workflow')}
                                    className={`px-3 py-1 rounded-md text-xs transition-all ${analysisMode === 'workflow'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                        }`}
                                >
                                    🔄 工作流程模式
                                </button>
                                <button
                                    onClick={() => setAnalysisMode('quick')}
                                    className={`px-3 py-1 rounded-md text-xs transition-all ${analysisMode === 'quick'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                        }`}
                                >
                                    ⚡ 快速分析模式
                                </button>
                            </div>
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                            {analysisMode === 'workflow'
                                ? '完整的任务跟踪和生命周期管理'
                                : '传统的快速流式分析'
                            }
                        </div>
                    </div>

                    {/* 工作流状态展示 */}
                    <div className="p-4 h-64 overflow-y-auto">
                        {currentWorkflowStage || workflowProgress > 0 ? (
                            <div className="space-y-4">
                                {/* 当前阶段 */}
                                <div className="bg-gray-700 rounded-lg p-3">
                                    <div className="flex items-center space-x-2 mb-2">
                                        <ClockIcon className="h-4 w-4 text-blue-400" />
                                        <span className="text-sm font-medium text-gray-200">
                                            当前阶段
                                        </span>
                                    </div>
                                    <div className="text-sm text-gray-300">
                                        {currentWorkflowStage || '初始化中...'}
                                    </div>
                                </div>

                                {/* 进度条 */}
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-gray-400">整体进度</span>
                                        <span className="text-gray-300">
                                            {Math.round(workflowProgress * 100)}%
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-700 rounded-full h-3">
                                        <div
                                            className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
                                            style={{ width: `${workflowProgress * 100}%` }}
                                        />
                                    </div>
                                </div>

                                {/* 工作流洞察 */}
                                {workflowInsights.length > 0 && (
                                    <div className="space-y-2">
                                        <h4 className="text-sm font-medium text-gray-300">最新洞察</h4>
                                        <div className="space-y-1">
                                            {workflowInsights.slice(-3).map((insight, index) => (
                                                <div key={index} className="text-xs text-gray-400 bg-gray-750 rounded p-2">
                                                    {insight}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* 工作流汇总 */}
                                {workflowSummary && (
                                    <div className="bg-gray-700 rounded-lg p-3">
                                        <h4 className="text-sm font-medium text-gray-200 mb-2">工作流汇总</h4>
                                        <div className="grid grid-cols-2 gap-2 text-xs">
                                            <div>
                                                <span className="text-gray-400">总任务:</span>
                                                <span className="text-gray-200 ml-1">
                                                    {workflowSummary.total_tasks || 0}
                                                </span>
                                            </div>
                                            <div>
                                                <span className="text-gray-400">已完成:</span>
                                                <span className="text-gray-200 ml-1">
                                                    {workflowSummary.completed_tasks || 0}
                                                </span>
                                            </div>
                                            <div>
                                                <span className="text-gray-400">完成率:</span>
                                                <span className="text-gray-200 ml-1">
                                                    {Math.round((workflowSummary.completion_rate || 0) * 100)}%
                                                </span>
                                            </div>
                                            <div>
                                                <span className="text-gray-400">参与者:</span>
                                                <span className="text-gray-200 ml-1">
                                                    {workflowSummary.participants?.length || 0}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="text-center text-gray-400 py-8">
                                <div className="text-4xl mb-4">🔄</div>
                                <div className="text-sm">
                                    {analysisMode === 'workflow'
                                        ? '请启动工作流程分析以查看实时进度'
                                        : '请切换到工作流程模式以查看详细进度'
                                    }
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
