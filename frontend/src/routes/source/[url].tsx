import { createAsync, query, useParams } from "@solidjs/router";
import { Suspense, For, Show, createEffect, createSignal } from "solid-js";
import * as api from "~/api";
import { usePolling } from "~/utils/polling";
import PageItem from "~/components/PageItem";

const getSourceJobs = query(async (url: string) => {
  return await api.getSourceJobs(url);
}, "sourceJobs");

const getSources = query(async () => {
  return await api.getSources();
}, "sources");

export default function SourceDetail() {
  const params = useParams();
  const decodedUrl = decodeURIComponent(params.url);
  const sourceJobs = createAsync(() => getSourceJobs(decodedUrl));
  const sources = createAsync(() => getSources());
  
  const [summarizeResult, setSummarizeResult] = createSignal<api.SummarizeJobResponse | null>(null);

  usePolling(getSourceJobs.keyFor(decodedUrl));
  usePolling(getSources.key);

  createEffect(async () => {
    const jobs = sourceJobs();
    if (!jobs) return;

    // Find completed summarize job
    const summarizeJob = jobs.find(job => job.job_type === "summarize" && job.status === "completed");
    if (summarizeJob && !summarizeResult()) {
      try {
        const result = await api.getSummarizeResult(summarizeJob.id);
        setSummarizeResult(result);
      } catch (error) {
        console.error("Failed to fetch summarize result:", error);
      }
    }
  });

  const getJobStatus = () => {
    const jobs = sourceJobs();
    if (!jobs || jobs.length === 0) return "No jobs";
    
    const hasRunning = jobs.some(job => job.status === "running");
    const allCompleted = jobs.every(job => job.status === "completed");
    
    if (hasRunning) return "Processing";
    if (allCompleted) return "Completed";
    return "Pending";
  };

  const getCurrentSource = () => {
    const allSources = sources();
    return allSources?.find(source => source.url === decodedUrl);
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
              "background-color": getJobStatus() === "Completed"
                ? "#d4edda"
                : "#fff3cd",
              color: getJobStatus() === "Completed" ? "#155724" : "#856404",
            }}
            aria-busy={getJobStatus() === "Processing"}
          >
            {getJobStatus()}
          </span>
        </p>

        <Show when={sourceJobs() && sourceJobs()!.length > 0}>
          <section>
            <p><strong>Jobs:</strong></p>
            <ul>
              <For each={sourceJobs()}>
                {(job) => (
                  <li>
                    {job.job_type}: {job.status}
                  </li>
                )}
              </For>
            </ul>
          </section>
        </Show>

        <Show when={summarizeResult()?.summary}>
          <section>
            <p><strong>Summary:</strong></p>
            <p>{summarizeResult()?.summary}</p>
          </section>
        </Show>

        <Show when={summarizeResult()?.data_origin}>
          <section>
            <p><strong>Data Origin:</strong></p>
            <p>{summarizeResult()?.data_origin}</p>
          </section>
        </Show>

        <Show when={summarizeResult()?.source_format}>
          <section>
            <p><strong>Source Format:</strong></p>
            <p>{summarizeResult()?.source_format}</p>
          </section>
        </Show>

        <Show when={summarizeResult()?.focus_area}>
          <section>
            <p><strong>Focus Area:</strong></p>
            <p>{summarizeResult()?.focus_area}</p>
          </section>
        </Show>

        <Show when={summarizeResult()?.input_tokens || summarizeResult()?.output_tokens}>
          <section>
            <p><strong>Token Usage:</strong></p>
            <p>Input: {summarizeResult()?.input_tokens || 0}, Output: {summarizeResult()?.output_tokens || 0}</p>
          </section>
        </Show>

        <Show when={getCurrentSource()?.pages && getCurrentSource()!.pages.length > 0}>
          <section>
            <p><strong>Pages:</strong></p>
            <ul>
              <For each={getCurrentSource()?.pages}>
                {(page) => <PageItem page={page} />}
              </For>
            </ul>
          </section>
        </Show>
      </section>
    </Suspense>
  );
}