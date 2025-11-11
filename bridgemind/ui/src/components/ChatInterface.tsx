import React, { useState, useRef, useEffect } from 'react';
import { sendChatMessage, ChatMessage } from '../api/client';

interface ChatInterfaceProps {
  tenantId: string;
  connectors?: Array<{ connectorId: string; name: string }>;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ tenantId, connectors = [] }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: 'Hello! I\'m BridgeMind. Ask me questions about your data, and I\'ll help you find answers. Try asking: "What\'s our refund rate by month?" or "Show me customer analytics by country".' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [toolsAllowed, setToolsAllowed] = useState<string[]>(['retrieval', 'sql', 'api', 'web']);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await sendChatMessage({
        tenantId,
        messages: [...messages, userMessage],
        toolsAllowed,
      });

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.answer || 'No response received',
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Show SQL if available
      if (response.artifacts?.sql) {
        setMessages(prev => [...prev, {
          role: 'system',
          content: `SQL Query:\n\`\`\`sql\n${response.artifacts.sql}\n\`\`\``
        }]);
      }
    } catch (error: any) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.response?.data?.detail || error.message || 'Failed to get response'}`
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>Chat with BridgeMind</h2>
        <div className="tools-selector">
          <label>Tools:</label>
          {['retrieval', 'sql', 'api', 'web'].map(tool => (
            <label key={tool}>
              <input
                type="checkbox"
                checked={toolsAllowed.includes(tool)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setToolsAllowed([...toolsAllowed, tool]);
                  } else {
                    setToolsAllowed(toolsAllowed.filter(t => t !== tool));
                  }
                }}
              />
              {tool}
            </label>
          ))}
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-role">{msg.role === 'user' ? 'You' : msg.role === 'system' ? 'System' : 'BridgeMind'}</div>
            <div className="message-content">
              {msg.content.split('\n').map((line, i) => (
                <React.Fragment key={i}>
                  {line.startsWith('```') ? (
                    <pre className="code-block">{line.replace(/```sql\n?/g, '').replace(/```/g, '')}</pre>
                  ) : (
                    <p>{line}</p>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-role">BridgeMind</div>
            <div className="message-content">Thinking...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your data..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;

