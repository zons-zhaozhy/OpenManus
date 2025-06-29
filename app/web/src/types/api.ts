/**
 * API 类型定义
 */

// 项目上下文
export interface ProjectContext {
    name: string;
    description: string;
    domain: string;
}

// 需求分析请求
export interface RequirementAnalysisRequest {
    requirement_text: string;
    action: 'requirement_matrix';
    session_id?: string;
    project_context?: ProjectContext;
}

// 需求分析响应
export interface RequirementAnalysisResponse {
    session_id: string;
    status: string;
    message: string;
    result?: {
        clarification: {
            questions: string[];
            suggestions: string[];
        };
        analysis: {
            points: string[];
            risks: string[];
        };
        metrics: {
            clarity: number;
            completeness: number;
            feasibility: number;
        };
        summary: string;
    };
    error?: string;
}

// 分析状态响应
export interface AnalysisStatusResponse {
    session_id: string;
    status: string;
    progress: number;
    current_agent?: string;
    error?: string;
}

// 错误响应
export interface ErrorResponse {
    status: 'error';
    message: string;
    error: {
        code: number;
        type: string;
        details?: any;
    };
}
