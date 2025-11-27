import { createAsync, query, useParams } from "@solidjs/router";
import { Suspense, For, Show, createMemo } from "solid-js";
import * as api from "~/api";

export default function SourceDetail() {
  const params = useParams();
  const decodedUrl = decodeURIComponent(params.url);

  const getSourceData = query(async () => {
    return await api.getSource(decodedUrl);
  }, "sourceDetail");

  const source = createAsync(() => getSourceData());

  // Find the latest summarize job result
  const summarizeResult = createMemo(() => {
    const sourceData = source();
    if (!sourceData) return null;

    const summarizeJobs = sourceData.jobs.filter(
      (job) => job.outcome && "data_origin" in job.outcome
    );

    if (summarizeJobs.length === 0) return null;

    // Get the most recent job
    const latestJob = summarizeJobs.sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )[0];

    return latestJob?.outcome as api.SummarizeJobResult | null;
  });

  return (
    <Suspense
      fallback={<section aria-busy="true">Loading source details...</section>}
    >
      <Show when={source()}>
        <section>
          <h2>Source Details</h2>

          <div
            style={{
              "margin-bottom": "24px",
              padding: "16px",
              "border-radius": "8px",
            }}
          >
            <p style={{ margin: "0 0 8px 0" }}>
              <strong>Source URL:</strong>
            </p>
            <a
              href={decodedUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                color: "#4443cd",
                "text-decoration": "none",
                "word-break": "break-all",
              }}
            >
              {decodedUrl}
            </a>
          </div>

          {/* Display Summarize Job Information */}
          <Show when={summarizeResult()}>
            <div
              style={{
                "margin-bottom": "24px",
                padding: "20px",
                border: "1px solid #ddd",
                "border-radius": "8px",
                "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
              }}
            >
              <h3 style={{ "margin-top": "0", color: "#4443cd" }}>
                Source Summary
              </h3>

              <div style={{ "margin-bottom": "16px" }}>
                <h4>Summary:</h4>
                <p style={{ "white-space": "pre-wrap", "line-height": "1.5" }}>
                  {summarizeResult()!.summary}
                </p>
              </div>

              <Show when={summarizeResult()!.key_facts}>
                <div style={{ "margin-bottom": "16px" }}>
                  <h4>Key Facts:</h4>
                  <p
                    style={{ "white-space": "pre-wrap", "line-height": "1.5" }}
                  >
                    {summarizeResult()!.key_facts}
                  </p>
                </div>
              </Show>

              <Show when={summarizeResult()!.key_quotes}>
                <div style={{ "margin-bottom": "16px" }}>
                  <h4>Key Quotes:</h4>
                  <p
                    style={{
                      "white-space": "pre-wrap",
                      "line-height": "1.5",
                      "font-style": "italic",
                    }}
                  >
                    {summarizeResult()!.key_quotes}
                  </p>
                </div>
              </Show>

              <Show when={summarizeResult()!.key_figures}>
                <div style={{ "margin-bottom": "16px" }}>
                  <h4>Key Figures:</h4>
                  <p
                    style={{ "white-space": "pre-wrap", "line-height": "1.5" }}
                  >
                    {summarizeResult()!.key_figures}
                  </p>
                </div>
              </Show>

              <div
                style={{
                  display: "grid",
                  "grid-template-columns":
                    "repeat(auto-fit, minmax(200px, 1fr))",
                  gap: "12px",
                  "margin-top": "20px",
                }}
              >
                <div>
                  <strong>Data Origin:</strong>
                  <div
                    style={{
                      "margin-top": "4px",
                      "border-radius": "4px",
                      "font-size": "0.9em",
                    }}
                  >
                    {summarizeResult()!.data_origin}
                  </div>
                </div>

                <div>
                  <strong>Source Format:</strong>
                  <div
                    style={{
                      "margin-top": "4px",
                      "border-radius": "4px",
                      "font-size": "0.9em",
                    }}
                  >
                    {summarizeResult()!.source_format}
                  </div>
                </div>

                <div>
                  <strong>Focus Area:</strong>
                  <div
                    style={{
                      "margin-top": "4px",
                      "border-radius": "4px",
                      "font-size": "0.9em",
                    }}
                  >
                    {summarizeResult()!.focus_area}
                  </div>
                </div>

                <div>
                  <strong>Dataset Presence:</strong>
                  <div
                    style={{
                      "margin-top": "4px",
                      padding: "4px 8px",
                      "background-color":
                        summarizeResult()!.dataset_presence === "Present"
                          ? "#d4edda"
                          : "#f8d7da",
                      color:
                        summarizeResult()!.dataset_presence === "Present"
                          ? "#155724"
                          : "#721c24",
                      "border-radius": "4px",
                      "font-size": "0.9em",
                    }}
                  >
                    {summarizeResult()!.dataset_presence}
                  </div>
                </div>
              </div>

              <div
                style={{
                  "margin-top": "16px",
                  "padding-top": "16px",
                  "border-top": "1px solid #eee",
                }}
              >
                <p style={{ color: "#666", "font-size": "0.9em", margin: "0" }}>
                  <strong>Review Status:</strong>{" "}
                  {summarizeResult()!.review_status} •
                  <strong> Token Usage:</strong> Input:{" "}
                  {summarizeResult()!.input_tokens}, Output:{" "}
                  {summarizeResult()!.output_tokens} •<strong> Model:</strong>{" "}
                  {summarizeResult()!.model}
                </p>
              </div>
            </div>
          </Show>

          {/* Display Pages */}
          <Show when={source()!.pages && source()!.pages.length > 0}>
            <div
              style={{
                "margin-bottom": "24px",
                padding: "20px",
                border: "1px solid #ddd",
                "border-radius": "8px",
                "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
              }}
            >
              <h3 style={{ "margin-top": "0", color: "#4443cd" }}>
                Pages ({source()!.pages.length})
              </h3>

              <div
                style={{
                  display: "flex",
                  "flex-direction": "column",
                  gap: "12px",
                }}
              >
                <For each={source()!.pages}>
                  {(page) => (
                    <div
                      style={{
                        padding: "12px",
                        "border-radius": "6px",
                        border: "1px solid #e9ecef",
                      }}
                    >
                      <div style={{ "margin-bottom": "8px" }}>
                        <a
                          href={`/page/${encodeURIComponent(page.url)}`}
                          style={{
                            color: "#4443cd",
                            "text-decoration": "none",
                            "word-break": "break-all",
                            "font-weight": "500",
                          }}
                        >
                          {page.url}
                        </a>
                      </div>
                      <div style={{ "margin-bottom": "8px" }}>
                        <a
                          href={page.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            color: "#666",
                            "text-decoration": "none",
                            "font-size": "0.8em",
                          }}
                        >
                          🔗 Visit Original
                        </a>
                      </div>

                      <div
                        style={{
                          "font-size": "0.85em",
                          color: "#666",
                          display: "flex",
                          "align-items": "center",
                          gap: "16px",
                        }}
                      >
                        <span>
                          <strong>Jobs:</strong> {page.jobs.length}
                        </span>
                        <span>
                          <strong>Status:</strong>{" "}
                          {page.jobs.every((job) => job.outcome) ? (
                            <span style={{ color: "#28a745" }}>Complete</span>
                          ) : (
                            <span style={{ color: "#ffc107" }}>Processing</span>
                          )}
                        </span>
                      </div>
                    </div>
                  )}
                </For>
              </div>
            </div>
          </Show>

          {/* Display Source Jobs */}
          <Show when={source()!.jobs && source()!.jobs.length > 0}>
            <div
              style={{
                padding: "20px",
                border: "1px solid #ddd",
                "border-radius": "8px",
                "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
              }}
            >
              <h3 style={{ "margin-top": "0", color: "#4443cd" }}>
                Source Jobs ({source()!.jobs.length})
              </h3>

              <div
                style={{
                  display: "flex",
                  "flex-direction": "column",
                  gap: "8px",
                }}
              >
                <For each={source()!.jobs}>
                  {(job) => (
                    <div
                      style={{
                        padding: "8px 12px",
                        "border-radius": "4px",
                        "font-size": "0.9em",
                      }}
                    >
                      <span
                        style={{ "font-family": "monospace", color: "#666" }}
                      >
                        {job.job_id}
                      </span>
                      <span style={{ "margin-left": "12px" }}>
                        {job.outcome ? (
                          <span style={{ color: "#28a745" }}>✓ Complete</span>
                        ) : (
                          <span style={{ color: "#ffc107" }}>
                            ⏳ Processing
                          </span>
                        )}
                      </span>
                      <span style={{ "margin-left": "12px", color: "#666" }}>
                        {new Date(job.created_at).toLocaleString()}
                      </span>
                    </div>
                  )}
                </For>
              </div>
            </div>
          </Show>
        </section>
      </Show>
    </Suspense>
  );
}
