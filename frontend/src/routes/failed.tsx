import { createAsync, query } from "@solidjs/router";
import { For, Show, Suspense, createMemo } from "solid-js";
import * as api from "~/api";
import { usePolling } from "~/utils/polling";

const getFailedJobs = query(async () => {
  return await api.getFailedJobs();
}, "failedJobs");

interface FailedJobData {
  sourceUrl: string;
  pageUrl?: string;
  jobType: string;
  errorMessage: string;
  createdAt: string;
}

export default function Failed() {
  const sources = createAsync(() => getFailedJobs());

  usePolling(getFailedJobs.key);

  // Extract failed job data from sources and pages
  const failedJobsData = createMemo(() => {
    const sourcesData = sources();
    if (!sourcesData) return [];

    const failedJobs: FailedJobData[] = [];

    for (const source of sourcesData) {
      // Process source-level failed jobs
      for (const job of source.jobs) {
        if (job.outcome && "message" in job.outcome) {
          const jobError = job.outcome as api.JobError;
          failedJobs.push({
            sourceUrl: source.url,
            pageUrl: undefined,
            jobType: getJobTypeFromJob(job),
            errorMessage: jobError.message,
            createdAt: job.created_at,
          });
        }
      }

      // Process page-level failed jobs
      for (const page of source.pages) {
        for (const job of page.jobs) {
          if (job.outcome && "message" in job.outcome) {
            const jobError = job.outcome as api.JobError;
            failedJobs.push({
              sourceUrl: source.url,
              pageUrl: page.url,
              jobType: getJobTypeFromJob(job),
              errorMessage: jobError.message,
              createdAt: job.created_at,
            });
          }
        }
      }
    }

    // Sort by creation date (most recent first)
    return failedJobs.sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  });

  function getJobTypeFromJob(job: api.Job): string {
    // Since this is a failed job, we need to infer the type from the job structure
    // This is a best guess based on typical job patterns
    if (!job.outcome) return "Unknown";
    
    // For failed jobs, we can try to determine type from job_id patterns or other clues
    // But since we don't have explicit type info, we'll use a generic approach
    return "Job";
  }

  return (
    <section>
      <h2>Failed Jobs</h2>
      <p style={{ color: "#666", "margin-bottom": "20px" }}>
        Jobs that have encountered errors during processing.
      </p>

      <Suspense fallback={<div aria-busy="true">Loading failed jobs...</div>}>
        <Show
          when={failedJobsData() && failedJobsData().length > 0}
          fallback={
            <div
              style={{
                padding: "20px",
                "background-color": "#d4edda",
                "border-radius": "8px",
                "text-align": "center",
                border: "1px solid #c3e6cb",
              }}
            >
              <p>✅ No failed jobs found!</p>
              <p style={{ color: "#155724", "font-size": "0.9em" }}>
                All jobs are completing successfully.
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
                <tr style={{ "background-color": "#dc3545", color: "white" }}>
                  <th
                    style={{
                      padding: "12px",
                      "text-align": "left",
                      "font-weight": "600",
                    }}
                  >
                    Source
                  </th>
                  <th
                    style={{
                      padding: "12px",
                      "text-align": "left",
                      "font-weight": "600",
                    }}
                  >
                    Page
                  </th>
                  <th
                    style={{
                      padding: "12px",
                      "text-align": "left",
                      "font-weight": "600",
                    }}
                  >
                    Job Type
                  </th>
                  <th
                    style={{
                      padding: "12px",
                      "text-align": "left",
                      "font-weight": "600",
                    }}
                  >
                    Error Message
                  </th>
                  <th
                    style={{
                      padding: "12px",
                      "text-align": "left",
                      "font-weight": "600",
                    }}
                  >
                    Failed At
                  </th>
                </tr>
              </thead>
              <tbody>
                <For each={failedJobsData()}>
                  {(data, index) => (
                    <tr
                      style={{
                        "border-bottom":
                          index() < failedJobsData().length - 1
                            ? "1px solid #eee"
                            : "none",
                        "background-color":
                          index() % 2 === 0 ? "#fff5f5" : "#fff",
                      }}
                    >
                      <td style={{ padding: "12px", "vertical-align": "top" }}>
                        <a
                          href={`/source/${encodeURIComponent(data.sourceUrl)}`}
                          style={{
                            color: "#dc3545",
                            "text-decoration": "none",
                            "word-break": "break-all",
                            "font-weight": "500",
                            "font-size": "0.9em",
                          }}
                        >
                          {data.sourceUrl}
                        </a>
                      </td>
                      <td style={{ padding: "12px", "vertical-align": "top" }}>
                        <Show
                          when={data.pageUrl}
                          fallback={
                            <span
                              style={{
                                color: "#666",
                                "font-style": "italic",
                                "font-size": "0.9em",
                              }}
                            >
                              Source-level
                            </span>
                          }
                        >
                          <a
                            href={`/page/${encodeURIComponent(data.pageUrl!)}`}
                            style={{
                              color: "#dc3545",
                              "text-decoration": "none",
                              "word-break": "break-all",
                              "font-size": "0.9em",
                            }}
                          >
                            {data.pageUrl}
                          </a>
                        </Show>
                      </td>
                      <td style={{ padding: "12px", "vertical-align": "top" }}>
                        <span
                          style={{
                            padding: "4px 8px",
                            "background-color": "#f8d7da",
                            color: "#721c24",
                            "border-radius": "4px",
                            "font-size": "0.8em",
                            "font-weight": "500",
                          }}
                        >
                          {data.jobType}
                        </span>
                      </td>
                      <td style={{ padding: "12px", "vertical-align": "top" }}>
                        <div
                          style={{
                            "max-width": "300px",
                            "word-wrap": "break-word",
                            "font-size": "0.9em",
                            color: "#721c24",
                          }}
                          title={data.errorMessage}
                        >
                          {data.errorMessage.length > 100
                            ? `${data.errorMessage.substring(0, 100)}...`
                            : data.errorMessage}
                        </div>
                      </td>
                      <td style={{ padding: "12px", "vertical-align": "top" }}>
                        <div style={{ "font-size": "0.85em", color: "#666" }}>
                          {new Date(data.createdAt).toLocaleString()}
                        </div>
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