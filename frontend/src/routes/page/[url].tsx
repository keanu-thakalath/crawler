import { createAsync, query, useParams } from "@solidjs/router";
import { Suspense, For, Show, createMemo } from "solid-js";
import { marked } from "marked";
import * as api from "~/api";

export default function PageDetail() {
  const params = useParams();
  const decodedUrl = decodeURIComponent(params.url);

  const getPageData = query(async () => {
    return await api.getPage(decodedUrl);
  }, "pageDetail");

  const page = createAsync(() => getPageData());

  // Find the latest scrape job result
  const scrapeResult = createMemo(() => {
    const pageData = page();
    if (!pageData) return null;

    const scrapeJobs = pageData.jobs.filter(
      (job) => job.outcome && "markdown" in job.outcome
    );

    if (scrapeJobs.length === 0) return null;

    const latestJob = scrapeJobs.sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )[0];

    return latestJob?.outcome as api.ScrapeJobResult | null;
  });

  // Find the latest extract job result
  const extractResult = createMemo(() => {
    const pageData = page();
    if (!pageData) return null;

    const extractJobs = pageData.jobs.filter(
      (job) =>
        job.outcome &&
        "summary" in job.outcome &&
        "relevant_internal_links" in job.outcome
    );

    if (extractJobs.length === 0) return null;

    const latestJob = extractJobs.sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )[0];

    return latestJob?.outcome as api.ExtractJobResult | null;
  });

  return (
    <Suspense
      fallback={<section aria-busy="true">Loading page details...</section>}
    >
      <Show when={page()}>
        <section>
          <h2>Page Details</h2>

          <div
            style={{
              "margin-bottom": "24px",
              padding: "16px",
              "border-radius": "8px",
            }}
          >
            <p style={{ margin: "0 0 8px 0" }}>
              <strong>Page URL:</strong>
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

          {/* Display Extract Job Information */}
          <Show when={extractResult()}>
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
                Page Analysis
              </h3>

              <div style={{ "margin-bottom": "16px" }}>
                <h4>Summary:</h4>
                <p style={{ "white-space": "pre-wrap", "line-height": "1.5" }}>
                  {extractResult()!.summary}
                </p>
              </div>

              <Show when={extractResult()!.key_facts}>
                <div style={{ "margin-bottom": "16px" }}>
                  <h4>Key Facts:</h4>
                  <p
                    style={{ "white-space": "pre-wrap", "line-height": "1.5" }}
                  >
                    {extractResult()!.key_facts}
                  </p>
                </div>
              </Show>

              <Show when={extractResult()!.key_quotes}>
                <div style={{ "margin-bottom": "16px" }}>
                  <h4>Key Quotes:</h4>
                  <p
                    style={{
                      "white-space": "pre-wrap",
                      "line-height": "1.5",
                      "font-style": "italic",
                    }}
                  >
                    {extractResult()!.key_quotes}
                  </p>
                </div>
              </Show>

              <Show when={extractResult()!.key_figures}>
                <div style={{ "margin-bottom": "16px" }}>
                  <h4>Key Figures:</h4>
                  <p
                    style={{ "white-space": "pre-wrap", "line-height": "1.5" }}
                  >
                    {extractResult()!.key_figures}
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
                  <strong>Trustworthiness:</strong>
                  <div
                    style={{
                      "margin-top": "4px",
                      padding: "4px 8px",
                      "border-radius": "4px",
                      "font-size": "0.9em",
                    }}
                  >
                    {extractResult()!.trustworthiness}
                  </div>
                </div>

                <div>
                  <strong>Relevancy:</strong>
                  <div
                    style={{
                      "margin-top": "4px",
                      padding: "4px 8px",
                      "background-color":
                        extractResult()!.relevancy === "High"
                          ? "#d1ecf1"
                          : extractResult()!.relevancy === "Medium"
                          ? "#fff3cd"
                          : extractResult()!.relevancy === "Low"
                          ? "#f8d7da"
                          : "#e2e3e5",
                      color:
                        extractResult()!.relevancy === "High"
                          ? "#0c5460"
                          : extractResult()!.relevancy === "Medium"
                          ? "#856404"
                          : extractResult()!.relevancy === "Low"
                          ? "#721c24"
                          : "#383d41",
                      "border-radius": "4px",
                      "font-size": "0.9em",
                    }}
                  >
                    {extractResult()!.relevancy}
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
                  {extractResult()!.review_status} •
                  <strong> Token Usage:</strong> Input:{" "}
                  {extractResult()!.input_tokens}, Output:{" "}
                  {extractResult()!.output_tokens} •<strong> Model:</strong>{" "}
                  {extractResult()!.model}
                </p>
              </div>
            </div>
          </Show>

          {/* Display Links */}
          <Show
            when={
              extractResult() &&
              ((extractResult()!.relevant_internal_links &&
                extractResult()!.relevant_internal_links.length > 0) ||
                (extractResult()!.relevant_external_links &&
                  extractResult()!.relevant_external_links.length > 0) ||
                (extractResult()!.relevant_file_links &&
                  extractResult()!.relevant_file_links.length > 0))
            }
          >
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
                Extracted Links
              </h3>

              <Show
                when={
                  extractResult()!.relevant_internal_links &&
                  extractResult()!.relevant_internal_links.length > 0
                }
              >
                <div style={{ "margin-bottom": "20px" }}>
                  <h4>
                    Internal Links (
                    {extractResult()!.relevant_internal_links.length}):
                  </h4>
                  <div
                    style={{
                      display: "flex",
                      "flex-direction": "column",
                      gap: "8px",
                    }}
                  >
                    <For each={extractResult()!.relevant_internal_links}>
                      {(link) => (
                        <a
                          href={link}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            color: "#4443cd",
                            "text-decoration": "none",
                            padding: "4px",
                            "border-radius": "4px",
                            "word-break": "break-all",
                            "font-size": "0.9em",
                          }}
                        >
                          {link}
                        </a>
                      )}
                    </For>
                  </div>
                </div>
              </Show>

              <Show
                when={
                  extractResult()!.relevant_external_links &&
                  extractResult()!.relevant_external_links.length > 0
                }
              >
                <div style={{ "margin-bottom": "20px" }}>
                  <h4>
                    External Links (
                    {extractResult()!.relevant_external_links.length}):
                  </h4>
                  <div
                    style={{
                      display: "flex",
                      "flex-direction": "column",
                      gap: "8px",
                    }}
                  >
                    <For each={extractResult()!.relevant_external_links}>
                      {(link) => (
                        <a
                          href={link}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            color: "#4443cd",
                            "text-decoration": "none",
                            padding: "4px",
                            "border-radius": "4px",
                            "word-break": "break-all",
                            "font-size": "0.9em",
                          }}
                        >
                          {link}
                        </a>
                      )}
                    </For>
                  </div>
                </div>
              </Show>

              <Show
                when={
                  extractResult()!.relevant_file_links &&
                  extractResult()!.relevant_file_links.length > 0
                }
              >
                <div>
                  <h4>
                    File Links ({extractResult()!.relevant_file_links.length}):
                  </h4>
                  <div
                    style={{
                      display: "flex",
                      "flex-direction": "column",
                      gap: "8px",
                    }}
                  >
                    <For each={extractResult()!.relevant_file_links}>
                      {(link) => (
                        <a
                          href={link}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            color: "#4443cd",
                            "text-decoration": "none",
                            padding: "8px",
                            "border-radius": "4px",
                            "word-break": "break-all",
                            "font-size": "0.9em",
                          }}
                        >
                          📁 {link}
                        </a>
                      )}
                    </For>
                  </div>
                </div>
              </Show>
            </div>
          </Show>

          {/* Display Jobs */}
          <Show when={page()!.jobs && page()!.jobs.length > 0}>
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
                Page Jobs ({page()!.jobs.length})
              </h3>

              <div
                style={{
                  display: "flex",
                  "flex-direction": "column",
                  gap: "8px",
                }}
              >
                <For each={page()!.jobs}>
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

          {/* Display Scraped Content */}
          <Show when={scrapeResult()?.markdown}>
            <div
              style={{
                padding: "20px",
                border: "1px solid #ddd",
                "border-radius": "8px",
                "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
              }}
            >
              <h3 style={{ "margin-top": "0", color: "#4443cd" }}>
                Scraped Content
              </h3>
              <article
                style={{
                  "line-height": "1.6",
                  "max-height": "500px",
                  "overflow-y": "auto",
                  padding: "16px",
                  "border-radius": "4px",
                }}
                innerHTML={marked.parse(scrapeResult()?.markdown || "", {
                  async: false,
                })}
              />
            </div>
          </Show>
        </section>
      </Show>
    </Suspense>
  );
}
