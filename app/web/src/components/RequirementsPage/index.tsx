import React, { useState, useEffect } from 'react';
import { RequirementsPageProvider } from './RequirementsPageContext';
import { ChatInterface } from './components/ChatInterface';
import { WorkflowPanel } from './components/WorkflowPanel';
import { ResultPanel } from './components/ResultPanel';
import { AgentTeamPanel } from './components/AgentTeamPanel';
import { DocumentOutputPanel } from './components/DocumentOutputPanel';

/**
 * 需求分析页面 - 重构版本
 *
 * 重构原则：
 * - 组件化：拆分成多个专职组件
 * - 状态管理：使用Context集中管理状态
 * - 自定义Hook：封装业务逻辑
 * - 可维护性：清晰的组件层次和职责划分
 */
export function RequirementsPage() {
    const [isWorkflowCollapsed, setIsWorkflowCollapsed] = useState(() => {
        return localStorage.getItem('reqPage_workflowCollapsed') === 'true';
    });

    const [activeRightPanelTab, setActiveRightPanelTab] = useState<'progress' | 'documents'>('progress');

    // 持久化折叠状态
    useEffect(() => {
        localStorage.setItem('reqPage_workflowCollapsed', String(isWorkflowCollapsed));
    }, [isWorkflowCollapsed]);

    return (
        <RequirementsPageProvider>
            <div className="bg-gray-900 text-white flex overflow-hidden" style={{ height: 'calc(100vh - 120px)' }}>
                {/* 主内容区域 - 聊天界面 */}
                <div className="flex-1 flex flex-col min-w-0">
                    {/* 工作流面板 - 可折叠 */}
                    <div className="flex-shrink-0">
                        <WorkflowPanel
                            isCollapsed={isWorkflowCollapsed}
                            onToggleCollapse={() => setIsWorkflowCollapsed(!isWorkflowCollapsed)}
                        />
                    </div>

                    {/* 聊天界面 - 占据剩余空间 */}
                    <div className="flex-1 min-h-0">
                        <ChatInterface />
                    </div>

                    {/* 结果展示面板 - 如果有内容才显示 */}
                    <div className="flex-shrink-0">
                        <ResultPanel />
                    </div>
                </div>

                {/* 右侧面板 - 页签模式 */}
                <div className="w-[25vw] bg-gray-800 border-l border-gray-700 flex flex-col flex-shrink-0 overflow-hidden">
                    {/* 页签导航 */}
                    <div className="flex-shrink-0 border-b border-gray-700">
                        <div className="flex">
                            <button
                                onClick={() => setActiveRightPanelTab('progress')}
                                className={`flex-1 py-3 text-sm font-medium text-center transition-colors ${activeRightPanelTab === 'progress'
                                    ? 'text-blue-400 border-b-2 border-blue-400'
                                    : 'text-gray-400 hover:text-gray-200'
                                    }`}
                            >
                                🔄 处理进度
                            </button>
                            <button
                                onClick={() => setActiveRightPanelTab('documents')}
                                className={`flex-1 py-3 text-sm font-medium text-center transition-colors ${activeRightPanelTab === 'documents'
                                    ? 'text-blue-400 border-b-2 border-blue-400'
                                    : 'text-gray-400 hover:text-gray-200'
                                    }`}
                            >
                                📄 需求文档输出
                            </button>
                        </div>
                    </div>

                    {/* 页签内容 */}
                    <div className="flex-1 overflow-auto">
                        {activeRightPanelTab === 'progress' && (
                            <div className="p-4">
                                <AgentTeamPanel />
                            </div>
                        )}
                        {activeRightPanelTab === 'documents' && (
                            <DocumentOutputPanel />
                        )}
                    </div>
                </div>
            </div>
        </RequirementsPageProvider>
    );
}
