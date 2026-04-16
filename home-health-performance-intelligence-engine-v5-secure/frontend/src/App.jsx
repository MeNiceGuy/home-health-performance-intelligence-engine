import "./App.css"

function App() {
  const openBackend = (path) => {
    window.open(`http://127.0.0.1:8000${path}`, "_blank")
  }

  return (
    <div className="app">
      <header className="hero">
        <h1>Home Health Performance Intelligence Engine</h1>
        <p>Performance, compliance, and operational risk insights for home health agencies.</p>
      </header>

      <main className="grid">
        <section className="card">
          <h2>Agency Intake</h2>
          <p>Open the secure intake form and submit a real report request.</p>
          <button onClick={() => openBackend("/")}>Start Intake</button>
        </section>

        <section className="card">
          <h2>Compliance Score</h2>
          <p>Open the live backend dashboard.</p>
          <button onClick={() => openBackend("/health")}>View Score</button>
        </section>

        <section className="card">
          <h2>Reports</h2>
          <p>Use the backend intake form to generate the report.</p>
          <button onClick={() => openBackend("/")}>Generate Report</button>
        </section>
      </main>
    </div>
  )
}

export default App
