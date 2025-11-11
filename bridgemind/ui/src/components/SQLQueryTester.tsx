import React, { useState } from 'react';
import { planSQLQuery, SQLPlanRequest } from '../api/client';

interface SQLQueryTesterProps {
  tenantId: string;
  connectors?: Array<{ connectorId: string; name: string }>;
}

const SQLQueryTester: React.FC<SQLQueryTesterProps> = ({ tenantId, connectors = [] }) => {
  const [query, setQuery] = useState('');
  const [selectedConnector, setSelectedConnector] = useState<string>('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const exampleQueries = [
    "What's our refund rate by month?",
    "Show me customer analytics by country",
    "How many orders do we have per status?",
    "What's the average order amount?",
    "List top 5 customers by order count",
  ];

  const handlePlanQuery = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const request: SQLPlanRequest = {
        tenantId,
        query,
        connectorId: selectedConnector || undefined,
      };

      const response = await planSQLQuery(request);
      setResult(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to plan query');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sql-query-tester">
      <h2>SQL Query Tester</h2>
      <p>Enter a natural language query to see the generated SQL plan</p>

      {connectors.length > 0 && (
        <div className="form-group">
          <label>Database Connector (Optional)</label>
          <select
            value={selectedConnector}
            onChange={(e) => setSelectedConnector(e.target.value)}
          >
            <option value="">Auto-select</option>
            {connectors.map(conn => (
              <option key={conn.connectorId} value={conn.connectorId}>
                {conn.name}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="example-queries">
        <label>Example Queries:</label>
        <div className="query-chips">
          {exampleQueries.map((example, idx) => (
            <button
              key={idx}
              type="button"
              className="query-chip"
              onClick={() => setQuery(example)}
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>Natural Language Query</label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., What's our refund rate by month?"
          rows={4}
        />
      </div>

      <button onClick={handlePlanQuery} disabled={loading || !query.trim()}>
        {loading ? 'Planning...' : 'Plan SQL Query'}
      </button>

      {error && <div className="error-message">{error}</div>}

      {result && (
        <div className="sql-result">
          <h3>SQL Plan Result</h3>
          <div className="result-section">
            <label>Generated SQL:</label>
            <pre className="sql-code">{result.sql}</pre>
          </div>
          <div className="result-section">
            <label>Risk Level:</label>
            <span className={`risk-badge risk-${result.risk}`}>{result.risk}</span>
          </div>
          {result.targetConnector && (
            <div className="result-section">
              <label>Target Connector:</label>
              <span>{result.targetConnector}</span>
            </div>
          )}
          {result.estimatedCost && (
            <div className="result-section">
              <label>Estimated Cost:</label>
              <span>{result.estimatedCost}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SQLQueryTester;

