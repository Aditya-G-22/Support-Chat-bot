const FEATURES = [
  {
    title: "Discovers topics with zero labels",
    desc: "Groups 20,000 messy tickets into 79 clear issue types, fully unsupervised. The structure comes straight out of the data.",
  },
  {
    title: "Ask in English, answer from German",
    desc: "It matches meaning across languages, not keywords, so a question in one language finds the fix written in another.",
  },
  {
    title: "Agentic RAG",
    desc: "It judges its own answer. If the retrieved context is weak, it searches again before replying.",
  },
  {
    title: "Grounded and scoped",
    desc: "Every answer comes from real past tickets. Ask it something off-topic and it declines instead of making things up.",
  },
  {
    title: "Hybrid retrieval",
    desc: "Semantic vector search combined with keyword search, then MMR reranking so results stay relevant and varied.",
  },
  {
    title: "Proven, not claimed",
    desc: "85% clustering agreement with the data's own labels, and 97% retrieval precision. Both measured, not guessed.",
  },
]

function Features() {
  return (
    <section className="features">
      <h2>Key features</h2>
      <div className="features-grid">
        {FEATURES.map((feature, index) => (
          <div key={index} className="feature-card">
            <h3>{feature.title}</h3>
            <p>{feature.desc}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

export default Features
