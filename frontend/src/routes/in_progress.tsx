import { createAsync, query } from "@solidjs/router";
import { For, Show, Suspense, createMemo } from "solid-js";
import * as api from "~/api";
import { usePolling } from "~/utils/polling";

const getInProgressSources = query(async () => {
  return await api.getInProgressSources();
}, "inProgressSources");

interface InProgressSourceData {
  url: string;
  jobCount: number;
  latestJobType: string;
  latestJobCreatedAt: string;
  hasError: boolean;
}

export default function InProgress() {
  const sources = createAsync(() => getInProgressSources());

  usePolling(getInProgressSources.key);

  // Extract job data from sources
  const inProgressData = createMemo(() => {
    const sourcesData = sources();
    if (!sourcesData) return [];

    return sourcesData.map((source): InProgressSourceData => {
      const jobs = source.jobs || [];
      const latestJob = jobs.sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )[0];

      // Determine job type from outcome type
      let jobType = "Unknown";
      let hasError = false;
      
      if (latestJob?.outcome) {
        if ("message" in latestJob.outcome) {
          jobType = "Error";
          hasError = true;
        } else if ("markdown" in latestJob.outcome) {
          jobType = "Scrape";
        } else if ("summary" in latestJob.outcome && "key_facts" in latestJob.outcome) {
          if ("data_origin" in latestJob.outcome) {
            jobType = "Summarize";
          } else {
            jobType = "Extract";
          }
        } else if ("pages_crawled" in latestJob.outcome) {
          jobType = "Crawl";
        }
      } else {
        jobType = "Pending";
      }

      return {
        url: source.url,
        jobCount: jobs.length,
        latestJobType: jobType,
        latestJobCreatedAt: latestJob?.created_at || "",
        hasError,
      };
    });
  });

  return (
    <section>
      <h2>In Progress Sources</h2>
      <p style={{ color: "#666", "margin-bottom": "20px" }}>
        Sources that have started crawling but haven't completed the full process yet.
      </p>

      <Suspense
        fallback={<div aria-busy="true">Loading in progress sources...</div>}
      >
        <Show
          when={inProgressData() && inProgressData().length > 0}
          fallback={
            <div
              style={{
                padding: "20px",
                "background-color": "#f8f9fa",
                "border-radius": "8px",
                "text-align": "center",
              }}
            >
              <p>⏳ No sources currently in progress!</p>
              <p style={{ color: "#666", "font-size": "0.9em" }}>
                All sources are either waiting to be crawled or have completed processing.
              </p>
            </div>
          }
        >
          <div
            style={{
              border: "1px solid #ddd",
              "border-radius": "8px",
              "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
              overflow: "hidden",
              "background-color": "#fff",
            }}
          >
            <For each={inProgressData()}>
              {(data, index) => (
                <div
                  style={{
                    padding: "16px",
                    "border-bottom":
                      index() < inProgressData().length - 1
                        ? "1px solid #eee"
                        : "none",
                    "background-color": data.hasError ? "#fff5f5" : "#fff",
                  }}
                >
                  <div style={{ "margin-bottom": "8px" }}>
                    <a
                      href={`/source/${encodeURIComponent(data.url)}`}
                      style={{
                        color: "#4443cd",
                        "text-decoration": "none",
                        "word-break": "break-all",
                        "font-weight": "500",
                        "font-size": "1.1em",
                      }}
                    >
                      {data.url}
                    </a>
                  </div>
                  
                  <div style={{ "margin-bottom": "8px" }}>
                    <a
                      href={data.url}
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
                      display: "flex",
                      "align-items": "center",
                      gap: "16px",
                      "flex-wrap": "wrap",
                      "font-size": "0.9em",
                    }}
                  >
                    <div style={{ display: "flex", "align-items": "center", gap: "4px" }}>
                      <span style={{ color: "#666" }}>Jobs:</span>
                      <span
                        style={{
                          "background-color": "#e9ecef",
                          padding: "2px 6px",
                          "border-radius": "3px",
                          "font-weight": "500",
                        }}
                      >
                        {data.jobCount}
                      </span>
                    </div>

                    <div style={{ display: "flex", "align-items": "center", gap: "4px" }}>
                      <span style={{ color: "#666" }}>Latest:</span>
                      <span
                        style={{
                          padding: "2px 6px",
                          "border-radius": "3px",
                          "font-weight": "500",
                          "background-color": data.hasError
                            ? "#f8d7da"
                            : data.latestJobType === "Pending"
                            ? "#fff3cd"
                            : "#d1ecf1",
                          color: data.hasError
                            ? "#721c24"
                            : data.latestJobType === "Pending"
                            ? "#856404"
                            : "#0c5460",
                        }}
                      >
                        {data.latestJobType}
                      </span>
                    </div>

                    <Show when={data.latestJobCreatedAt}>
                      <div style={{ color: "#666", "font-size": "0.85em" }}>
                        {new Date(data.latestJobCreatedAt).toLocaleString()}
                      </div>
                    </Show>
                  </div>
                </div>
              )}
            </For>
          </div>
        </Show>
      </Suspense>
    </section>
  );
}