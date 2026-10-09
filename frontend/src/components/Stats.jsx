const STATS = [
  { value: "20,000", label: "tickets ingested" },
  { value: "79", label: "topics discovered" },
  { value: "2", label: "languages" },
  { value: "97%", label: "retrieval precision" },
]

function Stats() {
  return (
    <section className="stats">
      <div className="stats-grid">
        {STATS.map((stat, index) => (
          <div key={index} className="stat">
            <div className="stat-value">{stat.value}</div>
            <div className="stat-label">{stat.label}</div>
          </div>
        ))}
      </div>
    </section>
  )
}

export default Stats
