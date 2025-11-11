import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>BridgeMind</h1>
        <p>AI agent for unified data source querying</p>
        <p className="status">🚧 Under Development</p>
      </header>
      <main>
        <div className="container">
          <h2>Welcome to BridgeMind</h2>
          <p>This is the initial UI scaffold. Implementation in progress.</p>
          <div className="features">
            <div className="feature">
              <h3>📊 Multiple Databases</h3>
              <p>Connect to multiple database sources</p>
            </div>
            <div className="feature">
              <h3>🔌 API Integration</h3>
              <p>Add OpenAPI connectors as tools</p>
            </div>
            <div className="feature">
              <h3>📄 Document Sources</h3>
              <p>Index and search documents</p>
            </div>
            <div className="feature">
              <h3>🌐 Web Data</h3>
              <p>Access real-time web data</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;

