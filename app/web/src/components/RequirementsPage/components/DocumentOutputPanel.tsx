import React, { useState } from 'react';
import {
    DocumentTextIcon,
    ArrowDownTrayIcon,
    ClipboardDocumentIcon,
    EyeIcon,
    ChevronDownIcon,
    ChevronUpIcon
} from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';
import { useRequirementsContext } from '../RequirementsPageContext';

export function DocumentOutputPanel() {
    const {
        chatHistory,
        workflowSummary,
        taskTree
    } = useRequirementsContext();

    const [isExpanded, setIsExpanded] = useState(false);
    const [activeDocumentTab, setActiveDocumentTab] = useState<'requirement' | 'analysis' | 'summary'>('requirement');

    // 提取最终需求文档
    const finalRequirementDoc = React.useMemo(() => {
        // 查找包含"需求规格说明书"、"最终报告"等关键词的消息
        const docMessages = chatHistory.filter(msg =>
            msg.type === 'assistant' && (
                msg.content.includes('需求规格说明书') ||
                msg.content.includes('最终报告') ||
                msg.content.includes('分析结果') ||
                msg.agent === '最终报告' ||
                msg.agent === '技术文档师' ||
                msg.agent === '质量评审师'
            )
        );

        // 返回最新的文档消息
        return docMessages.length > 0 ? docMessages[docMessages.length - 1] : null;
    }, [chatHistory]);

    // 提取分析报告
    const analysisReport = React.useMemo(() => {
        const analysisMessages = chatHistory.filter(msg =>
            msg.type === 'assistant' && (
                msg.agent === '业务分析师' ||
                msg.content.includes('分析总结') ||
                msg.content.includes('业务流程')
            )
        );
        return analysisMessages.length > 0 ? analysisMessages[analysisMessages.length - 1] : null;
    }, [chatHistory]);

    // 生成工作流摘要文档
    const workflowSummaryDoc = React.useMemo(() => {
        if (!workflowSummary || !taskTree) return null;

        return {
            content: `# 需求分析工作流摘要\n\n## 执行概况\n- **总任务数**: ${workflowSummary.total_tasks || 0}\n- **已完成**: ${workflowSummary.completed_tasks || 0}\n- **完成率**: ${Math.round((workflowSummary.completion_rate || 0) * 100)}%\n- **参与智能体**: ${workflowSummary.participants?.join(', ') || '无'}\n\n## 任务详情\n${taskTree.tasks ? taskTree.tasks.map((task: any) => `\n### ${task.name || '未命名任务'}\n- **状态**: ${task.status || '未知'}\n- **负责人**: ${task.assignee || '未分配'}\n- **完成时间**: ${task.completion_time || '未完成'}\n- **质量分数**: ${task.quality_score ? (task.quality_score * 100).toFixed(0) + '%' : '未评估'}\n`).join('\n') : '暂无任务详情'}\n\n## 产出物清单\n${workflowSummary.artifacts ? workflowSummary.artifacts.map((artifact: string) => `- ${artifact}`).join('\n') : '- 暂无产出物'}\n`,
            timestamp: new Date(),
            agent: '工作流程管理器'
        };
    }, [workflowSummary, taskTree]);

    const handleDownload = (content: string, filename: string) => {
        const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const handleCopy = async (content: string) => {
        try {
            await navigator.clipboard.writeText(content);
            // 可以添加成功提示
        } catch (err) {
            console.error('复制失败:', err);
        }
    };

    const hasDocuments = finalRequirementDoc || analysisReport || workflowSummaryDoc;

    return (
        <div className="border-t border-gray-700 flex flex-col h-full">
            {/* 文档面板头部 */}
            <div className="p-4 bg-gray-750 flex-shrink-0">
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="w-full flex items-center justify-between text-left"
                >
                    <div className="flex items-center space-x-2">
                        <DocumentTextIcon className="h-5 w-5 text-blue-400" />
                        <span className="font-medium text-white">需求文档输出</span>
                        {hasDocuments && (
                            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                        )}
                    </div>
                    {isExpanded ? (
                        <ChevronUpIcon className="h-5 w-5 text-gray-400" />
                    ) : (
                        <ChevronDownIcon className="h-5 w-5 text-gray-400" />
                    )}
                </button>

                {!isExpanded && hasDocuments && (
                    <div className="mt-2 text-xs text-gray-400">
                        已生成 {[finalRequirementDoc, analysisReport, workflowSummaryDoc].filter(Boolean).length} 个文档
                    </div>
                )}
            </div>

            {/* 文档内容 */}
            {isExpanded && (
                <div className="flex-1 overflow-y-auto min-h-0">
                    {hasDocuments ? (
                        <div className="p-4">
                            {/* 文档标签页 */}
                            <div className="flex space-x-1 mb-4 border-b border-gray-700">
                                {finalRequirementDoc && (
                                    <button
                                        onClick={() => setActiveDocumentTab('requirement')}
                                        className={`px-3 py-2 text-xs font-medium rounded-t-lg transition-colors ${activeDocumentTab === 'requirement'
                                            ? 'bg-blue-600 text-white border-b-2 border-blue-400'
                                            : 'text-gray-400 hover:text-gray-200'
                                            }`}
                                    >
                                        📋 需求规格说明书
                                    </button>
                                )}
                                {analysisReport && (
                                    <button
                                        onClick={() => setActiveDocumentTab('analysis')}
                                        className={`px-3 py-2 text-xs font-medium rounded-t-lg transition-colors ${activeDocumentTab === 'analysis'
                                            ? 'bg-blue-600 text-white border-b-2 border-blue-400'
                                            : 'text-gray-400 hover:text-gray-200'
                                            }`}
                                    >
                                        📊 分析报告
                                    </button>
                                )}
                                {workflowSummaryDoc && (
                                    <button
                                        onClick={() => setActiveDocumentTab('summary')}
                                        className={`px-3 py-2 text-xs font-medium rounded-t-lg transition-colors ${activeDocumentTab === 'summary'
                                            ? 'bg-blue-600 text-white border-b-2 border-blue-400'
                                            : 'text-gray-400 hover:text-gray-200'
                                            }`}
                                    >
                                        🔄 工作流摘要
                                    </button>
                                )}
                            </div>

                            {/* 当前文档内容 */}
                            <div className="space-y-4">
                                {activeDocumentTab === 'requirement' && finalRequirementDoc && (
                                    <DocumentView
                                        title="需求规格说明书"
                                        content={finalRequirementDoc.content}
                                        timestamp={finalRequirementDoc.timestamp}
                                        agent={finalRequirementDoc.agent}
                                        onDownload={() => handleDownload(finalRequirementDoc.content, '需求规格说明书.md')}
                                        onCopy={() => handleCopy(finalRequirementDoc.content)}
                                    />
                                )}

                                {activeDocumentTab === 'analysis' && analysisReport && (
                                    <DocumentView
                                        title="业务分析报告"
                                        content={analysisReport.content}
                                        timestamp={analysisReport.timestamp}
                                        agent={analysisReport.agent}
                                        onDownload={() => handleDownload(analysisReport.content, '业务分析报告.md')}
                                        onCopy={() => handleCopy(analysisReport.content)}
                                    />
                                )}

                                {activeDocumentTab === 'summary' && workflowSummaryDoc && (
                                    <DocumentView
                                        title="工作流执行摘要"
                                        content={workflowSummaryDoc.content}
                                        timestamp={workflowSummaryDoc.timestamp}
                                        agent={workflowSummaryDoc.agent}
                                        onDownload={() => handleDownload(workflowSummaryDoc.content, '工作流摘要.md')}
                                        onCopy={() => handleCopy(workflowSummaryDoc.content)}
                                    />
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="p-8 text-center text-gray-400">
                            <DocumentTextIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                            <div className="text-sm">
                                尚未生成需求文档
                            </div>
                            <div className="text-xs mt-1 opacity-75">
                                完成需求分析后，文档将自动在此处显示
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

interface DocumentViewProps {
    title: string;
    content: string;
    timestamp: Date;
    agent?: string;
    onDownload: () => void;
    onCopy: () => void;
}

function DocumentView({ title, content, timestamp, agent, onDownload, onCopy }: DocumentViewProps) {
    const [isPreviewMode, setIsPreviewMode] = useState(true);

    return (
        <div className="space-y-3">
            {/* 文档头部信息 */}
            <div className="flex items-center justify-between">
                <div>
                    <h4 className="text-sm font-medium text-white">{title}</h4>
                    <div className="text-xs text-gray-400">
                        {agent && `由 ${agent} 生成`} · {timestamp.toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                        {content.length} 字符
                    </div>
                </div>
                <div className="flex space-x-2">
                    <button
                        onClick={() => setIsPreviewMode(!isPreviewMode)}
                        className="p-2 rounded-full hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
                        title={isPreviewMode ? '切换到原始模式' : '切换到预览模式'}
                    >
                        <EyeIcon className="h-4 w-4" />
                    </button>
                    <button
                        onClick={onCopy}
                        className="p-2 rounded-full hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
                        title="复制内容"
                    >
                        <ClipboardDocumentIcon className="h-4 w-4" />
                    </button>
                    <button
                        onClick={onDownload}
                        className="p-2 rounded-full hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
                        title="下载文档"
                    >
                        <ArrowDownTrayIcon className="h-4 w-4" />
                    </button>
                </div>
            </div>

            {/* 文档内容区域 */}
            <div className="bg-gray-800 rounded-lg p-4 overflow-auto" style={{ maxHeight: isPreviewMode ? 'none' : '300px' }}>
                {isPreviewMode ? (
                    <ReactMarkdown
                        className="prose prose-sm max-w-none prose-invert"
                        components={{
                            p: ({ children }) => <p className="mb-2 last:mb-0 text-gray-300">{children}</p>,
                            ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1 text-gray-300">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1 text-gray-300">{children}</ol>,
                            li: ({ children }) => <li className="text-gray-300">{children}</li>,
                            strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
                            h1: ({ children }) => <h1 className="text-xl font-bold text-white mb-3">{children}</h1>,
                            h2: ({ children }) => <h2 className="text-lg font-bold text-white mb-2">{children}</h2>,
                            h3: ({ children }) => <h3 className="text-base font-bold text-white mb-2">{children}</h3>,
                            code: ({ children }) => <code className="bg-gray-700 text-gray-200 rounded px-1 py-0.5 text-xs">{children}</code>,
                            pre: ({ children }) => <pre className="bg-gray-700 rounded-lg p-3 overflow-x-auto text-gray-200 text-xs">{children}</pre>,
                        }}
                    >
                        {content}
                    </ReactMarkdown>
                ) : (
                    <textarea
                        className="w-full h-full bg-gray-700 border border-gray-600 rounded-lg p-3 text-white text-sm font-mono focus:outline-none focus:border-blue-500 resize-none"
                        value={content}
                        readOnly
                        rows={15} // 设置初始行数，可根据内容调整
                    />
                )}
            </div>
        </div>
    );
}
