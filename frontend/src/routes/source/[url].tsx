import { createAsync, query, useParams, action, revalidate, useSubmission } from "@solidjs/router";
import { Suspense, For, Show, createMemo, createSignal } from "solid-js";
import * as api from "~/api";
import { usePolling } from "~/utils/polling";
import PageItem from "~/components/PageItem";
import TaskStatus from "~/components/TaskStatus";

const getSources = query(async () => {
  return await api.getSources();
}, "sources");

const summarizeAction = action(async (formData: FormData) => {
  const sourceUrl = formData.get("sourceUrl") as string;
  const allPageSummaries = formData.get("allPageSummaries") as string;
  const prompt = formData.get("prompt") as string;
  
  if (!sourceUrl) throw new Error("Source URL is required");
  if (!allPageSummaries) throw new Error("Page summaries are required");

  await api.summarizeSource(sourceUrl, allPageSummaries, prompt || undefined);
  await revalidate("sources");
  return {};
}, "summarizeSource");

export default function SourceDetail() {
  const params = useParams();
  const decodedUrl = decodeURIComponent(params.url);
  const sources = createAsync(() => getSources());
  const [summarizePrompt, setSummarizePrompt] = createSignal("");
  const summarizeSubmission = useSubmission(summarizeAction);

  usePolling(getSources.key);

  const currentSource = createMemo(() => {
    const allSources = sources();
    return allSources?.find((source) => source.url === decodedUrl);
  });

  const summarizeResult = createMemo(() => {
    const source = currentSource();
    if (!source) return null;

    const summarizeJobs = source.jobs.filter(
      (job) =>
        job.outcome && "summary" in job.outcome && "data_origin" in job.outcome
    );
    const lastSummarizeJob = summarizeJobs[summarizeJobs.length - 1];
    return lastSummarizeJob?.outcome as api.SummarizeJobOutcome | undefined;
  });

  const getJobStatus = () => {
    const source = currentSource();
    if (!source || source.jobs.length === 0) return "No jobs";

    const hasRunning = source.jobs.some((job) => !job.outcome);
    const allCompleted = source.jobs.every((job) => job.outcome);

    if (hasRunning) return "Processing";
    if (allCompleted) return "Completed";
    return "Pending";
  };

  const getPageSummaries = () => {
    const source = currentSource();
    if (!source) return "";

    const summaries: string[] = [];
    for (const page of source.pages) {
      const extractJobs = page.jobs.filter(
        (job) =>
          job.outcome &&
          "summary" in job.outcome &&
          "internal_links" in job.outcome
      );
      const lastExtractJob = extractJobs[extractJobs.length - 1];
      if (lastExtractJob?.outcome && "summary" in lastExtractJob.outcome) {
        summaries.push(`Markdown for ${page.url}:\n\n${lastExtractJob.outcome.summary}`);
      }
    }
    return summaries.join("\n\n");
  };

  return (
    <Suspense
      fallback={<section aria-busy="true">Loading source details...</section>}
    >
      <section>
        <p>
          <strong>URL:</strong> {decodedUrl}
        </p>

        <p>
          <strong>Status:</strong>
          <span
            style={{
              "margin-left": "8px",
              padding: "2px 6px",
              "border-radius": "4px",
              "font-size": "12px",
              "background-color":
                getJobStatus() === "Completed" ? "#d4edda" : "#fff3cd",
              color: getJobStatus() === "Completed" ? "#155724" : "#856404",
            }}
            aria-busy={getJobStatus() === "Processing"}
          >
            {getJobStatus()}
          </span>
        </p>

        <Show when={getPageSummaries()}>
          <section style={{ 
            "margin-bottom": "24px", 
            padding: "16px", 
            border: "1px solid #ddd", 
            "border-radius": "8px",
            "background-color": "#f9f9f9"
          }}>
            <p>
              <strong>Summarize Source:</strong>
            </p>
            <form action={summarizeAction} method="post">
              <input type="hidden" name="sourceUrl" value={decodedUrl} />
              <input type="hidden" name="allPageSummaries" value={getPageSummaries()} />
              
              <textarea
                name="prompt"
                value={summarizePrompt()}
                onInput={(e) => setSummarizePrompt(e.target.value)}
                placeholder="Enter custom summarization prompt (optional)"
                style={{
                  width: "100%",
                  height: "80px",
                  "margin-bottom": "12px",
                  padding: "8px",
                  "border-radius": "4px",
                  border: "1px solid #ccc",
                  "font-family": "monospace",
                  "font-size": "12px"
                }}
                aria-invalid={summarizeSubmission.error && !!summarizeSubmission.error}
              />
              <button
                type="submit"
                disabled={summarizeSubmission.pending}
                aria-busy={summarizeSubmission.pending}
                style={{
                  padding: "8px 16px",
                  "background-color": "#28a745",
                  color: "white",
                  border: "none",
                  "border-radius": "4px",
                  cursor: summarizeSubmission.pending ? "not-allowed" : "pointer",
                  opacity: summarizeSubmission.pending ? 0.6 : 1
                }}
              >
                {summarizeSubmission.pending ? "Summarizing..." : "Summarize"}
              </button>

              {summarizeSubmission.error && (
                <div style={{ 
                  "margin-top": "12px", 
                  color: "#dc3545",
                  "font-size": "14px"
                }}>
                  Error: {summarizeSubmission.error.message}
                </div>
              )}
            </form>
          </section>
        </Show>

        <Show when={currentSource()?.jobs && currentSource()!.jobs.length > 0}>
          <section>
            <p>
              <strong>Jobs:</strong>
            </p>
            <ul>
              <For each={currentSource()!.jobs}>
                {(job) => (
                  <li>
                    {job.job_id}: <TaskStatus job={job} />
                    <div style={{ "font-size": "0.8em", color: "#666" }}>
                      Created: {new Date(job.created_at).toLocaleString()}
                    </div>
                  </li>
                )}
              </For>
            </ul>
          </section>
        </Show>

        <Show when={summarizeResult()?.summary}>
          <section>
            <p>
              <strong>Summary:</strong>
            </p>
            <p>{summarizeResult()!.summary}</p>
          </section>
        </Show>

        <Show when={summarizeResult()?.data_origin}>
          <section>
            <p>
              <strong>Data Origin:</strong>
            </p>
            <p>{summarizeResult()!.data_origin}</p>
          </section>
        </Show>

        <Show when={summarizeResult()?.source_format}>
          <section>
            <p>
              <strong>Source Format:</strong>
            </p>
            <p>{summarizeResult()!.source_format}</p>
          </section>
        </Show>

        <Show when={summarizeResult()?.focus_area}>
          <section>
            <p>
              <strong>Focus Area:</strong>
            </p>
            <p>{summarizeResult()!.focus_area}</p>
          </section>
        </Show>

        <Show
          when={
            summarizeResult()?.input_tokens || summarizeResult()?.output_tokens
          }
        >
          <section>
            <p>
              <strong>Token Usage:</strong>
            </p>
            <p>
              Input: {summarizeResult()?.input_tokens || 0}, Output:{" "}
              {summarizeResult()?.output_tokens || 0}
            </p>
          </section>
        </Show>

        <Show
          when={currentSource()?.pages && currentSource()!.pages.length > 0}
        >
          <section>
            <p>
              <strong>Pages:</strong>
            </p>
            <ul>
              <For each={currentSource()!.pages}>
                {(page) => <PageItem page={page} />}
              </For>
            </ul>
          </section>
        </Show>
      </section>
    </Suspense>
  );
}
