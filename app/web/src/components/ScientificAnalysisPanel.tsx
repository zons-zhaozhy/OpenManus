import React, { useState, useEffect } from 'react';
import {
    ChartBarIcon,
    BeakerIcon,
    CpuChipIcon,
    AcademicCapIcon,
    SparklesIcon,
    ClockIcon,
    CheckCircleIcon,
    ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface AnalysisMetrics {
    qualityScore: number;
    goalOrientedScore: number;
    confidenceLevel: number;
    processingTime: number;
    dimensionScores: Record<string, number>;
    learningInsights?: LearningInsight[];
}

interface LearningInsight {
    type: string;
    description: string;
    confidence: number;
    recommendation: string;
    impact: number;
}

interface ScientificAnalysisPanelProps {
    metrics: AnalysisMetrics;
    isAnalyzing: boolean;
    showDetailedMetrics?: boolean;
}

export const ScientificAnalysisPanel: React.FC<ScientificAnalysisPanelProps> = ({
    metrics,
    isAnalyzing,
    showDetailedMetrics = true
}) => {
    const [activeTab, setActiveTab] = useState<'overview' | 'dimensions' | 'learning'>('overview');
    const [animatedScores, setAnimatedScores] = useState<Record<string, number>>({});

    // 动画效果：分数逐渐增长
    useEffect(() => {
        if (!isAnalyzing && metrics) {
            const animationDuration = 1500;
            const steps = 60;
            const interval = animationDuration / steps;

            let currentStep = 0;
            const timer = setInterval(() => {
                currentStep++;
                const progress = currentStep / steps;

                setAnimatedScores({
                    quality: metrics.qualityScore * progress,
                    goalOriented: metrics.goalOrientedScore * progress,
                    confidence: metrics.confidenceLevel * progress
                });

                if (currentStep >= steps) {
                    clearInterval(timer);
                }
            }, interval);

            return () => clearInterval(timer);
        }
    }, [isAnalyzing, metrics]);

    const getScoreColor = (score: number) => {
        if (score >= 0.8) return 'text-green-500';
        if (score >= 0.6) return 'text-yellow-500';
        return 'text-red-500';
    };

    const getScoreBackground = (score: number) => {
        if (score >= 0.8) return 'bg-green-500';
        if (score >= 0.6) return 'bg-yellow-500';
        return 'bg-red-500';
    };

    const formatPercentage = (score: number) => Math.round(score * 100);

    const dimensionLabels = {
        functional_requirements: '功能需求',
        non_functional_requirements: '非功能需求',
        user_roles: '用户角色',
        business_rules: '业务规则',
        constraints: '约束条件',
        acceptance_criteria: '验收标准',
        integration_requirements: '集成需求',
        data_requirements: '数据需求'
    };

    return (
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
            {/* 头部 */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 text-white">
                <div className="flex items-center space-x-3">
                    <BeakerIcon className="h-8 w-8" />
                    <div>
                        <h3 className="text-xl font-bold">AI科学分析引擎</h3>
                        <p className="text-blue-100 text-sm">基于软件工程最佳实践的智能分析</p>
                    </div>
                </div>

                {isAnalyzing && (
                    <div className="mt-4 flex items-center space-x-2">
                        <SparklesIcon className="h-5 w-5 animate-spin" />
                        <span className="text-sm">AI正在进行多维度深度分析...</span>
                    </div>
                )}
            </div>

            {/* 标签页导航 */}
            <div className="border-b border-gray-200">
                <nav className="flex space-x-8 px-6">
                    {[
                        { id: 'overview', label: '总览', icon: ChartBarIcon },
                        { id: 'dimensions', label: '8维度分析', icon: CpuChipIcon },
                        { id: 'learning', label: 'AI学习洞察', icon: AcademicCapIcon }
                    ].map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={`flex items-center space-x-2 py-4 border-b-2 transition-colors ${activeTab === tab.id
                                    ? 'border-blue-500 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            <tab.icon className="h-4 w-4" />
                            <span className="font-medium">{tab.label}</span>
                        </button>
                    ))}
                </nav>
            </div>

            {/* 内容区域 */}
            <div className="p-6">
                {activeTab === 'overview' && (
                    <div className="space-y-6">
                        {/* 核心指标 */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {/* 质量评分 */}
                            <div className="bg-gray-50 rounded-lg p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium text-gray-600">质量评分</span>
                                    <span className={`text-2xl font-bold ${getScoreColor(animatedScores.quality || 0)}`}>
                                        {formatPercentage(animatedScores.quality || 0)}%
                                    </span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div
                                        className={`h-2 rounded-full transition-all duration-1000 ${getScoreBackground(animatedScores.quality || 0)}`}
                                        style={{ width: `${formatPercentage(animatedScores.quality || 0)}%` }}
                                    />
                                </div>
                                <p className="text-xs text-gray-500 mt-1">8维度综合质量评估</p>
                            </div>

                            {/* 目标导向评分 */}
                            <div className="bg-gray-50 rounded-lg p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium text-gray-600">目标导向</span>
                                    <span className={`text-2xl font-bold ${getScoreColor(animatedScores.goalOriented || 0)}`}>
                                        {formatPercentage(animatedScores.goalOriented || 0)}%
                                    </span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div
                                        className={`h-2 rounded-full transition-all duration-1000 ${getScoreBackground(animatedScores.goalOriented || 0)}`}
                                        style={{ width: `${formatPercentage(animatedScores.goalOriented || 0)}%` }}
                                    />
                                </div>
                                <p className="text-xs text-gray-500 mt-1">目标达成有效性评估</p>
                            </div>

                            {/* AI置信度 */}
                            <div className="bg-gray-50 rounded-lg p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium text-gray-600">AI置信度</span>
                                    <span className={`text-2xl font-bold ${getScoreColor(animatedScores.confidence || 0)}`}>
                                        {formatPercentage(animatedScores.confidence || 0)}%
                                    </span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div
                                        className={`h-2 rounded-full transition-all duration-1000 ${getScoreBackground(animatedScores.confidence || 0)}`}
                                        style={{ width: `${formatPercentage(animatedScores.confidence || 0)}%` }}
                                    />
                                </div>
                                <p className="text-xs text-gray-500 mt-1">AI分析结果可信度</p>
                            </div>
                        </div>

                        {/* 处理时间和状态 */}
                        <div className="bg-blue-50 rounded-lg p-4">
                            <div className="flex items-center space-x-4">
                                <ClockIcon className="h-6 w-6 text-blue-500" />
                                <div>
                                    <p className="font-medium text-blue-900">处理性能</p>
                                    <p className="text-sm text-blue-700">
                                        分析耗时: {metrics.processingTime?.toFixed(1) || 0}秒 |
                                        多智能体协作: 4个专业智能体 |
                                        分析方法: 质量导向澄清引擎
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* 科学性说明 */}
                        <div className="border border-gray-200 rounded-lg p-4">
                            <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                                <AcademicCapIcon className="h-5 w-5 mr-2" />
                                科学分析方法论
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                <div className="space-y-2">
                                    <div className="flex items-start space-x-2">
                                        <CheckCircleIcon className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                                        <span><strong>8维度质量评估:</strong> 基于软件工程需求分析最佳实践</span>
                                    </div>
                                    <div className="flex items-start space-x-2">
                                        <CheckCircleIcon className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                                        <span><strong>目标导向设计:</strong> 围绕需求规格说明书最终目标</span>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <div className="flex items-start space-x-2">
                                        <CheckCircleIcon className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                                        <span><strong>动态澄清策略:</strong> 基于质量缺陷动态生成问题</span>
                                    </div>
                                    <div className="flex items-start space-x-2">
                                        <CheckCircleIcon className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                                        <span><strong>自适应学习:</strong> 持续从历史案例中学习优化</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'dimensions' && (
                    <div className="space-y-4">
                        <h4 className="font-semibold text-gray-900">8维度质量分析详情</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {Object.entries(metrics.dimensionScores || {}).map(([key, score]) => (
                                <div key={key} className="bg-gray-50 rounded-lg p-4">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-medium text-gray-700">
                                            {dimensionLabels[key as keyof typeof dimensionLabels] || key}
                                        </span>
                                        <span className={`text-lg font-bold ${getScoreColor(score)}`}>
                                            {formatPercentage(score)}%
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className={`h-2 rounded-full transition-all duration-1000 ${getScoreBackground(score)}`}
                                            style={{ width: `${formatPercentage(score)}%` }}
                                        />
                                    </div>
                                    <div className="mt-2 flex items-center text-xs">
                                        {score >= 0.8 ? (
                                            <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" />
                                        ) : (
                                            <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500 mr-1" />
                                        )}
                                        <span className="text-gray-600">
                                            {score >= 0.8 ? '优秀' : score >= 0.6 ? '良好' : '需改进'}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="bg-blue-50 rounded-lg p-4 mt-6">
                            <h5 className="font-medium text-blue-900 mb-2">维度评估说明</h5>
                            <p className="text-sm text-blue-700">
                                8维度评估体系基于国际软件工程标准(IEEE 830)和需求工程最佳实践，
                                确保需求分析的完整性、一致性和可追溯性。每个维度都有具体的质量指标和评估标准。
                            </p>
                        </div>
                    </div>
                )}

                {activeTab === 'learning' && (
                    <div className="space-y-4">
                        <h4 className="font-semibold text-gray-900">AI自我学习洞察</h4>

                        {metrics.learningInsights && metrics.learningInsights.length > 0 ? (
                            <div className="space-y-3">
                                {metrics.learningInsights.map((insight, index) => (
                                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                                        <div className="flex items-start justify-between mb-2">
                                            <span className="text-sm font-medium text-gray-700 capitalize">
                                                {insight.type.replace('_', ' ')}
                                            </span>
                                            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                                置信度: {formatPercentage(insight.confidence)}%
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-600 mb-2">{insight.description}</p>
                                        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3">
                                            <p className="text-sm text-yellow-800">
                                                <strong>建议:</strong> {insight.recommendation}
                                            </p>
                                        </div>
                                        <div className="mt-2 flex items-center text-xs text-gray-500">
                                            <span>影响度: {formatPercentage(insight.impact)}%</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="bg-gray-50 rounded-lg p-8 text-center">
                                <AcademicCapIcon className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                                <p className="text-gray-600">AI正在积累学习数据...</p>
                                <p className="text-sm text-gray-500 mt-1">
                                    当分析案例达到一定数量后，系统将自动生成学习洞察
                                </p>
                            </div>
                        )}

                        <div className="bg-green-50 rounded-lg p-4">
                            <h5 className="font-medium text-green-900 mb-2">自我学习机制</h5>
                            <p className="text-sm text-green-700">
                                系统会自动分析历史案例，识别成功模式，学习质量影响因子，
                                优化问题策略，并持续改进分析方法。这确保了AI助手能够不断进化，
                                为用户提供越来越精准的需求分析服务。
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
