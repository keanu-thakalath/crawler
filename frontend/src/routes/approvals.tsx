import { createAsync, query } from "@solidjs/router";
import { Show, Suspense, createMemo } from "solid-js";
import { marked } from "marked";
import * as api from "~/api";
import { usePolling } from "~/utils/polling";
import EditableSummary from "~/components/EditableSummary";

const getSources = query(async () => {
  return await api.getSources();
}, "sources");

export default function Approvals() {
  const sources = createAsync(() => getSources());

  usePolling(getSources.key);

  // Find the next unreviewed job declaratively from getSources()
  const nextUnreviewedJob = createMemo(() => {
    const allSources = sources();
    if (!allSources) return null;

    // Search through all sources and their pages/jobs
    for (const source of allSources) {
      // Check page-level jobs (extract jobs)
      for (const page of source.pages) {
        for (const job of page.jobs) {
          if (
            job.outcome &&
            "summary" in job.outcome &&
            "internal_links" in job.outcome &&
            job.outcome.review_status === "Unreviewed"
          ) {
            return {
              job,
              outcome: job.outcome as api.ExtractJobOutcome,
              type: "extract" as const,
              sourceUrl: source.url,
              pageUrl: page.url,
            };
          }
        }
      }

      // Check source-level jobs (summarize jobs)
      for (const job of source.jobs) {
        if (
          job.outcome &&
          "summary" in job.outcome &&
          "data_origin" in job.outcome &&
          job.outcome.review_status === "Unreviewed"
        ) {
          return {
            job,
            outcome: job.outcome as api.SummarizeJobOutcome,
            type: "summarize" as const,
            sourceUrl: source.url,
            pageUrl: null,
          };
        }
      }
    }
    return null;
  });

  // Get scraped markdown for extract jobs to show as metadata
  const scrapedMarkdown = createMemo(() => {
    const jobInfo = nextUnreviewedJob();
    if (!jobInfo || jobInfo.type !== "extract") return null;

    const allSources = sources();
    if (!allSources) return null;

    // Find the page and look for a scrape job result
    for (const source of allSources) {
      const page = source.pages.find((p) => p.url === jobInfo.pageUrl);
      if (page) {
        const scrapeJob = page.jobs.find(
          (job) => job.outcome && "markdown" in job.outcome
        );
        return scrapeJob?.outcome as api.ScrapeJobOutcome | null;
      }
    }
    return null;
  });

  return (
    <section>
      <h2>Job Approval Workflow</h2>

      <Suspense fallback={<section aria-busy="true">Loading...</section>}>
        <Show
          when={nextUnreviewedJob()}
          fallback={
            <div
              style={{
                padding: "20px",
                "background-color": "#f8f9fa",
                "border-radius": "8px",
                "text-align": "center",
              }}
            >
              <p>🎉 No jobs pending approval!</p>
              <p style={{ color: "#666", "font-size": "0.9em" }}>
                All jobs have been reviewed and approved.
              </p>
            </div>
          }
        >
          {(jobInfo) => (
            <div>
              <div
                style={{
                  padding: "16px",
                  "background-color": "#4443cd",
                  "border-radius": "8px",
                  "margin-bottom": "20px",
                }}
              >
                <h3>Job Pending Approval</h3>
                <p>
                  <strong>Job ID:</strong> {jobInfo().job.job_id}
                </p>
                <p>
                  <strong>Type:</strong>{" "}
                  {jobInfo().type === "extract"
                    ? "Page Extract"
                    : "Source Summary"}
                </p>
                <p>
                  <strong>Source:</strong>
                  <a
                    href={jobInfo().sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {jobInfo().sourceUrl}
                  </a>
                </p>
                <Show when={jobInfo().pageUrl}>
                  <p>
                    <strong>Page:</strong>
                    <a
                      href={jobInfo().pageUrl!}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {jobInfo().pageUrl}
                    </a>
                  </p>
                </Show>
                <p>
                  <strong>Created:</strong>{" "}
                  {new Date(jobInfo().job.created_at).toLocaleString()}
                </p>

                <Show when={jobInfo().type === "summarize"}>
                  <div style={{ "margin-top": "12px" }}>
                    <p>
                      <strong>Data Origin:</strong>{" "}
                      {
                        (jobInfo().outcome as api.SummarizeJobOutcome)
                          .data_origin
                      }
                    </p>
                    <p>
                      <strong>Source Format:</strong>{" "}
                      {
                        (jobInfo().outcome as api.SummarizeJobOutcome)
                          .source_format
                      }
                    </p>
                    <p>
                      <strong>Focus Area:</strong>{" "}
                      {
                        (jobInfo().outcome as api.SummarizeJobOutcome)
                          .focus_area
                      }
                    </p>
                  </div>
                </Show>

                <Show
                  when={
                    jobInfo().outcome.input_tokens ||
                    jobInfo().outcome.output_tokens
                  }
                >
                  <p>
                    <strong>Token Usage:</strong>
                    Input: {jobInfo().outcome.input_tokens || 0}, Output:{" "}
                    {jobInfo().outcome.output_tokens || 0}
                  </p>
                </Show>
              </div>

              <Show when={jobInfo().outcome.summary}>
                <EditableSummary
                  initialSummary={jobInfo().outcome.summary}
                  jobId={jobInfo().job.job_id}
                />
              </Show>

              {/* Show scraped content for extract jobs as metadata */}
              <Show when={scrapedMarkdown()?.markdown}>
                <details style={{ "margin-top": "24px" }}>
                  <summary style={{ cursor: "pointer", "font-weight": "bold" }}>
                    View Original Scraped Content
                  </summary>
                  <div
                    style={{
                      "margin-top": "12px",
                      padding: "16px",
                      "background-color": "#f8f9fa",
                      "border-radius": "4px",
                      "max-height": "400px",
                      "overflow-y": "auto",
                    }}
                  >
                    <article
                      innerHTML={marked.parse(scrapedMarkdown()!.markdown, {
                        async: false,
                      })}
                    />
                  </div>
                </details>
              </Show>
            </div>
          )}
        </Show>
      </Suspense>
    </section>
  );
}
