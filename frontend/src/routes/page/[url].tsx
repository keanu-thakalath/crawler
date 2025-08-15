import { createAsync, query, useParams } from "@solidjs/router";
import { Suspense, For, Show, createEffect, createSignal } from "solid-js";
import { marked } from "marked";
import * as api from "~/api";
import { usePolling } from "~/utils/polling";

const getPageJobs = query(async (url: string) => {
  return await api.getPageJobs(url);
}, "pageJobs");

export default function PageDetail() {
  const params = useParams();
  const decodedUrl = decodeURIComponent(params.url);
  const pageJobs = createAsync(() => getPageJobs(decodedUrl));

  const [scrapeResult, setScrapeResult] =
    createSignal<api.ScrapeJobResponse | null>(null);
  const [extractResult, setExtractResult] =
    createSignal<api.ExtractJobResponse | null>(null);

  usePolling(getPageJobs.keyFor(decodedUrl));

  createEffect(async () => {
    const jobs = pageJobs();
    if (!jobs) return;

    // Find completed scrape job
    const scrapeJob = jobs.find(
      (job) => job.job_type === "scrape" && job.status === "completed"
    );
    if (scrapeJob && !scrapeResult()) {
      try {
        const result = await api.getScrapeResult(scrapeJob.id);
        setScrapeResult(result);
      } catch (error) {
        console.error("Failed to fetch scrape result:", error);
      }
    }

    // Find completed extract job
    const extractJob = jobs.find(
      (job) => job.job_type === "extract" && job.status === "completed"
    );
    if (extractJob && !extractResult()) {
      try {
        const result = await api.getExtractResult(extractJob.id);
        setExtractResult(result);
      } catch (error) {
        console.error("Failed to fetch extract result:", error);
      }
    }
  });

  const getJobStatus = () => {
    const jobs = pageJobs();
    if (!jobs || jobs.length === 0) return "No jobs";

    const hasRunning = jobs.some((job) => job.status === "running");
    const allCompleted = jobs.every((job) => job.status === "completed");

    if (hasRunning) return "Processing";
    if (allCompleted) return "Completed";
    return "Pending";
  };

  return (
    <Suspense
      fallback={<section aria-busy="true">Loading page details...</section>}
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

        <Show when={pageJobs() && pageJobs()!.length > 0}>
          <section>
            <p>
              <strong>Jobs:</strong>
            </p>
            <ul>
              <For each={pageJobs()}>
                {(job) => (
                  <li aria-busy={job.status === "pending"}>
                    {job.job_type}: {job.status}
                    <Show when={job.status === "pending"}>
                      <span style={{ "margin-left": "8px" }}>⏳</span>
                    </Show>
                  </li>
                )}
              </For>
            </ul>
          </section>
        </Show>

        <Show
          when={extractResult()?.files && extractResult()!.files.length > 0}
        >
          <section>
            <p>
              <strong>Extracted Files:</strong>
            </p>
            <ul>
              <For each={extractResult()?.files}>
                {(file) => (
                  <li>
                    <a
                      href={file.url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {file.url}
                    </a>
                  </li>
                )}
              </For>
            </ul>
          </section>
        </Show>

        <Show when={extractResult()?.summary}>
          <section>
            <p>
              <strong>Summary:</strong>
            </p>
            <p>{extractResult()?.summary}</p>
          </section>
        </Show>

        <Show
          when={extractResult()?.input_tokens || extractResult()?.output_tokens}
        >
          <section>
            <p>
              <strong>Token Usage:</strong>
            </p>
            <p>
              Input: {extractResult()?.input_tokens || 0}, Output:{" "}
              {extractResult()?.output_tokens || 0}
            </p>
          </section>
        </Show>

        <Show when={scrapeResult()?.markdown}>
          <section>
            <p>
              <strong>Scraped content:</strong>
            </p>
            <article
              innerHTML={marked.parse(scrapeResult()?.markdown || "", {
                async: false,
              })}
            />
          </section>
        </Show>
      </section>
    </Suspense>
  );
}
