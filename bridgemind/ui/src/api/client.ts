import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface DatabaseConnector {
  tenantId: string;
  name: string;
  description?: string;
  dbType: string;
  connectionString: string;
  readOnly?: boolean;
  maxRowsPerQuery?: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatRequest {
  tenantId: string;
  messages: ChatMessage[];
  toolsAllowed?: string[];
  dryRun?: boolean;
}

export interface ChatResponse {
  answer: string;
  citations: Array<{
    type: string;
    source?: string;
    table?: string;
    url?: string;
    file?: string;
    page?: number;
    lines?: string;
  }>;
  artifacts?: {
    sql?: string;
    curl?: string;
  };
}

export interface SQLPlanRequest {
  tenantId: string;
  query: string;
  connectorId?: string;
}

export interface SQLPlanResponse {
  sql: string;
  risk: string;
  estimatedCost?: string;
  targetConnector?: string;
}

// Database Connector API
export const createDatabaseConnector = async (connector: DatabaseConnector) => {
  const response = await apiClient.post('/v1/admin/connectors/database', connector);
  return response.data;
};

export const listDatabaseConnectors = async (tenantId: string) => {
  const response = await apiClient.get('/v1/admin/connectors/database', {
    params: { tenantId },
  });
  return response.data;
};

export const getDatabaseConnector = async (connectorId: string) => {
  const response = await apiClient.get(`/v1/admin/connectors/database/${connectorId}`);
  return response.data;
};

export const deleteDatabaseConnector = async (connectorId: string) => {
  const response = await apiClient.delete(`/v1/admin/connectors/database/${connectorId}`);
  return response.data;
};

// Chat API
export const sendChatMessage = async (request: ChatRequest): Promise<ChatResponse> => {
  const response = await apiClient.post('/v1/chat', request);
  return response.data;
};

// SQL Planning API
export const planSQLQuery = async (request: SQLPlanRequest): Promise<SQLPlanResponse> => {
  const response = await apiClient.post('/v1/tools/sql/plan', request);
  return response.data;
};

export default apiClient;

