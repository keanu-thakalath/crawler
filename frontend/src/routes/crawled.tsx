import { createAsync, query } from "@solidjs/router";
import { For, Show, Suspense, createMemo } from "solid-js";
import * as api from "~/api";
import { usePolling } from "~/utils/polling";

const getCrawledSources = query(async () => {
  return await api.getCrawledSources();
}, "crawledSources");

interface CrawledSourceData {
  url: string;
  dataOrigin: string;
  sourceFormat: string;
  focusArea: string;
  datasetPresence: string;
  summary?: string;
}

export default function Crawled() {
  const sources = createAsync(() => getCrawledSources());

  usePolling(getCrawledSources.key);

  // Extract summarize job data from sources
  const crawledData = createMemo(() => {
    const sourcesData = sources();
    if (!sourcesData) return [];

    return sourcesData.map((source): CrawledSourceData => {
      // Find the latest approved SummarizeJobResult
      const summarizeJob = source.jobs
        .filter((job) => job.outcome && "data_origin" in job.outcome)
        .sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )[0];

      if (summarizeJob?.outcome) {
        const outcome = summarizeJob.outcome as api.SummarizeJobResult;
        return {
          url: source.url,
          dataOrigin: outcome.data_origin || "N/A",
          sourceFormat: outcome.source_format || "N/A",
          focusArea: outcome.focus_area || "N/A",
          datasetPresence: outcome.dataset_presence || "N/A",
          summary: outcome.summary,
        };
      }

      return {
        url: source.url,
        dataOrigin: "N/A",
        sourceFormat: "N/A",
        focusArea: "N/A",
        datasetPresence: "N/A",
      };
    });
  });

  return (
    <section>
      <h2>Crawled Sources</h2>
      <p style={{ color: "#666", "margin-bottom": "20px" }}>
        Sources that have been successfully crawled and summarized with approved
        results.
      </p>

      <Suspense
        fallback={<div aria-busy="true">Loading crawled sources...</div>}
      >
        <Show
          when={crawledData() && crawledData().length > 0}
          fallback={
            <div
              style={{
                padding: "20px",
                "background-color": "#f8f9fa",
                "border-radius": "8px",
                "text-align": "center",
              }}
            >
              <p>📋 No crawled sources found!</p>
              <p style={{ color: "#666", "font-size": "0.9em" }}>
                No sources have completed the full crawl and summarization
                process yet.
              </p>
            </div>
          }
        >
          <div style={{ "overflow-x": "auto" }}>
            <table
              style={{
                width: "100%",
                "border-collapse": "collapse",
                "background-color": "#fff",
                "border-radius": "8px",
                overflow: "hidden",
                "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
              }}
            >
              <thead>
                <tr style={{ "background-color": "#4443cd", color: "white" }}>
                  <th
                    style={{
                      padding: "12px",
                      "text-align": "left",
                      "font-weight": "600",
                    }}
                  >
                    Source URL
                  </th>
                  <th
                    style={{
                      padding: "12px",
                      "text-align": "left",
                      "font-weight": "600",
                    }}
                  >
                    Data Origin
                  </th>
                  <th
                    style={{
                      padding: "12px",
                      "text-align": "left",
                      "font-weight": "600",
                    }}
                  >
                    Source Format
                  </th>
                  <th
                    style={{
                      padding: "12px",
                      "text-align": "left",
                      "font-weight": "600",
                    }}
                  >
                    Focus Area
                  </th>
                  <th
                    style={{
                      padding: "12px",
                      "text-align": "left",
                      "font-weight": "600",
                    }}
                  >
                    Dataset Presence
                  </th>
                </tr>
              </thead>
              <tbody>
                <For each={crawledData()}>
                  {(data, index) => (
                    <tr
                      style={{
                        "border-bottom":
                          index() < crawledData().length - 1
                            ? "1px solid #eee"
                            : "none",
                        "background-color":
                          index() % 2 === 0 ? "#f8f9fa" : "#fff",
                      }}
                    >
                      <td style={{ padding: "12px", "vertical-align": "top" }}>
                        <div style={{ "margin-bottom": "8px" }}>
                          <a
                            href={`/source/${encodeURIComponent(data.url)}`}
                            style={{
                              color: "#4443cd",
                              "text-decoration": "none",
                              "word-break": "break-all",
                              "font-weight": "500",
                            }}
                          >
                            {data.url}
                          </a>
                        </div>
                        <div>
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
                        <Show when={data.summary}>
                          <div
                            style={{
                              "margin-top": "4px",
                              "font-size": "0.85em",
                              color: "#666",
                              "line-height": "1.3",
                              "max-width": "300px",
                            }}
                            title={data.summary}
                          >
                            {data.summary!.length > 100
                              ? `${data.summary!.substring(0, 100)}...`
                              : data.summary}
                          </div>
                        </Show>
                      </td>
                      <td style={{ padding: "12px", "vertical-align": "top" }}>
                        <span
                          style={{
                            "border-radius": "4px",
                            "font-size": "0.9em",
                          }}
                        >
                          {data.dataOrigin}
                        </span>
                      </td>
                      <td style={{ padding: "12px", "vertical-align": "top" }}>
                        <span
                          style={{
                            "border-radius": "4px",
                            "font-size": "0.9em",
                          }}
                        >
                          {data.sourceFormat}
                        </span>
                      </td>
                      <td style={{ padding: "12px", "vertical-align": "top" }}>
                        <span
                          style={{
                            "border-radius": "4px",
                            "font-size": "0.9em",
                          }}
                        >
                          {data.focusArea}
                        </span>
                      </td>
                      <td style={{ padding: "12px", "vertical-align": "top" }}>
                        <span
                          style={{
                            padding: "4px 8px",
                            "background-color":
                              data.datasetPresence === "Present"
                                ? "#d4edda"
                                : "#f8d7da",
                            color:
                              data.datasetPresence === "Present"
                                ? "#155724"
                                : "#721c24",
                            "border-radius": "4px",
                            "font-size": "0.9em",
                          }}
                        >
                          {data.datasetPresence}
                        </span>
                      </td>
                    </tr>
                  )}
                </For>
              </tbody>
            </table>
          </div>
        </Show>
      </Suspense>
    </section>
  );
}
