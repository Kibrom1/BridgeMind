import React, { useState } from 'react';
import { createDatabaseConnector, DatabaseConnector } from '../api/client';

interface DatabaseConnectorFormProps {
  tenantId: string;
  onSuccess?: () => void;
}

const DatabaseConnectorForm: React.FC<DatabaseConnectorFormProps> = ({ tenantId, onSuccess }) => {
  const [formData, setFormData] = useState<DatabaseConnector>({
    tenantId,
    name: '',
    description: '',
    dbType: 'postgresql',
    connectionString: '',
    readOnly: true,
    maxRowsPerQuery: 100,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const result = await createDatabaseConnector(formData);
      setSuccess(true);
      console.log('Connector created:', result);
      // Reset form after a short delay to show success message
      setTimeout(() => {
        setFormData({
          tenantId,
          name: '',
          description: '',
          dbType: 'postgresql',
          connectionString: '',
          readOnly: true,
          maxRowsPerQuery: 100,
        });
        setSuccess(false);
      }, 3000);
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create connector');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="connector-form">
      <h2>Add Database Connector</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Name *</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
            placeholder="e.g., Analytics DB"
          />
        </div>

        <div className="form-group">
          <label>Description</label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Database description"
            rows={2}
          />
        </div>

        <div className="form-group">
          <label>Database Type *</label>
          <select
            value={formData.dbType}
            onChange={(e) => setFormData({ ...formData, dbType: e.target.value })}
            required
          >
            <option value="postgresql">PostgreSQL</option>
            <option value="mysql">MySQL</option>
            <option value="sqlite">SQLite</option>
            <option value="mssql">Microsoft SQL Server</option>
            <option value="snowflake">Snowflake</option>
            <option value="bigquery">BigQuery</option>
          </select>
        </div>

        <div className="form-group">
          <label>Connection String *</label>
          <input
            type="text"
            value={formData.connectionString}
            onChange={(e) => setFormData({ ...formData, connectionString: e.target.value })}
            required
            placeholder="postgresql://user:pass@host:port/dbname"
          />
          <small>Example: postgresql://bridgemind:bridgemind_dev@localhost:5433/bridgemind</small>
        </div>

        <div className="form-group">
          <label>
            <input
              type="checkbox"
              checked={formData.readOnly}
              onChange={(e) => setFormData({ ...formData, readOnly: e.target.checked })}
            />
            Read Only
          </label>
        </div>

        <div className="form-group">
          <label>Max Rows Per Query</label>
          <input
            type="number"
            value={formData.maxRowsPerQuery}
            onChange={(e) => setFormData({ ...formData, maxRowsPerQuery: parseInt(e.target.value) })}
            min="1"
            max="10000"
          />
        </div>

        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">✅ Connector created successfully!</div>}

        <button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create Connector'}
        </button>
      </form>
    </div>
  );
};

export default DatabaseConnectorForm;

