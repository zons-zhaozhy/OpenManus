import React from 'react';
import {
    UserGroupIcon,
    CpuChipIcon,
    ClockIcon,
    CheckCircleIcon,
    ExclamationTriangleIcon,
    BeakerIcon
} from '@heroicons/react/24/outline';
import { useRequirementsContext } from '../RequirementsPageContext';

export function AgentTeamPanel() {
    const { agents, currentWorkflowStage, workflowProgress } = useRequirementsContext();

    // 定义任务流程和依赖关系
    const workflowSteps = [
        {
            id: 'business_analyst',
            name: '业务分析师',
            task: '需求理解',
            icon: '📊',
            description: '理解用户需求，提取关键信息',
            dependencies: [],
            position: { x: 280, y: 40 }
        },
        {
            id: 'requirement_clarifier',
            name: '需求澄清专家',
            task: '需求澄清',
            icon: '🔍',
            description: '识别模糊点，生成澄清问题',
            dependencies: ['business_analyst'],
            position: { x: 280, y: 160 }
        },
        {
            id: 'technical_writer',
            name: '技术文档编写师',
            task: '文档生成',
            icon: '📝',
            description: '生成需求规格说明书',
            dependencies: ['business_analyst', 'requirement_clarifier'],
            position: { x: 280, y: 280 }
        },
        {
            id: 'quality_reviewer',
            name: '质量评审员',
            task: '质量评审',
            icon: '✅',
            description: '评审需求分析质量和完整性',
            dependencies: ['business_analyst', 'requirement_clarifier', 'technical_writer'],
            position: { x: 280, y: 400 }
        }
    ];

    // 获取智能体状态
    const getAgentStatus = (stepId: string) => {
        const agent = agents.find(a => a.id === stepId);
        return agent?.status || 'waiting';
    };

    // 获取状态对应的颜色和图标
    const getStatusConfig = (status: string) => {
        switch (status) {
            case 'waiting':
                return { color: '#6B7280', bgColor: '#374151', icon: '⏳', label: '等待中' };
            case '准备中':
                return { color: '#3B82F6', bgColor: '#1E3A8A', icon: '🔵', label: '准备中' };
            case '执行中':
                return { color: '#F59E0B', bgColor: '#92400E', icon: '🟡', label: '执行中', pulse: true };
            case '已完成':
                return { color: '#10B981', bgColor: '#065F46', icon: '🟢', label: '已完成' };
            case '中断':
                return { color: '#EF4444', bgColor: '#7F1D1D', icon: '🔴', label: '中断' };
            case '连接中断':
                return { color: '#8B5CF6', bgColor: '#5B21B6', icon: '⚡', label: '连接中断' };
            default:
                return { color: '#6B7280', bgColor: '#374151', icon: '⏳', label: status };
        }
    };

    // 获取连接线颜色
    const getConnectionColor = (fromStatus: string, toStatus: string) => {
        const fromConfig = getStatusConfig(fromStatus);
        if (fromStatus === '已完成') {
            return fromConfig.color;
        }
        return '#374151'; // 灰色
    };

    return (
        <div className="p-4 overflow-y-auto h-full">
            {/* 三大阵营协作状态 */}
            <div className="mb-6 p-3 bg-gradient-to-r from-gray-700/30 to-gray-600/30 rounded-lg border border-gray-600">
                <div className="text-sm font-medium text-gray-300 mb-3 text-center">🤝 三方协作体系</div>
                <div className="flex space-x-2">
                    {/* 用户方 */}
                    <div className="flex-1 flex items-center space-x-2 p-2 bg-blue-500/10 border border-blue-500/20 rounded">
                        <span className="text-blue-400">👤</span>
                        <div className="flex-1">
                            <span className="text-blue-300 text-xs font-medium">用户方</span>
                            <div className="text-blue-200 text-xs">需求提供 • 澄清确认</div>
                        </div>
                        <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                    </div>

                    {/* OpenManus系统方 */}
                    <div className="flex-1 flex items-center space-x-2 p-2 bg-green-500/10 border border-green-500/20 rounded">
                        <span className="text-green-400">🤖</span>
                        <div className="flex-1">
                            <span className="text-green-300 text-xs font-medium">OpenManus系统</span>
                            <div className="text-green-200 text-xs">智能体协作 • 流程管理</div>
                        </div>
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    </div>

                    {/* LLM引擎方 */}
                    <div className="flex-1 flex items-center space-x-2 p-2 bg-amber-500/10 border border-amber-500/20 rounded">
                        <span className="text-amber-400">🧠</span>
                        <div className="flex-1">
                            <span className="text-amber-300 text-xs font-medium">LLM引擎</span>
                            <div className="text-amber-200 text-xs">AI推理 • 内容生成</div>
                        </div>
                        <div className="w-2 h-2 bg-amber-400 rounded-full animate-pulse"></div>
                    </div>
                </div>
            </div>

            {/* 当前工作流阶段 */}
            {currentWorkflowStage && (
                <div className="mb-6 p-3 bg-gray-700/50 rounded-lg border-l-4 border-blue-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="flex items-center space-x-2">
                                <ClockIcon className="h-4 w-4 text-blue-400" />
                                <span className="text-sm font-medium text-gray-300">当前阶段</span>
                            </div>
                            <p className="text-white font-medium mt-1">{currentWorkflowStage}</p>
                        </div>
                        {workflowProgress > 0 && (
                            <div className="text-right">
                                <div className="text-sm text-gray-300">{Math.round(workflowProgress * 100)}%</div>
                                <div className="w-16 bg-gray-600 rounded-full h-1.5 mt-1">
                                    <div
                                        className="bg-blue-500 h-1.5 rounded-full transition-all duration-500"
                                        style={{ width: `${workflowProgress * 100}%` }}
                                    />
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* 流程图展示 */}
            <div className="mb-4">
                <div className="flex items-center space-x-2 mb-3">
                    <span className="text-green-400">🔄</span>
                    <span className="text-sm font-medium text-gray-300">需求分析流程图</span>
                </div>

                {/* SVG流程图容器 */}
                <div className="bg-gray-800/30 rounded-lg p-4 border border-gray-600 overflow-hidden">
                    <svg width="100%" height="500" viewBox="0 0 800 500" className="overflow-visible" preserveAspectRatio="xMidYMid meet">
                        {/* 绘制连接线 */}
                        {workflowSteps.map((step, index) => (
                            step.dependencies.map(depId => {
                                const depStep = workflowSteps.find(s => s.id === depId);
                                if (!depStep) return null;

                                const fromStatus = getAgentStatus(depId);
                                const toStatus = getAgentStatus(step.id);
                                const lineColor = getConnectionColor(fromStatus, toStatus);

                                return (
                                    <line
                                        key={`${depId}-${step.id}`}
                                        x1={depStep.position.x + 120}
                                        y1={depStep.position.y + 40}
                                        x2={step.position.x + 120}
                                        y2={step.position.y}
                                        stroke={lineColor}
                                        strokeWidth="3"
                                        strokeDasharray={fromStatus === '已完成' ? '0' : '5,5'}
                                        markerEnd="url(#arrowhead)"
                                    />
                                );
                            })
                        ))}

                        {/* 箭头标记定义 */}
                        <defs>
                            <marker
                                id="arrowhead"
                                markerWidth="10"
                                markerHeight="7"
                                refX="9"
                                refY="3.5"
                                orient="auto"
                            >
                                <polygon
                                    points="0 0, 10 3.5, 0 7"
                                    fill="currentColor"
                                    className="text-gray-400"
                                />
                            </marker>
                        </defs>

                        {/* 绘制节点 */}
                        {workflowSteps.map((step, index) => {
                            const status = getAgentStatus(step.id);
                            const isActive = currentWorkflowStage === step.id;
                            const statusColor = getStatusConfig(status).color;

                            return (
                                <g key={step.id} transform={`translate(${step.position.x}, ${step.position.y})`}>
                                    {/* 节点背景 */}
                                    <rect
                                        x="0"
                                        y="0"
                                        width="240"
                                        height="80"
                                        rx="8"
                                        className={`${isActive ? 'fill-gray-700' : 'fill-gray-800'} stroke-gray-600`}
                                        strokeWidth="2"
                                    />

                                    {/* 节点内容 */}
                                    <text x="20" y="30" className="text-base font-medium fill-gray-200">
                                        {step.icon} {step.name}
                                    </text>
                                    <text x="20" y="55" className="text-sm fill-gray-400">
                                        {step.task}
                                    </text>

                                    {/* 状态指示器 */}
                                    <circle
                                        cx="220"
                                        cy="20"
                                        r="6"
                                        className={`${statusColor} transition-all duration-300`}
                                    />
                                </g>
                            );
                        })}
                    </svg>
                </div>

                {/* 状态说明 */}
                <div className="mt-4 grid grid-cols-2 gap-4">
                    <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 rounded-full bg-gray-500"></div>
                        <span className="text-sm text-gray-400">等待中</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 rounded-full bg-yellow-500 animate-pulse"></div>
                        <span className="text-sm text-gray-400">进行中</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 rounded-full bg-green-500"></div>
                        <span className="text-sm text-gray-400">已完成</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 rounded-full bg-red-500"></div>
                        <span className="text-sm text-gray-400">出错</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
