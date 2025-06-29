/**
 * 类型定义
 * 提供全局共享的TypeScript类型定义
 */

// 需求分析相关类型
export interface RequirementInput {
    content: string;
    projectId?: string;
    projectContext?: string;
    useMultiDimensional?: boolean;
    enableConflictDetection?: boolean;
}

export interface ClarificationRequest {
    sessionId: string;
    answer: string;
    question?: string;
}

export interface AnalysisRequest {
    sessionId: string;
    answer: string;
}

export interface RequirementStatus {
    sessionId: string;
    stage: string;
    progress: {
        percentage: number;
        currentStage: string;
        roundCount: number;
        totalRounds: number;
    };
    result?: string;
}

// 会话相关类型
export interface Session {
    id: string;
    requirementText: string;
    clarificationHistory: ClarificationHistory[];
    roundCount: number;
    initialAnalysis: any;
    status: 'active' | 'completed' | 'error';
    startTime: string;
    lastUpdateTime: string;
}

export interface ClarificationHistory {
    question: string;
    answer: string;
    timestamp: string;
}

// 架构设计相关类型
export interface ArchitectureRequest {
    requirementsDoc: string;
    sessionId?: string;
    sourceRequirementsSessionId?: string;
    projectConstraints?: Record<string, any>;
}

export interface ArchitectureResponse {
    sessionId: string;
    architectureDoc: string;
    diagrams: string[];
    recommendations: string[];
    technicalStack: string[];
    qualityAttributes: Record<string, number>;
}

// UI组件相关类型
export interface TabProps {
    label: string;
    value: string;
    icon?: React.ReactNode;
    disabled?: boolean;
}

export interface PanelProps {
    children: React.ReactNode;
    value: string;
    index: string;
}

// 分析指标相关类型
export interface AnalysisMetrics {
    clarityScore: number;
    completenessScore: number;
    consistencyScore: number;
    feasibilityScore: number;
    overallQuality: number;
    recommendations: string[];
    warnings: string[];
}

// 思维链相关类型
export interface ThinkActReflectData {
    thoughts: string[];
    actions: string[];
    reflections: string[];
    insights: string[];
    nextSteps: string[];
}

// 智能体相关类型
export interface Agent {
    id: string;
    name: string;
    role: string;
    status: 'idle' | 'working' | 'error';
    lastAction?: string;
    lastUpdate?: string;
}
