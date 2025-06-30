interface WebSocketMessage {
  type: string;
  data: string;
  status?: string;
}

class WebSocketService {
  private url: string;
  private ws: WebSocket | null = null;
  private onMessageCallback: (message: WebSocketMessage) => void;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectInterval: number = 3000;

  constructor(url: string, onMessageCallback: (message: WebSocketMessage) => void) {
    this.url = url;
    this.onMessageCallback = onMessageCallback;
  }

  connect(): void {
    this.ws = new WebSocket(this.url);
    this.setupEventListeners();
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.reconnectAttempts = 0;
    }
  }

  sendMessage(message: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const payload: WebSocketMessage = {
        type: 'user_input',
        data: message,
      };
      this.ws.send(JSON.stringify(payload));
    } else {
      console.error('WebSocket is not connected.');
    }
  }

  private setupEventListeners(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      const initMessage: WebSocketMessage = {
        type: 'connection',
        data: 'Frontend connected',
        status: '已连接',
      };
      this.onMessageCallback(initMessage);
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.onMessageCallback(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
        const errorMessage: WebSocketMessage = {
          type: 'error',
          data: `Error parsing message: ${error}`,
        };
        this.onMessageCallback(errorMessage);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      const errorMessage: WebSocketMessage = {
        type: 'error',
        data: `WebSocket error: ${error}`,
        status: '错误',
      };
      this.onMessageCallback(errorMessage);
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed');
      const closeMessage: WebSocketMessage = {
        type: 'connection',
        data: 'WebSocket connection closed',
        status: '未连接',
      };
      this.onMessageCallback(closeMessage);
      this.attemptReconnect();
    };
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})...`);
        this.reconnectAttempts++;
        this.connect();
      }, this.reconnectInterval);
    } else {
      console.error('Max reconnect attempts reached. Could not reconnect to WebSocket.');
      const failMessage: WebSocketMessage = {
        type: 'error',
        data: 'Failed to reconnect after maximum attempts',
        status: '未连接',
      };
      this.onMessageCallback(failMessage);
    }
  }
}

export default WebSocketService;
