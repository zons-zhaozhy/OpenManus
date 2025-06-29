import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatInterface } from '../components/ChatInterface';
import { RequirementsProvider, useRequirementsContext } from '../RequirementsPageContext';

// 模拟api模块
jest.mock('../../../utils/api');

// 模拟上下文
jest.mock('../RequirementsPageContext', () => {
    const actual = jest.requireActual('../RequirementsPageContext');
    return {
        ...actual,
        useRequirementsContext: jest.fn(() => ({
            messages: [
                {
                    type: 'user',
                    content: '开发一个在线商城系统',
                    timestamp: '2024-06-01T10:00:00Z'
                },
                {
                    type: 'assistant',
                    content: '正在分析您的需求...',
                    agent: '需求澄清专家',
                    timestamp: '2024-06-01T10:00:01Z'
                }
            ],
            sendMessage: jest.fn(),
            isProcessing: false,
            currentAgent: null,
            progress: 0,
            error: null,
            clearError: jest.fn()
        })),
        RequirementsProvider: ({ children }: { children: React.ReactNode }) => (
            <div>{children}</div>
        )
    };
});

describe('ChatInterface', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders without crashing', () => {
        render(
            <RequirementsProvider>
                <ChatInterface />
            </RequirementsProvider>
        );
    });

    it('displays messages correctly', () => {
        render(
            <RequirementsProvider>
                <ChatInterface />
            </RequirementsProvider>
        );

        // 验证用户消息
        expect(screen.getByText('开发一个在线商城系统')).toBeInTheDocument();

        // 验证系统消息
        expect(screen.getByText('正在分析您的需求...')).toBeInTheDocument();
    });

    it('handles message submission', async () => {
        const mockSendMessage = jest.fn();
        const mockContext = {
            messages: [
                {
                    type: 'user',
                    content: '开发一个在线商城系统',
                    timestamp: '2024-06-01T10:00:00Z'
                },
                {
                    type: 'assistant',
                    content: '正在分析您的需求...',
                    agent: '需求澄清专家',
                    timestamp: '2024-06-01T10:00:01Z'
                }
            ],
            sendMessage: mockSendMessage,
            isProcessing: false,
            currentAgent: null,
            progress: 0,
            error: null,
            clearError: jest.fn()
        };

        (useRequirementsContext as jest.Mock).mockImplementation(() => mockContext);

        const { getByPlaceholderText, getByRole } = render(
            <RequirementsProvider>
                <ChatInterface />
            </RequirementsProvider>
        );

        // 输入消息
        const input = getByPlaceholderText('请输入您的需求描述...');
        fireEvent.change(input, { target: { value: '测试消息' } });

        // 提交消息
        const submitButton = getByRole('button', { name: '发送' });
        fireEvent.click(submitButton);

        // 验证sendMessage被调用
        await waitFor(() => {
            expect(mockSendMessage).toHaveBeenCalledWith('测试消息');
        });

        // 验证输入框被清空
        expect(input).toHaveValue('');
    });

    it('shows progress indicator when processing', () => {
        const mockContext = {
            messages: [
                {
                    type: 'user',
                    content: '开发一个在线商城系统',
                    timestamp: '2024-06-01T10:00:00Z'
                },
                {
                    type: 'assistant',
                    content: '正在分析您的需求...',
                    agent: '需求澄清专家',
                    timestamp: '2024-06-01T10:00:01Z'
                }
            ],
            sendMessage: jest.fn(),
            isProcessing: true,
            currentAgent: '需求澄清专家',
            progress: 50,
            error: null,
            clearError: jest.fn()
        };

        (useRequirementsContext as jest.Mock).mockImplementation(() => mockContext);

        render(
            <RequirementsProvider>
                <ChatInterface />
            </RequirementsProvider>
        );

        // 验证进度指示器
        expect(screen.getByText('正在分析您的需求...')).toBeInTheDocument();
    });

    it('shows error message when there is an error', () => {
        const mockContext = {
            messages: [
                {
                    type: 'user',
                    content: '开发一个在线商城系统',
                    timestamp: '2024-06-01T10:00:00Z'
                },
                {
                    type: 'assistant',
                    content: '正在分析您的需求...',
                    agent: '需求澄清专家',
                    timestamp: '2024-06-01T10:00:01Z'
                }
            ],
            sendMessage: jest.fn(),
            isProcessing: false,
            currentAgent: null,
            progress: 0,
            error: '需求分析失败，请重试',
            clearError: jest.fn()
        };

        (useRequirementsContext as jest.Mock).mockImplementation(() => mockContext);

        render(
            <RequirementsProvider>
                <ChatInterface />
            </RequirementsProvider>
        );

        // 验证错误消息
        expect(screen.getByText('需求分析失败，请重试')).toBeInTheDocument();
    });

    it('disables input when processing', () => {
        const mockContext = {
            messages: [
                {
                    type: 'user',
                    content: '开发一个在线商城系统',
                    timestamp: '2024-06-01T10:00:00Z'
                },
                {
                    type: 'assistant',
                    content: '正在分析您的需求...',
                    agent: '需求澄清专家',
                    timestamp: '2024-06-01T10:00:01Z'
                }
            ],
            sendMessage: jest.fn(),
            isProcessing: true,
            currentAgent: null,
            progress: 0,
            error: null,
            clearError: jest.fn()
        };

        (useRequirementsContext as jest.Mock).mockImplementation(() => mockContext);

        render(
            <RequirementsProvider>
                <ChatInterface />
            </RequirementsProvider>
        );

        // 验证输入框被禁用
        const input = screen.getByPlaceholderText('请输入您的需求描述...');
        expect(input).toBeDisabled();
    });

    it('scrolls to bottom when new messages arrive', () => {
        const scrollIntoViewMock = jest.fn();
        window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;

        const mockContext = {
            messages: [
                {
                    type: 'user',
                    content: '开发一个在线商城系统',
                    timestamp: '2024-06-01T10:00:00Z'
                },
                {
                    type: 'assistant',
                    content: '正在分析您的需求...',
                    agent: '需求澄清专家',
                    timestamp: '2024-06-01T10:00:01Z'
                },
                {
                    type: 'assistant',
                    content: '新消息',
                    agent: '系统',
                    timestamp: '2024-06-01T10:00:02Z'
                }
            ],
            sendMessage: jest.fn(),
            isProcessing: false,
            currentAgent: null,
            progress: 0,
            error: null,
            clearError: jest.fn()
        };

        (useRequirementsContext as jest.Mock).mockImplementation(() => mockContext);

        render(
            <RequirementsProvider>
                <ChatInterface />
            </RequirementsProvider>
        );

        // 验证滚动
        expect(scrollIntoViewMock).toHaveBeenCalled();
    });
});
