import React from 'react';
import { Tag } from 'antd';

interface StatusIndicatorProps {
  status: string;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status }) => {
  let color;
  switch (status) {
    case '未连接':
      color = 'default';
      break;
    case '已连接':
      color = 'success';
      break;
    case '澄清中':
      color = 'processing';
      break;
    case '分析中':
      color = 'warning';
      break;
    case '生成文档中':
      color = 'error';
      break;
    default:
      color = 'default';
  }

  return (
    <Tag color={color} style={{ marginBottom: 16 }}>
      当前状态: {status}
    </Tag>
  );
};

export default StatusIndicator;
