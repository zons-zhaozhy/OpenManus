import React, { useState } from 'react';
import {
    LightBulbIcon,
    CogIcon,
    MagnifyingGlassIcon,
    ChevronDownIcon,
    ChevronRightIcon,
    CheckCircleIcon,
    ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface ThinkActReflectData {
    think_phase?: {
        problem: string;
        summary: string;
        insights: string[];
        next_actions: string[];
        confidence: number;
        reasoning_chain: string[];
        error?: string;
    };
    act_phase?: {
        analysis_result: string;
        session_summary: any;
        execution_time: number;
    };
    reflect_phase?: {
        quality_metrics: {
            overall_score: number;
            completeness: number;
            accuracy: number;
            professionalism: number;
            clarity: number;
            actionability: number;
            innovation: number;
        };
        identified_issues: string[];
        improvement_suggestions: string[];
        quality_gate_passed: boolean;
        error?: string;
    };
}

interface ThinkActReflectPanelProps {
    data: ThinkActReflectData;
    isVisible: boolean;
    onToggle: () => void;
}

export function ThinkActReflectPanel({ data, isVisible, onToggle }: ThinkActReflectPanelProps) {
    const [activePhase, setActivePhase] = useState<'think' | 'act' | 'reflect'>('think');
    const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['think']));

    const toggleSection = (section: string) => {
        const newExpanded = new Set(expandedSections);
        if (newExpanded.has(section)) {
            newExpanded.delete(section);
        } else {
            newExpanded.add(section);
        }
        setExpandedSections(newExpanded);
    };

    if (!isVisible) {
        return (
            <div className="fixed bottom-4 right-4 z-50">
                <button
                    onClick={onToggle}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 transition-colors"
                >
                    <LightBulbIcon className="w-5 h-5" />
                    查看AI思维过程
                </button>
            </div>
        );
    }

    return (
        <div className="fixed bottom-4 right-4 w-96 max-h-[80vh] bg-white rounded-lg shadow-2xl border border-gray-200 z-50 overflow-hidden">
            {/* 头部 */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <LightBulbIcon className="w-6 h-6" />
                    <h3 className="font-semibold">AI思维过程</h3>
                </div>
                <button
                    onClick={onToggle}
                    className="text-white hover:text-gray-200 transition-colors"
                >
                    <ChevronDownIcon className="w-5 h-5" />
                </button>
            </div>

            {/* 内容区域 */}
            <div className="max-h-[60vh] overflow-y-auto">
                {/* Think Phase */}
                <div className="border-b border-gray-200">
                    <button
                        onClick={() => toggleSection('think')}
                        className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                    >
                        <div className="flex items-center gap-3">
                            <LightBulbIcon className="w-5 h-5 text-yellow-500" />
                            <div className="text-left">
                                <div className="font-medium text-gray-900">Think - 深度思考</div>
                                <div className="text-sm text-gray-500">分析问题本质，制定策略</div>
                            </div>
                        </div>
                        {data.think_phase?.confidence && (
                            <div className="text-sm text-blue-600 font-medium">
                                {Math.round(data.think_phase.confidence * 100)}%
                            </div>
                        )}
                        {expandedSections.has('think') ?
                            <ChevronDownIcon className="w-4 h-4 text-gray-400" /> :
                            <ChevronRightIcon className="w-4 h-4 text-gray-400" />
                        }
                    </button>

                    {expandedSections.has('think') && (
                        <div className="px-4 pb-4 space-y-3">
                            {data.think_phase?.error ? (
                                <div className="text-red-600 text-sm">
                                    错误: {data.think_phase.error}
                                </div>
                            ) : (
                                <>
                                    {data.think_phase?.summary && (
                                        <div>
                                            <div className="text-xs font-medium text-gray-700 mb-1">思维总结</div>
                                            <div className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
                                                {data.think_phase.summary}
                                            </div>
                                        </div>
                                    )}

                                    {data.think_phase?.insights && data.think_phase.insights.length > 0 && (
                                        <div>
                                            <div className="text-xs font-medium text-gray-700 mb-1">关键洞察</div>
                                            <ul className="text-sm space-y-1">
                                                {data.think_phase.insights.slice(0, 3).map((insight, index) => (
                                                    <li key={index} className="flex items-start gap-2">
                                                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                                                        <span className="text-gray-600">{insight}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    )}
                </div>

                {/* Act Phase */}
                <div className="border-b border-gray-200">
                    <button
                        onClick={() => toggleSection('act')}
                        className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                    >
                        <div className="flex items-center gap-3">
                            <CogIcon className="w-5 h-5 text-blue-500" />
                            <div className="text-left">
                                <div className="font-medium text-gray-900">Act - 执行行动</div>
                                <div className="text-sm text-gray-500">基于思考执行具体分析</div>
                            </div>
                        </div>
                        {data.act_phase?.execution_time && (
                            <div className="text-sm text-green-600 font-medium">
                                {data.act_phase.execution_time.toFixed(1)}s
                            </div>
                        )}
                        {expandedSections.has('act') ?
                            <ChevronDownIcon className="w-4 h-4 text-gray-400" /> :
                            <ChevronRightIcon className="w-4 h-4 text-gray-400" />
                        }
                    </button>

                    {expandedSections.has('act') && (
                        <div className="px-4 pb-4 space-y-3">
                            {data.act_phase?.analysis_result && (
                                <div>
                                    <div className="text-xs font-medium text-gray-700 mb-1">执行结果</div>
                                    <div className="text-sm text-gray-600 bg-gray-50 p-2 rounded max-h-32 overflow-y-auto">
                                        {data.act_phase.analysis_result.substring(0, 200)}
                                        {data.act_phase.analysis_result.length > 200 && '...'}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Reflect Phase */}
                <div>
                    <button
                        onClick={() => toggleSection('reflect')}
                        className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                    >
                        <div className="flex items-center gap-3">
                            <MagnifyingGlassIcon className="w-5 h-5 text-purple-500" />
                            <div className="text-left">
                                <div className="font-medium text-gray-900">Reflect - 反思评估</div>
                                <div className="text-sm text-gray-500">评估质量，持续改进</div>
                            </div>
                        </div>
                        {data.reflect_phase?.quality_metrics?.overall_score && (
                            <div className="flex items-center gap-1">
                                {data.reflect_phase.quality_gate_passed ?
                                    <CheckCircleIcon className="w-4 h-4 text-green-500" /> :
                                    <ExclamationTriangleIcon className="w-4 h-4 text-orange-500" />
                                }
                                <span className="text-sm font-medium text-gray-900">
                                    {Math.round(data.reflect_phase.quality_metrics.overall_score * 100)}分
                                </span>
                            </div>
                        )}
                        {expandedSections.has('reflect') ?
                            <ChevronDownIcon className="w-4 h-4 text-gray-400" /> :
                            <ChevronRightIcon className="w-4 h-4 text-gray-400" />
                        }
                    </button>

                    {expandedSections.has('reflect') && (
                        <div className="px-4 pb-4 space-y-3">
                            {data.reflect_phase?.error ? (
                                <div className="text-red-600 text-sm">
                                    错误: {data.reflect_phase.error}
                                </div>
                            ) : (
                                <>
                                    {data.reflect_phase?.quality_metrics && (
                                        <div>
                                            <div className="text-xs font-medium text-gray-700 mb-2">质量评估</div>
                                            <div className="grid grid-cols-2 gap-2 text-xs">
                                                <div className="flex justify-between">
                                                    <span>完整性</span>
                                                    <span className="font-medium">
                                                        {Math.round(data.reflect_phase.quality_metrics.completeness * 100)}%
                                                    </span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span>准确性</span>
                                                    <span className="font-medium">
                                                        {Math.round(data.reflect_phase.quality_metrics.accuracy * 100)}%
                                                    </span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span>专业性</span>
                                                    <span className="font-medium">
                                                        {Math.round(data.reflect_phase.quality_metrics.professionalism * 100)}%
                                                    </span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span>清晰度</span>
                                                    <span className="font-medium">
                                                        {Math.round(data.reflect_phase.quality_metrics.clarity * 100)}%
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {data.reflect_phase?.improvement_suggestions &&
                                        data.reflect_phase.improvement_suggestions.length > 0 && (
                                            <div>
                                                <div className="text-xs font-medium text-gray-700 mb-1">改进建议</div>
                                                <ul className="text-xs space-y-1">
                                                    {data.reflect_phase.improvement_suggestions.slice(0, 2).map((suggestion, index) => (
                                                        <li key={index} className="flex items-start gap-2">
                                                            <div className="w-1.5 h-1.5 bg-purple-500 rounded-full mt-1.5 flex-shrink-0" />
                                                            <span className="text-gray-600">{suggestion}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                </>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
