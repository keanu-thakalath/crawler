"use client";

export interface ChatMessage {
  role: string;
  content: string;
  function_call?: Record<string, any>;
  tool_calls?: Record<string, any>[];
}

// For client-side, we need to get the BASE_URL differently
// In development, it's likely the same origin with a different port
const BASE_URL = import.meta.env.VITE_BACKEND_URL;

// Client-side chat streaming function
export function createChatStream(
  messages: ChatMessage[],
  authToken: string,
  onMessage: (content: string) => void,
  onComplete: () => void,
  onError: (error: string) => void
): Promise<() => void> {
  return new Promise(async (resolve) => {
    try {
      const response = await fetch(`${BASE_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({ messages }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        onError(`HTTP ${response.status}: ${errorText}`);
        resolve(() => {});
        return;
      }

      if (!response.body) {
        onError("No response body received");
        resolve(() => {});
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let isActive = true;

      const cleanup = () => {
        isActive = false;
        reader.cancel();
      };

      resolve(cleanup);

      // Process the stream
      try {
        let currentEvent = "";
        let dataCounter = 0;

        while (isActive) {
          const { done, value } = await reader.read();

          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          console.log(buffer);
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // Keep the last incomplete line

          for (const line of lines) {
            if (!line.trim()) {
              // Empty line indicates end of SSE message
              currentEvent = "";
              continue;
            }

            if (line.startsWith("event: ")) {
              currentEvent = line.slice(7).trim();
              dataCounter = 0;
            } else if (line.startsWith("data: ")) {
              dataCounter++;
              const data = line.slice(6);

              if (currentEvent === "complete") {
                onComplete();
                cleanup();
                return;
              } else if (currentEvent === "error") {
                onError(data);
                cleanup();
                return;
              } else if (currentEvent === "message" || !currentEvent) {
                // Handle message data - add all data, even if it's just a space
                onMessage(dataCounter >= 2 ? `\n${data}` : data);
              }
            }
          }
        }
      } catch (error) {
        if (isActive) {
          onError(error instanceof Error ? error.message : String(error));
        }
      } finally {
        cleanup();
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : String(error));
      resolve(() => {});
    }
  });
}
