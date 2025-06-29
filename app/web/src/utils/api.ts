/**
 * API工具函数
 * 提供与后端API交互的工具函数
 */

import axios from 'axios';
import {
    RequirementAnalysisRequest,
    RequirementAnalysisResponse,
    AnalysisStatusResponse,
    ErrorResponse
} from '../types/api';

// 获取环境变量
const getEnvVar = (key: string): string => {
    // 优先使用 import.meta.env
    if (typeof import.meta !== 'undefined' && import.meta.env) {
        return import.meta.env[key];
    }
    // 回退到 window.env 或 global.env
    // @ts-ignore
    const env = typeof window !== 'undefined' ? window.env : global.env;
    return env ? env[key] : '';
};

const API_BASE_URL = getEnvVar('VITE_API_BASE_URL') || 'http://localhost:8000';

// API客户端实例
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// 请求拦截器
apiClient.interceptors.request.use(
    config => {
        console.log('发送请求:', {
            url: config.url,
            method: config.method,
            data: config.data
        });
        return config;
    },
    error => {
        console.error('请求配置错误:', error);
        return Promise.reject(error);
    }
);

// 响应拦截器
apiClient.interceptors.response.use(
    response => {
        console.log('收到响应:', {
            url: response.config.url,
            status: response.status,
            data: response.data
        });
        return response;
    },
    error => {
        if (error.response) {
            // 服务器返回错误状态码
            console.error('API请求失败:', {
                url: error.config.url,
                status: error.response.status,
                data: error.response.data,
                headers: error.response.headers
            });
        } else if (error.request) {
            // 请求已发送但没有收到响应
            console.error('未收到响应:', {
                url: error.config.url,
                request: error.request
            });
        } else {
            // 请求配置出错
            console.error('请求配置错误:', error.message);
        }
        return Promise.reject(error);
    }
);

// 需求分析API
export const requirementsApi = {
    // 分析需求
    analyzeRequirement: async (content: string): Promise<RequirementAnalysisResponse> => {
        try {
            console.log('发送需求分析请求:', content);
            const request: RequirementAnalysisRequest = {
                requirement_text: content,
                action: 'requirement_matrix'
            };
            const response = await apiClient.post<RequirementAnalysisResponse>('/api/requirements/analyze', request);
            console.log('需求分析响应:', response.data);
            return response.data;
        } catch (error) {
            console.error('需求分析请求失败:', error);
            throw error;
        }
    },

    // 工作流程分析
    analyzeWorkflow: async (content: string) => {
        try {
            console.log('发送工作流分析请求:', content);
            const response = await apiClient.post('/api/requirements/workflow/start', {
                workflow_type: 'requirements_analysis',
                requirement_text: content,
                project_context: '智能需求分析项目'
            });
            console.log('工作流分析响应:', response.data);
            return response.data;
        } catch (error) {
            console.error('工作流分析请求失败:', error);
            throw error;
        }
    },

    // 澄清需求
    clarifyRequirement: async (content: string) => {
        try {
            console.log('发送需求澄清请求:', content);
            const response = await apiClient.post('/api/requirements/clarification/question', {
                requirement: content
            });
            console.log('需求澄清响应:', response.data);
            return response.data;
        } catch (error) {
            console.error('需求澄清请求失败:', error);
            throw error;
        }
    },

    // 处理澄清回答
    processAnswer: async (content: string, context?: any) => {
        try {
            console.log('发送澄清回答请求:', { content, context });
            const response = await apiClient.post('/api/requirements/clarification/answer', {
                answer: content,
                context: context,
            });
            console.log('澄清回答响应:', response.data);
            return response.data;
        } catch (error) {
            console.error('澄清回答请求失败:', error);
            throw error;
        }
    },

    // 获取分析流
    getAnalysisStream: async (content: string) => {
        try {
            console.log('发送分析流请求:', content);
            const response = await apiClient.post('/api/requirements/analyze/stream', {
                requirement_text: content
            });
            console.log('分析流响应:', response.data);
            return response.data;
        } catch (error) {
            console.error('分析流请求失败:', error);
            throw error;
        }
    },

    // 获取会话信息
    getSession: async (sessionId: string) => {
        try {
            console.log('发送获取会话请求:', sessionId);
            const response = await apiClient.get(`/api/requirements/session/${sessionId}`);
            console.log('获取会话响应:', response.data);
            return response.data;
        } catch (error) {
            console.error('获取会话请求失败:', error);
            throw error;
        }
    },

    // 获取活跃会话列表
    getActiveSessions: async () => {
        try {
            console.log('发送获取活跃会话列表请求');
            const response = await apiClient.get('/api/requirements/session/active/list');
            console.log('获取活跃会话列表响应:', response.data);
            return response.data;
        } catch (error) {
            console.error('获取活跃会话列表请求失败:', error);
            throw error;
        }
    },

    // 获取分析进度
    getAnalysisProgress: async (taskId: string) => {
        try {
            console.log('发送获取分析进度请求:', taskId);
            const response = await apiClient.get(`/api/requirements/analyze/progress/${taskId}`);
            console.log('获取分析进度响应:', response.data);
            return response.data;
        } catch (error) {
            console.error('获取分析进度请求失败:', error);
            throw error;
        }
    },

    // 取消分析任务
    cancelAnalysis: async (taskId: string) => {
        try {
            console.log('发送取消分析请求:', taskId);
            const response = await apiClient.post(`/api/requirements/analyze/cancel/${taskId}`);
            console.log('取消分析响应:', response.data);
            return response.data;
        } catch (error) {
            console.error('取消分析请求失败:', error);
            throw error;
        }
    },

    // 重试分析任务
    retryAnalysis: async (taskId: string) => {
        try {
            console.log('发送重试分析请求:', taskId);
            const response = await apiClient.post(`/api/requirements/analyze/retry/${taskId}`);
            console.log('重试分析响应:', response.data);
            return response.data;
        } catch (error) {
            console.error('重试分析请求失败:', error);
            throw error;
        }
    },

    // 获取智能体状态
    getAgentStatus: async (agentId: string) => {
        try {
            console.log('发送获取智能体状态请求:', agentId);
            const response = await apiClient.get(`/api/requirements/agent/status/${agentId}`);
            console.log('获取智能体状态响应:', response.data);
            return response.data;
        } catch (error) {
            console.error('获取智能体状态请求失败:', error);
            throw error;
        }
    },

    // 获取系统性能指标
    getPerformanceMetrics: async () => {
        try {
            console.log('发送获取性能指标请求');
            const response = await apiClient.get('/api/requirements/metrics');
            console.log('获取性能指标响应:', response.data);
            return response.data;
        } catch (error) {
            console.error('获取性能指标请求失败:', error);
            throw error;
        }
    },

    // 获取分析状态
    getAnalysisStatus: async (sessionId: string): Promise<AnalysisStatusResponse> => {
        try {
            const response = await apiClient.get<AnalysisStatusResponse>(`/api/requirements/status/${sessionId}`);
            return response.data;
        } catch (error) {
            console.error('获取分析状态失败:', error);
            throw error;
        }
    }
};

// 架构设计API
export const architectureApi = {
    // 分析架构
    analyzeArchitecture: async (requirementsDoc: string) => {
        const response = await apiClient.post('/api/architecture/analyze', {
            requirements_doc: requirementsDoc,
        });
        return response.data;
    },

    // 获取架构建议
    getArchitectureRecommendations: async (sessionId: string) => {
        const response = await apiClient.get(`/api/architecture/${sessionId}/recommendations`);
        return response.data;
    },
};
