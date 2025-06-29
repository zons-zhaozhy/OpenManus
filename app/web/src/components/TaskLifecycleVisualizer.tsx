import React, { useState, useEffect, useRef } from 'react';
import {
    Clock,
    User,
    CheckCircle,
    XCircle,
    PlayCircle,
    PauseCircle,
    Users,
    FileText,
    AlertCircle,
    TrendingUp,
    Calendar,
    Target
} from 'lucide-react';

// 任务状态枚举
export enum TaskStatus {
    PENDING = 'pending',
    RUNNING = 'running',
    PAUSED = 'paused',
    COMPLETED = 'completed',
    FAILED = 'failed',
    CANCELLED = 'cancelled'
}

// 参与者角色枚举
export enum ParticipantRole {
    OWNER = 'owner',
    EXECUTOR = 'executor',
    REVIEWER = 'reviewer',
    STAKEHOLDER = 'stakeholder'
}

// 数据接口定义
interface Participant {
    id: string;
    name: string;
    role: ParticipantRole;
    agent_type: string;
    capabilities: string[];
}

interface TaskResult {
    content: any;
    quality_score: number;
    confidence: number;
    metadata: Record<string, any>;
    artifacts: string[];
}

interface Task {
    id: string;
    name: string;
    description: string;
    parent_id?: string;
    participants: Participant[];
    created_at: string;
    started_at?: string;
    estimated_duration?: string;
    actual_duration?: string;
    completed_at?: string;
    status: TaskStatus;
    progress: number;
    dependencies: string[];
    result?: TaskResult;
    error_message?: string;
    subtasks: string[];
    children?: Task[];
}

interface WorkflowSummary {
    root_task: Task;
    total_tasks: number;
    completed_tasks: number;
    failed_tasks: number;
    completion_rate: number;
    overall_progress: number;
    estimated_remaining?: string;
    participants: string[];
}

interface TaskLifecycleVisualizerProps {
    workflowSummary?: WorkflowSummary;
    taskTree?: Task;
    onTaskSelect?: (task: Task) => void;
    className?: string;
}

// 任务状态图标映射
const getStatusIcon = (status: TaskStatus) => {
    switch (status) {
        case TaskStatus.PENDING:
            return <Clock className="w-4 h-4 text-gray-400" />;
        case TaskStatus.RUNNING:
            return <PlayCircle className="w-4 h-4 text-blue-500 animate-pulse" />;
        case TaskStatus.PAUSED:
            return <PauseCircle className="w-4 h-4 text-yellow-500" />;
        case TaskStatus.COMPLETED:
            return <CheckCircle className="w-4 h-4 text-green-500" />;
        case TaskStatus.FAILED:
            return <XCircle className="w-4 h-4 text-red-500" />;
        case TaskStatus.CANCELLED:
            return <XCircle className="w-4 h-4 text-gray-500" />;
        default:
            return <Clock className="w-4 h-4 text-gray-400" />;
    }
};

// 任务状态颜色映射
const getStatusColor = (status: TaskStatus) => {
    switch (status) {
        case TaskStatus.PENDING:
            return 'bg-gray-100 border-gray-300';
        case TaskStatus.RUNNING:
            return 'bg-blue-50 border-blue-300 ring-2 ring-blue-200';
        case TaskStatus.PAUSED:
            return 'bg-yellow-50 border-yellow-300';
        case TaskStatus.COMPLETED:
            return 'bg-green-50 border-green-300';
        case TaskStatus.FAILED:
            return 'bg-red-50 border-red-300';
        case TaskStatus.CANCELLED:
            return 'bg-gray-50 border-gray-300';
        default:
            return 'bg-gray-100 border-gray-300';
    }
};

// 参与者角色图标映射
const getRoleIcon = (role: ParticipantRole) => {
    switch (role) {
        case ParticipantRole.OWNER:
            return <Target className="w-3 h-3" />;
        case ParticipantRole.EXECUTOR:
            return <User className="w-3 h-3" />;
        case ParticipantRole.REVIEWER:
            return <CheckCircle className="w-3 h-3" />;
        case ParticipantRole.STAKEHOLDER:
            return <Users className="w-3 h-3" />;
        default:
            return <User className="w-3 h-3" />;
    }
};

// 任务卡片组件
const TaskCard: React.FC<{
    task: Task;
    onSelect?: (task: Task) => void;
    isRoot?: boolean;
}> = ({ task, onSelect, isRoot = false }) => {
    const statusColor = getStatusColor(task.status);
    const statusIcon = getStatusIcon(task.status);

    const formatDuration = (duration?: string) => {
        if (!duration) return '-';
        if (duration.includes(':')) {
            const parts = duration.split(':');
            if (parts.length >= 2) {
                const hours = parseInt(parts[0]);
                const minutes = parseInt(parts[1]);
                if (hours > 0) {
                    return `${hours}h ${minutes}m`;
                } else {
                    return `${minutes}m`;
                }
            }
        }
        return duration;
    };

    return (
        <div
            className={`
        p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 hover:shadow-md
        ${statusColor}
        ${isRoot ? 'mb-6' : 'mb-3'}
      `}
            onClick={() => onSelect?.(task)}
        >
            <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                    {statusIcon}
                    <h3 className={`font-medium ${isRoot ? 'text-lg' : 'text-sm'}`}>
                        {task.name}
                    </h3>
                </div>
                <div className="text-right text-xs text-gray-500">
                    {task.status === TaskStatus.RUNNING && (
                        <div className="text-blue-600 font-medium">
                            {Math.round(task.progress * 100)}%
                        </div>
                    )}
                </div>
            </div>

            <p className="text-xs text-gray-600 mb-3">{task.description}</p>

            {/* 进度条 */}
            {task.status === TaskStatus.RUNNING && (
                <div className="mb-3">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${task.progress * 100}%` }}
                        />
                    </div>
                </div>
            )}

            {/* 参与者 */}
            <div className="flex flex-wrap gap-1 mb-3">
                {task.participants.map((participant) => (
                    <div
                        key={participant.id}
                        className="flex items-center space-x-1 bg-white bg-opacity-70 rounded-full px-2 py-1 text-xs"
                    >
                        {getRoleIcon(participant.role as ParticipantRole)}
                        <span>{participant.name}</span>
                    </div>
                ))}
            </div>

            {/* 时间信息 */}
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                <div className="flex items-center space-x-1">
                    <Calendar className="w-3 h-3" />
                    <span>
                        {task.estimated_duration ? formatDuration(task.estimated_duration) : '-'}
                    </span>
                </div>
                <div className="flex items-center space-x-1">
                    <Clock className="w-3 h-3" />
                    <span>
                        {task.actual_duration ? formatDuration(task.actual_duration) : '-'}
                    </span>
                </div>
            </div>

            {/* 结果信息 */}
            {task.result && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center space-x-1">
                            <FileText className="w-3 h-3" />
                            <span>质量分数: {(task.result.quality_score * 100).toFixed(0)}%</span>
                        </div>
                        <div className="flex items-center space-x-1">
                            <TrendingUp className="w-3 h-3" />
                            <span>信心度: {(task.result.confidence * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                    {task.result.artifacts.length > 0 && (
                        <div className="mt-1 text-xs text-gray-500">
                            产出物: {task.result.artifacts.join(', ')}
                        </div>
                    )}
                </div>
            )}

            {/* 错误信息 */}
            {task.error_message && (
                <div className="mt-3 pt-3 border-t border-red-200">
                    <div className="flex items-center space-x-1 text-red-600 text-xs">
                        <AlertCircle className="w-3 h-3" />
                        <span>{task.error_message}</span>
                    </div>
                </div>
            )}
        </div>
    );
};

// 工作流程摘要组件
const WorkflowSummaryCard: React.FC<{ summary: WorkflowSummary }> = ({ summary }) => {
    return (
        <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <Target className="w-5 h-5 mr-2 text-blue-500" />
                工作流程概览
            </h2>

            {/* 总体进度 */}
            <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-600">总体进度</span>
                    <span className="text-sm font-bold text-blue-600">
                        {Math.round(summary.overall_progress * 100)}%
                    </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                        className="bg-gradient-to-r from-blue-400 to-blue-600 h-3 rounded-full transition-all duration-500"
                        style={{ width: `${summary.overall_progress * 100}%` }}
                    />
                </div>
            </div>

            {/* 统计信息 */}
            <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center">
                    <div className="text-2xl font-bold text-gray-800">{summary.total_tasks}</div>
                    <div className="text-xs text-gray-500">总任务数</div>
                </div>
                <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{summary.completed_tasks}</div>
                    <div className="text-xs text-gray-500">已完成</div>
                </div>
                <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">{summary.failed_tasks}</div>
                    <div className="text-xs text-gray-500">失败</div>
                </div>
            </div>

            {/* 完成率 */}
            <div className="mb-4">
                <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">完成率</span>
                    <span className="text-sm font-medium">
                        {Math.round(summary.completion_rate * 100)}%
                    </span>
                </div>
            </div>

            {/* 预计剩余时间 */}
            {summary.estimated_remaining && (
                <div className="mb-4">
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">预计剩余时间</span>
                        <span className="text-sm font-medium text-blue-600">
                            {summary.estimated_remaining}
                        </span>
                    </div>
                </div>
            )}

            {/* 参与者 */}
            <div>
                <div className="text-sm font-medium text-gray-600 mb-2">参与者</div>
                <div className="flex flex-wrap gap-1">
                    {summary.participants.map((participant, index) => (
                        <span
                            key={index}
                            className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full"
                        >
                            {participant}
                        </span>
                    ))}
                </div>
            </div>
        </div>
    );
};

// 任务树可视化组件
const TaskTreeView: React.FC<{
    task: Task;
    onTaskSelect?: (task: Task) => void;
    level?: number;
}> = ({ task, onTaskSelect, level = 0 }) => {
    const [isExpanded, setIsExpanded] = useState(true);

    return (
        <div className={`${level > 0 ? 'ml-6 border-l-2 border-gray-200 pl-4' : ''}`}>
            <TaskCard
                task={task}
                onSelect={onTaskSelect}
                isRoot={level === 0}
            />

            {/* 子任务 */}
            {task.children && task.children.length > 0 && (
                <div className={`${isExpanded ? 'block' : 'hidden'}`}>
                    {task.children.map((child) => (
                        <TaskTreeView
                            key={child.id}
                            task={child}
                            onTaskSelect={onTaskSelect}
                            level={level + 1}
                        />
                    ))}
                </div>
            )}
        </div>
    );
};

// 主组件
export const TaskLifecycleVisualizer: React.FC<TaskLifecycleVisualizerProps> = ({
    workflowSummary,
    taskTree,
    onTaskSelect,
    className = ""
}) => {
    const [selectedTask, setSelectedTask] = useState<Task | null>(null);

    const handleTaskSelect = (task: Task) => {
        setSelectedTask(task);
        onTaskSelect?.(task);
    };

    return (
        <div className={`space-y-6 ${className}`}>
            {/* 工作流程摘要 */}
            {workflowSummary && (
                <WorkflowSummaryCard summary={workflowSummary} />
            )}

            {/* 任务树 */}
            {taskTree && (
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                        <Users className="w-5 h-5 mr-2 text-green-500" />
                        任务执行详情
                    </h2>
                    <TaskTreeView task={taskTree} onTaskSelect={handleTaskSelect} />
                </div>
            )}

            {/* 任务详情面板 */}
            {selectedTask && (
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                        <FileText className="w-5 h-5 mr-2 text-purple-500" />
                        任务详情
                    </h2>

                    <div className="space-y-4">
                        <div>
                            <h3 className="font-medium text-gray-700 mb-2">基本信息</h3>
                            <div className="bg-gray-50 rounded p-3 text-sm">
                                <div className="grid grid-cols-2 gap-2">
                                    <div>任务ID: {selectedTask.id}</div>
                                    <div>状态: {selectedTask.status}</div>
                                    <div>创建时间: {new Date(selectedTask.created_at).toLocaleString()}</div>
                                    {selectedTask.started_at && (
                                        <div>开始时间: {new Date(selectedTask.started_at).toLocaleString()}</div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {selectedTask.result && (
                            <div>
                                <h3 className="font-medium text-gray-700 mb-2">执行结果</h3>
                                <div className="bg-gray-50 rounded p-3 text-sm">
                                    <div className="mb-2">
                                        <strong>质量分数:</strong> {(selectedTask.result.quality_score * 100).toFixed(1)}%
                                    </div>
                                    <div className="mb-2">
                                        <strong>信心度:</strong> {(selectedTask.result.confidence * 100).toFixed(1)}%
                                    </div>
                                    {selectedTask.result.artifacts.length > 0 && (
                                        <div className="mb-2">
                                            <strong>产出物:</strong>
                                            <ul className="list-disc list-inside ml-2">
                                                {selectedTask.result.artifacts.map((artifact, index) => (
                                                    <li key={index}>{artifact}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                    <div>
                                        <strong>内容摘要:</strong>
                                        <div className="mt-1 p-2 bg-white rounded border text-xs max-h-32 overflow-y-auto">
                                            {typeof selectedTask.result.content === 'string'
                                                ? selectedTask.result.content.substring(0, 300) + '...'
                                                : JSON.stringify(selectedTask.result.content, null, 2).substring(0, 300) + '...'
                                            }
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default TaskLifecycleVisualizer;
