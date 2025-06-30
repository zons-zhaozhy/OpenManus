import React from 'react';
import { List } from 'antd';

interface LogViewProps {
  logs: string[];
}

const LogView: React.FC<LogViewProps> = ({ logs }) => {
  return (
    <div style={{ height: '400px', overflowY: 'auto', border: '1px solid #e8e8e8', padding: '8px' }}>
      <List
        dataSource={logs}
        renderItem={(item, index) => (
          <List.Item style={{ padding: '4px 0', border: 'none' }}>
            <span style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>{item}</span>
          </List.Item>
        )}
        style={{ height: '100%', overflowY: 'auto' }}
      />
    </div>
  );
};

export default LogView;
