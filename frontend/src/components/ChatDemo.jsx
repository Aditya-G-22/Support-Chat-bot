import { useState } from 'react'

const API_URL = 'http://127.0.0.1:8000/chat'

function ConfidenceRing({ score }) {
  const pct = Math.round(score * 100)
  const radius = 44
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (pct / 100) * circumference

  return (
    <svg className="ring" width="120" height="120" viewBox="0 0 120 120">
      <circle className="ring-track" cx="60" cy="60" r={radius} />
      <circle
        className="ring-fill"
        cx="60"
        cy="60"
        r={radius}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
      />
      <text x="60" y="60" className="ring-text">{pct}%</text>
    </svg>
  )
}

function ChatDemo() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [info, setInfo] = useState(null)

  async function handleSend() {
    if (input.trim() === '' || loading) return

    const question = input
    setMessages((prev) => [...prev, { role: 'user', text: question }])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question }),
      })
      const data = await response.json()
      setMessages((prev) => [...prev, { role: 'bot', text: data.answer }])
      setInfo({ topic: data.matched_topic, sources: data.sources })
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: 'bot', text: 'Something went wrong. Is the backend running?' },
      ])
    } finally {
      setLoading(false)
    }
  }

  const queues =
    info && info.sources ? [...new Set(info.sources.map((s) => s.queue))] : []

  return (
    <section className="demo" id="demo">
      <h2>Demo</h2>
      <div className="demo-body">
        <div className="chat">
          <div className="messages">
            {messages.length === 0 && (
              <div className="empty">Ask a support question to get started.</div>
            )}
            {messages.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                {message.text}
              </div>
            ))}
            {loading && <div className="message bot">Thinking...</div>}
          </div>

          <div className="input-row">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask a question..."
            />
            <button onClick={handleSend} disabled={loading}>
              Send
            </button>
          </div>
        </div>

        <div className="topic-panel">
          <h3 className="panel-title">Under the hood</h3>

          {!info ? (
            <div className="panel-empty">
              Ask a question to see which topic the bot matches and the tickets
              it used.
            </div>
          ) : (
            <div className="panel-content">
              {info.topic ? (
                <>
                  <div className="topic-badge">{info.topic.label}</div>
                  <ConfidenceRing score={info.topic.score} />
                  <div className="panel-caption">topic match confidence</div>
                </>
              ) : (
                <div className="panel-empty">
                  No strong topic match for this one.
                </div>
              )}

              {queues.length > 0 && (
                <div className="sources-section">
                  <div className="sources-title">Tickets used</div>
                  <div className="source-chips">
                    {queues.map((queue, i) => (
                      <span key={i} className="source-chip">{queue}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

export default ChatDemo
