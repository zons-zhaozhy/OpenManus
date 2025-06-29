import React, { useState, useEffect } from 'react';
import {
    CheckCircleIcon,
    ClockIcon,
    UserIcon,
    DocumentTextIcon,
    AcademicCapIcon,
    CogIcon
} from '@heroicons/react/24/outline';

interface WorkflowStep {
    id: string;
    title: string;
    description: string;
    icon: React.ComponentType<any>;
    status: 'pending' | 'active' | 'completed' | 'error';
    estimatedTime: string;
    details?: string;
}

interface AnalysisWorkflowVisualizerProps {
    currentStage: string;
    progress: number;
    insights?: string[];
}

export const AnalysisWorkflowVisualizer: React.FC<AnalysisWorkflowVisualizerProps> = ({
    currentStage,
    progress,
    insights = []
}) => {
    const [steps, setSteps] = useState<WorkflowStep[]>([
        {
            id: 'understanding',
            title: '需求理解',
            description: '分析和理解用户需求的核心意图',
            icon: UserIcon,
            status: 'pending',
            estimatedTime: '30秒',
            details: ''
        },
        {
            id: 'analysis',
            title: '业务分析',
            description: '识别业务场景、用户角色和功能模块',
            icon: CogIcon,
            status: 'pending',
            estimatedTime: '45秒',
            details: ''
        },
        {
            id: 'classification',
            title: '需求分类',
            description: '按优先级和复杂度对需求进行分类',
            icon: AcademicCapIcon,
            status: 'pending',
            estimatedTime: '30秒',
            details: ''
        },
        {
            id: 'documentation',
            title: '文档生成',
            description: '生成专业的需求规格说明书',
            icon: DocumentTextIcon,
            status: 'pending',
            estimatedTime: '60秒',
            details: ''
        }
    ]);

    const [currentInsight, setCurrentInsight] = useState<string>('');
    const [showProgressDetails, setShowProgressDetails] = useState(false);

    // 根据当前阶段更新步骤状态
    useEffect(() => {
        setSteps(prev => prev.map(step => {
            const stageMapping: Record<string, string[]> = {
                'understanding': ['understanding', 'clarifier', 'semantic_analysis'],
                'analysis': ['analysis', 'analyst', 'classification'],
                'classification': ['classification', 'writer'],
                'documentation': ['documentation', 'generating_result', 'final_review']
            };

            let newStatus = step.status;

            // 检查当前步骤是否应该激活
            if (stageMapping[step.id]?.includes(currentStage)) {
                newStatus = 'active';
            } else {
                // 检查是否已完成
                const stepIndex = Object.keys(stageMapping).indexOf(step.id);
                const currentStageIndex = Object.keys(stageMapping).findIndex(key =>
                    stageMapping[key].includes(currentStage)
                );

                if (stepIndex < currentStageIndex) {
                    newStatus = 'completed';
                } else if (stepIndex > currentStageIndex) {
                    newStatus = 'pending';
                }
            }

            return { ...step, status: newStatus };
        }));
    }, [currentStage]);

    // 更新当前洞察
    useEffect(() => {
        if (insights.length > 0) {
            setCurrentInsight(insights[insights.length - 1]);
        }
    }, [insights]);

    const getStepStatusColor = (status: string) => {
        switch (status) {
            case 'completed': return 'text-green-600 border-green-600 bg-green-50';
            case 'active': return 'text-blue-600 border-blue-600 bg-blue-50';
            case 'error': return 'text-red-600 border-red-600 bg-red-50';
            default: return 'text-gray-400 border-gray-300 bg-gray-50';
        }
    };

    const getStepIconColor = (status: string) => {
        switch (status) {
            case 'completed': return 'text-green-600';
            case 'active': return 'text-blue-600';
            case 'error': return 'text-red-600';
            default: return 'text-gray-400';
        }
    };

    return (
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            {/* 头部 */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="text-xl font-bold text-gray-900">AI需求分析工作流</h3>
                    <p className="text-sm text-gray-600 mt-1">智能体团队正在为您分析需求</p>
                </div>
                <div className="flex items-center space-x-2">
                    <button
                        onClick={() => setShowProgressDetails(!showProgressDetails)}
                        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                    >
                        {showProgressDetails ? '隐藏详情' : '显示详情'}
                    </button>
                </div>
            </div>

            {/* 整体进度条 */}
            <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">总体进度</span>
                    <span className="text-sm font-medium text-gray-700">{Math.round(progress * 100)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                        className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all duration-1000"
                        style={{ width: `${progress * 100}%` }}
                    />
                </div>
            </div>

            {/* 工作流程步骤 */}
            <div className="space-y-4 relative">
                {steps.map((step, index) => {
                    const Icon = step.icon;
                    return (
                        <div key={step.id} className="flex items-start space-x-4 relative">
                            {/* 步骤图标 */}
                            <div className={`
                                flex-shrink-0 w-12 h-12 rounded-full border-2 flex items-center justify-center
                                ${getStepStatusColor(step.status)}
                                transition-all duration-300 relative z-10
                            `}>
                                {step.status === 'completed' ? (
                                    <CheckCircleIcon className="h-6 w-6 text-green-600" />
                                ) : step.status === 'active' ? (
                                    <Icon className={`h-6 w-6 ${getStepIconColor(step.status)} animate-pulse`} />
                                ) : (
                                    <Icon className={`h-6 w-6 ${getStepIconColor(step.status)}`} />
                                )}
                            </div>

                            {/* 连接线 */}
                            {index < steps.length - 1 && (
                                <div className="absolute left-6 top-12 w-0.5 h-8 bg-gray-300" />
                            )}

                            {/* 步骤内容 */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between">
                                    <h4 className={`
                                        text-lg font-semibold
                                        ${step.status === 'active' ? 'text-blue-600' :
                                            step.status === 'completed' ? 'text-green-600' : 'text-gray-500'}
                                    `}>
                                        {step.title}
                                    </h4>
                                    <div className="flex items-center space-x-2">
                                        <ClockIcon className="h-4 w-4 text-gray-400" />
                                        <span className="text-sm text-gray-500">{step.estimatedTime}</span>
                                    </div>
                                </div>
                                <p className="text-sm text-gray-600 mt-1">{step.description}</p>

                                {/* 当前步骤的详细信息 */}
                                {step.status === 'active' && currentInsight && (
                                    <div className="mt-2 p-3 bg-blue-50 rounded-lg border-l-4 border-blue-400">
                                        <p className="text-sm text-blue-800">💡 {currentInsight}</p>
                                    </div>
                                )}

                                {step.status === 'completed' && step.details && (
                                    <div className="mt-2 p-3 bg-green-50 rounded-lg border-l-4 border-green-400">
                                        <p className="text-sm text-green-800">✅ {step.details}</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* 详细进度信息 */}
            {showProgressDetails && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-900 mb-3">分析详情</h4>
                    <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                            <span className="text-gray-600">当前阶段:</span>
                            <span className="font-medium">{currentStage}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-gray-600">预计完成时间:</span>
                            <span className="font-medium">2-3分钟</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-gray-600">分析方法:</span>
                            <span className="font-medium">AI智能分析</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
