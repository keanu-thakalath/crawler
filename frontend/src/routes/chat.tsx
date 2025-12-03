import ChatComponent from "~/components/ChatComponent";

export default function Chat() {
  return (
    <section>
      <div style={{ "margin-bottom": "20px" }}>
        <h2 style={{ margin: "0 0 8px 0", color: "#333" }}>
          🤖 Chat with Your Sources
        </h2>
        <p
          style={{
            margin: "0",
            color: "#666",
            "line-height": "1.5",
            "font-size": "0.95em",
          }}
        >
          Ask questions about your crawled sources. I can help you explore the
          data, find specific information, and provide insights from your
          collected content.
        </p>
      </div>

      <div style={{ "max-width": "100%", margin: "0 auto" }}>
        <ChatComponent
          style={{
            "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
            "max-width": "1000px",
            margin: "0 auto",
          }}
        />
      </div>

      {/* Help section */}
      <div
        style={{
          "margin-top": "24px",
          padding: "16px",
          "background-color": "#f8f9fa",
          "border-radius": "8px",
          "border-left": "4px solid #4443cd",
        }}
      >
        <h3
          style={{
            margin: "0 0 12px 0",
            "font-size": "1em",
            color: "#4443cd",
          }}
        >
          💡 How to Use
        </h3>
        <ul
          style={{
            margin: "0",
            "padding-left": "20px",
            "line-height": "1.6",
            "font-size": "0.9em",
            color: "#555",
          }}
        >
          <li>
            <strong>List sources:</strong> "What sources do you have?" or "Show
            me all available sources"
          </li>
          <li>
            <strong>Explore content:</strong> "Tell me about [source URL]" or
            "What are the key facts from [source]?"
          </li>
          <li>
            <strong>Research questions:</strong> "What sources talk about
            environmental impacts?" or "Find sources with datasets"
          </li>
          <li>
            <strong>Compare sources:</strong> "Compare the findings from these
            sources..." or "What do multiple sources say about...?"
          </li>
        </ul>
      </div>

      {/* Features section */}
    </section>
  );
}
