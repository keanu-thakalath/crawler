import { createAsync, query, useParams } from "@solidjs/router";
import { Suspense, For, Show, createMemo } from "solid-js";
import * as api from "~/api";
import { usePolling } from "~/utils/polling";
import PageItem from "~/components/PageItem";
import TaskStatus from "~/components/TaskStatus";

const getSources = query(async () => {
  return await api.getSources();
}, "sources");

export default function SourceDetail() {
  const params = useParams();
  const decodedUrl = decodeURIComponent(params.url);
  const sources = createAsync(() => getSources());

  usePolling(getSources.key);

  const currentSource = createMemo(() => {
    const allSources = sources();
    return allSources?.find((source) => source.url === decodedUrl);
  });

  const summarizeResult = createMemo(() => {
    const source = currentSource();
    if (!source) return null;

    const summarizeJob = source.jobs.find(
      (job) =>
        job.outcome && "summary" in job.outcome && "data_origin" in job.outcome
    );
    return summarizeJob?.outcome as api.SummarizeJobOutcome | undefined;
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
