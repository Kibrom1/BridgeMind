import React, { useState, useCallback } from 'react';
import './App.css';
import DatabaseConnectorForm from './components/DatabaseConnectorForm';
import ChatInterface from './components/ChatInterface';
import SQLQueryTester from './components/SQLQueryTester';
import ConnectorList from './components/ConnectorList';

function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'sql' | 'connectors'>('connectors');
  const [connectorRefreshKey, setConnectorRefreshKey] = useState(0);
  const tenantId = 'demo'; // Default tenant for MVP

  const handleConnectorCreated = useCallback(() => {
    // Trigger refresh of connector list
    setConnectorRefreshKey(prev => prev + 1);
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>BridgeMind</h1>
        <p>AI agent for unified data source querying</p>
      </header>

      <nav className="main-nav">
        <button
          className={activeTab === 'chat' ? 'active' : ''}
          onClick={() => setActiveTab('chat')}
        >
          💬 Chat
        </button>
        <button
          className={activeTab === 'sql' ? 'active' : ''}
          onClick={() => setActiveTab('sql')}
        >
          🔍 SQL Tester
        </button>
        <button
          className={activeTab === 'connectors' ? 'active' : ''}
          onClick={() => setActiveTab('connectors')}
        >
          🔌 Connectors
        </button>
      </nav>

      <main className="main-content">
        {activeTab === 'chat' && (
          <div className="tab-content">
            <ChatInterface tenantId={tenantId} />
          </div>
        )}

        {activeTab === 'sql' && (
          <div className="tab-content">
            <SQLQueryTester tenantId={tenantId} connectors={[]} />
          </div>
        )}

        {activeTab === 'connectors' && (
          <div className="tab-content connectors-tab">
            <div className="connectors-section">
              <DatabaseConnectorForm
                tenantId={tenantId}
                onSuccess={handleConnectorCreated}
              />
            </div>
            <div className="connectors-section">
              <ConnectorList key={connectorRefreshKey} tenantId={tenantId} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
