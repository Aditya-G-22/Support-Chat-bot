const COLUMNS = ["subject", "body", "answer", "queue", "type", "language"]

const ROWS = [
  {
    subject: "Unvorhergesehener Absturz der Datenanalyse-Plattform",
    body: "Die Datenanalyse-Plattform brach unerwartet ab, da die Speicheroberfläche zu gering war. Ich habe versucht, Laravel 8 neu zu starten.",
    answer: "Ich werde Ihnen bei der Lösung des Problems helfen, indem die Plattform neu gestartet wird. Bitte bereiten Sie Ihre Speichereinstellungen vor.",
    queue: "General Inquiry",
    type: "Incident",
    language: "de",
  },
  {
    subject: "Login Issue Possibly Linked to Caching",
    body: "I can't log in after the latest update. It could be due to an outdated browser version.",
    answer: "Please try a different browser, clear your cookies, and share the exact error message so we can look into it.",
    queue: "IT Support",
    type: "Incident",
    language: "en",
  },
  {
    subject: "Problem with Invoice",
    body: "Unexpected charges appeared on my recent invoice for a subscription I did not use.",
    answer: "Please share your account number and invoice number so we can investigate the billing issue.",
    queue: "Billing and Payments",
    type: "Problem",
    language: "en",
  },
  {
    subject: "Netzwerkverbindung fiel während der Datenanalyse aus",
    body: "Seit dem letzten Update habe ich wiederholt Probleme mit der Netzwerkverbindung bei der Datenanalyse.",
    answer: "Vielen Dank für Ihre Nachricht. Bitte teilen Sie uns das Modell Ihres Routers und die Firmware-Version mit.",
    queue: "Technical Support",
    type: "Incident",
    language: "de",
  },
  {
    subject: "Campaign metrics not updating",
    body: "The campaign metrics are not updating or appear inaccurate on the dashboard.",
    answer: "We will investigate the issue. Could you share your account and integration details?",
    queue: "Product Support",
    type: "Problem",
    language: "en",
  },
]

function Dataset() {
  return (
    <section className="dataset">
      <h2>Dataset used</h2>
      <div className="dataset-body">
        <div className="csv-preview">
          <table className="csv-table">
            <thead>
              <tr>
                {COLUMNS.map((col) => (
                  <th key={col}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ROWS.map((row, index) => (
                <tr key={index}>
                  {COLUMNS.map((col) => (
                    <td key={col}>{row[col]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="dataset-desc">
          <p>
            Around 20,000 customer support tickets in English and German, from
            the Customer IT Support dataset on Kaggle. Each row is a customer
            problem, an agent reply, and a few labels.
          </p>
          <p>
            The tickets are messy on purpose. The text has HTML in it, private
            details are masked a dozen different ways, and there is no clean
            structure. That mess is the point. The bot has to find the structure
            itself.
          </p>
        </div>
      </div>
    </section>
  )
}

export default Dataset
