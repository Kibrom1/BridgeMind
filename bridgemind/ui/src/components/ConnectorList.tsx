import React, { useEffect, useState } from 'react';
import { listDatabaseConnectors, deleteDatabaseConnector } from '../api/client';

interface ConnectorListProps {
  tenantId: string;
  onConnectorSelect?: (connectorId: string) => void;
}

const ConnectorList: React.FC<ConnectorListProps> = ({ tenantId, onConnectorSelect }) => {
  const [connectors, setConnectors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  const loadConnectors = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await listDatabaseConnectors(tenantId);
      setConnectors(response.connectors || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load connectors');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (connectorId: string, connectorName: string) => {
    if (!window.confirm(`Are you sure you want to delete connector "${connectorName}"?`)) {
      return;
    }

    setDeleting(connectorId);
    setError(null);
    try {
      await deleteDatabaseConnector(connectorId);
      // Reload connectors after deletion
      await loadConnectors();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to delete connector');
    } finally {
      setDeleting(null);
    }
  };

  useEffect(() => {
    loadConnectors();
  }, [tenantId]);

  if (loading) return <div>Loading connectors...</div>;
  if (error) return <div className="error-message">Error: {error}</div>;

  return (
    <div className="connector-list">
      <div className="list-header">
        <h3>Database Connectors</h3>
        <button onClick={loadConnectors}>Refresh</button>
      </div>
      {connectors.length === 0 ? (
        <p className="empty-state">No connectors yet. Add one to get started!</p>
      ) : (
        <div className="connector-items">
          {connectors.map((connector) => (
            <div
              key={connector.connectorId}
              className="connector-item"
            >
              <div 
                className="connector-content"
                onClick={() => onConnectorSelect?.(connector.connectorId)}
              >
                <div className="connector-name">{connector.name}</div>
                <div className="connector-details">
                  <span className="connector-type">{connector.dbType}</span>
                  <span className={`connector-status status-${connector.status}`}>
                    {connector.status}
                  </span>
                </div>
                {connector.tablesCount && (
                  <div className="connector-meta">
                    {connector.tablesCount} tables
                  </div>
                )}
              </div>
              <button
                className="delete-button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete(connector.connectorId, connector.name);
                }}
                disabled={deleting === connector.connectorId}
                title="Delete connector"
              >
                {deleting === connector.connectorId ? 'Deleting...' : '🗑️'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ConnectorList;

