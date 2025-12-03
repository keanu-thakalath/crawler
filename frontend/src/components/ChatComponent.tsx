import { createSignal, createEffect, onCleanup, For, Show } from "solid-js";
import { createAsync } from "@solidjs/router";
import { getAuthToken } from "~/utils/auth";
import { createChatStream, type ChatMessage } from "~/utils/chatStream";
import { marked } from "marked";

interface ChatComponentProps {
  class?: string;
  style?: Record<string, string>;
}

export default function ChatComponent(props: ChatComponentProps) {
  const [messages, setMessages] = createSignal<ChatMessage[]>([]);
  const [inputValue, setInputValue] = createSignal("");
  const [isStreaming, setIsStreaming] = createSignal(false);
  const [currentStreamContent, setCurrentStreamContent] = createSignal("");
  const [error, setError] = createSignal("");

  const authToken = createAsync(() => getAuthToken());

  // Configure marked for better security and styling
  marked.setOptions({
    breaks: true,
    gfm: true,
  });

  let messagesContainer: HTMLDivElement | undefined;
  let streamCleanup: (() => void) | undefined;

  // Auto-scroll to bottom when new messages arrive
  createEffect(() => {
    if (
      messagesContainer &&
      (messages().length > 0 || currentStreamContent())
    ) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  });

  // Cleanup on unmount
  onCleanup(() => {
    if (streamCleanup) {
      streamCleanup();
    }
  });

  const sendMessage = async (e: Event) => {
    e.preventDefault();

    const content = inputValue().trim();
    const token = authToken();

    if (!content || isStreaming() || !token) {
      return;
    }

    setError("");
    setInputValue("");

    // Add user message
    const userMessage: ChatMessage = { role: "user", content };
    const newMessages = [...messages(), userMessage];
    setMessages(newMessages);

    setIsStreaming(true);
    setCurrentStreamContent("");

    try {
      streamCleanup = await createChatStream(
        newMessages,
        token,
        (content: string) => {
          // Append new content to the streaming response
          setCurrentStreamContent((prev) => prev + content);
        },
        () => {
          // Stream complete - add assistant message and reset streaming state
          // Clean up carriage returns and normalize line endings
          const cleanContent = currentStreamContent();
          const assistantMessage: ChatMessage = {
            role: "assistant",
            content: cleanContent,
          };
          setMessages((prev) => [...prev, assistantMessage]);
          setCurrentStreamContent("");
          setIsStreaming(false);
          streamCleanup = undefined;
        },
        (error: string) => {
          // Handle error
          setError(error);
          setIsStreaming(false);
          setCurrentStreamContent("");
          streamCleanup = undefined;
        }
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setIsStreaming(false);
      setCurrentStreamContent("");
    }
  };

  const clearChat = () => {
    if (streamCleanup) {
      streamCleanup();
      streamCleanup = undefined;
    }
    setMessages([]);
    setCurrentStreamContent("");
    setIsStreaming(false);
    setError("");
  };

  const formatMessage = (content: string) => {
    // Display as plain text with preserved whitespace
    return (
      <div style={{ "line-height": "1.6", "white-space": "pre-wrap" }}>
        {content}
      </div>
    );
  };

  return (
    <div
      class={props.class}
      style={{
        display: "flex",
        "flex-direction": "column",
        height: "600px",
        border: "1px solid #ddd",
        "border-radius": "8px",
        overflow: "hidden",
        "background-color": "#fff",
        ...props.style,
      }}
    >
      {/* Chat header */}
      <div
        style={{
          padding: "12px 16px",
          "background-color": "#4443cd",
          color: "white",
          "border-bottom": "1px solid #ddd",
          display: "flex",
          "justify-content": "space-between",
          "align-items": "center",
        }}
      >
        <h3 style={{ margin: "0", "font-size": "1.1em" }}>
          🤖 Source Explorer Chat
        </h3>
        <button
          onClick={clearChat}
          disabled={isStreaming()}
          style={{
            padding: "6px 12px",
            "background-color": "rgba(255, 255, 255, 0.2)",
            color: "white",
            border: "1px solid rgba(255, 255, 255, 0.3)",
            "border-radius": "4px",
            cursor: isStreaming() ? "not-allowed" : "pointer",
            "font-size": "0.9em",
            opacity: isStreaming() ? "0.5" : "1",
          }}
        >
          Clear Chat
        </button>
      </div>

      {/* Messages container */}
      <div
        ref={messagesContainer}
        style={{
          flex: "1",
          padding: "16px",
          "overflow-y": "auto",
          "background-color": "#f8f9fa",
        }}
      >
        <Show
          when={messages().length > 0 || isStreaming()}
          fallback={
            <div
              style={{
                "text-align": "center",
                color: "#666",
                padding: "40px 20px",
                "line-height": "1.5",
              }}
            >
              <div style={{ "font-size": "2em", "margin-bottom": "16px" }}>
                💬
              </div>
              <p style={{ margin: "0 0 8px 0", "font-weight": "500" }}>
                Welcome to Source Explorer Chat!
              </p>
              <p style={{ margin: "0", "font-size": "0.9em" }}>
                Ask me about your crawled sources. I can help you list available
                sources, explore their content, and answer questions about the
                data.
              </p>
            </div>
          }
        >
          <For each={messages()}>
            {(message) => (
              <div
                style={{
                  "margin-bottom": "16px",
                  display: "flex",
                  "justify-content":
                    message.role === "user" ? "flex-end" : "flex-start",
                }}
              >
                <div
                  style={{
                    "max-width": "70%",
                    padding: "12px 16px",
                    "border-radius":
                      message.role === "user"
                        ? "18px 18px 4px 18px"
                        : "18px 18px 18px 4px",
                    "background-color":
                      message.role === "user" ? "#4443cd" : "#fff",
                    color: message.role === "user" ? "white" : "#333",
                    "box-shadow": "0 1px 3px rgba(0, 0, 0, 0.1)",
                    border:
                      message.role === "assistant"
                        ? "1px solid #e0e0e0"
                        : "none",
                  }}
                >
                  <div style={{ "font-size": "0.9em", "line-height": "1.4" }}>
                    {formatMessage(message.content)}
                  </div>
                </div>
              </div>
            )}
          </For>

          {/* Streaming message */}
          <Show when={isStreaming()}>
            <div
              style={{
                "margin-bottom": "16px",
                display: "flex",
                "justify-content": "flex-start",
              }}
            >
              <div
                style={{
                  "max-width": "70%",
                  padding: "12px 16px",
                  "border-radius": "18px 18px 18px 4px",
                  "background-color": "#fff",
                  color: "#333",
                  "box-shadow": "0 1px 3px rgba(0, 0, 0, 0.1)",
                  border: "1px solid #e0e0e0",
                  position: "relative",
                }}
              >
                <div style={{ "font-size": "0.9em", "line-height": "1.4" }}>
                  {/* Use plain text for streaming, markdown only when complete */}
                  <div
                    style={{ "line-height": "1.6", "white-space": "pre-wrap" }}
                  >
                    {currentStreamContent()}
                  </div>
                  <span
                    style={{
                      display: "inline-block",
                      width: "8px",
                      height: "12px",
                      "background-color": "#4443cd",
                      "margin-left": "2px",
                      animation: "blink 1s infinite",
                    }}
                  />
                </div>
              </div>
            </div>
          </Show>
        </Show>

        {/* Error message */}
        <Show when={error()}>
          <div
            style={{
              "margin-bottom": "16px",
              padding: "12px 16px",
              "background-color": "#f8d7da",
              color: "#721c24",
              "border-radius": "8px",
              border: "1px solid #f5c6cb",
            }}
          >
            <strong>Error:</strong> {error()}
          </div>
        </Show>
      </div>

      {/* Input form */}
      <form
        onSubmit={sendMessage}
        style={{
          padding: "16px",
          "border-top": "1px solid #ddd",
          "background-color": "#fff",
        }}
      >
        <div style={{ display: "flex-row", gap: "8px" }}>
          <input
            type="text"
            value={inputValue()}
            onInput={(e) => setInputValue(e.currentTarget.value)}
            placeholder="Ask about your sources..."
            disabled={isStreaming()}
            style={{
              flex: "1",
              padding: "12px",
              border: "1px solid #ddd",
              "border-radius": "20px",
              "font-size": "0.9em",
              outline: "none",
              opacity: isStreaming() ? "0.5" : "1",
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = "#4443cd";
              e.currentTarget.style.boxShadow =
                "0 0 0 2px rgba(68, 67, 205, 0.2)";
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = "#ddd";
              e.currentTarget.style.boxShadow = "none";
            }}
          />
          <button
            type="submit"
            disabled={!inputValue().trim() || isStreaming()}
            style={{
              padding: "12px 20px",
              "background-color": "#4443cd",
              color: "white",
              border: "none",
              "border-radius": "20px",
              cursor:
                !inputValue().trim() || isStreaming()
                  ? "not-allowed"
                  : "pointer",
              "font-size": "0.9em",
              opacity: !inputValue().trim() || isStreaming() ? "0.5" : "1",
              "white-space": "nowrap",
            }}
          >
            {isStreaming() ? "..." : "Send"}
          </button>
        </div>
      </form>

      {/* Add styles for cursor animation and markdown content */}
      <style>
        {`
          @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
          }
          
          .markdown-content {
            font-family: inherit;
          }
          
          .markdown-content h1,
          .markdown-content h2,
          .markdown-content h3,
          .markdown-content h4,
          .markdown-content h5,
          .markdown-content h6 {
            margin: 16px 0 8px 0;
            font-weight: 600;
            line-height: 1.3;
          }
          
          .markdown-content h1 { font-size: 1.4em; }
          .markdown-content h2 { font-size: 1.3em; }
          .markdown-content h3 { font-size: 1.2em; }
          .markdown-content h4 { font-size: 1.1em; }
          .markdown-content h5 { font-size: 1.05em; }
          .markdown-content h6 { font-size: 1em; }
          
          .markdown-content p {
            margin: 8px 0;
            line-height: 1.6;
          }
          
          .markdown-content ul,
          .markdown-content ol {
            margin: 8px 0;
            padding-left: 20px;
          }
          
          .markdown-content li {
            margin: 4px 0;
            line-height: 1.5;
          }
          
          .markdown-content strong {
            font-weight: 600;
          }
          
          .markdown-content em {
            font-style: italic;
          }
          
          .markdown-content code {
            background-color: rgba(68, 67, 205, 0.1);
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
          }
          
          .markdown-content pre {
            background-color: #f8f9fa;
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 8px 0;
            border: 1px solid #e0e0e0;
          }
          
          .markdown-content pre code {
            background-color: transparent;
            padding: 0;
          }
          
          .markdown-content blockquote {
            border-left: 3px solid #4443cd;
            margin: 8px 0;
            padding-left: 12px;
            color: #666;
            font-style: italic;
          }
          
          .markdown-content a {
            color: #4443cd;
            text-decoration: none;
          }
          
          .markdown-content a:hover {
            text-decoration: underline;
          }
          
          .markdown-content table {
            border-collapse: collapse;
            width: 100%;
            margin: 8px 0;
          }
          
          .markdown-content th,
          .markdown-content td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
          }
          
          .markdown-content th {
            background-color: #f8f9fa;
            font-weight: 600;
          }
        `}
      </style>
    </div>
  );
}
