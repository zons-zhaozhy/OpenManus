import React, { useState, useEffect } from 'react';
import { Layout, Typography, Button, Input } from 'antd';
import '../App.css';
import LogView from '../components/LogView';
import StatusIndicator from '../components/StatusIndicator';
import WebSocketService from '../services/WebSocketService';

const { Header, Content, Footer } = Layout;
const { Title } = Typography;
const { TextArea } = Input;

const AnalysisPage: React.FC = () => {
  const [wsService, setWsService] = useState<WebSocketService | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [status, setStatus] = useState<string>('未连接');
  const [inputValue, setInputValue] = useState<string>('');

  useEffect(() => {
    const service = new WebSocketService(
      'ws://localhost:8000/ws/requirements/session1',
      (message) => {
        setLogs((prevLogs) => [...prevLogs, message.data]);
        setStatus(message.status || '已连接');
      }
    );
    service.connect();
    setWsService(service);

    return () => {
      service.disconnect();
    };
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
  };

  const handleSendMessage = () => {
    if (wsService && inputValue.trim()) {
      wsService.sendMessage(inputValue);
      setInputValue('');
    }
  };

  return (
    <Layout className="layout" style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: 0 }}>
        <Title level={3} style={{ margin: '16px', textAlign: 'center' }}>
          需求分析助手
        </Title>
      </Header>
      <Content style={{ margin: '24px 16px 0', overflow: 'initial' }}>
        <div style={{ padding: 24, background: '#fff', textAlign: 'center' }}>
          <StatusIndicator status={status} />
          <TextArea
            rows={4}
            value={inputValue}
            onChange={handleInputChange}
            placeholder="请输入您的需求或问题..."
            style={{ marginBottom: 16 }}
          />
          <Button type="primary" onClick={handleSendMessage} style={{ marginBottom: 16 }}>
            发送
          </Button>
          <LogView logs={logs} />
        </div>
      </Content>
      <Footer style={{ textAlign: 'center' }}>
        OpenManus ©2025 需求分析系统
      </Footer>
    </Layout>
  );
};

export default AnalysisPage;
