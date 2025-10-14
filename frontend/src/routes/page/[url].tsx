import { createAsync, query, useParams, action, revalidate, useSubmission } from "@solidjs/router";
import { Suspense, For, Show, createMemo, createSignal } from "solid-js";
import { marked } from "marked";
import * as api from "~/api";
import { usePolling } from "~/utils/polling";
import TaskStatus from "~/components/TaskStatus";

const getSources = query(async () => {
  return await api.getSources();
}, "sources");

const extractAction = action(async (formData: FormData) => {
  const pageUrl = formData.get("pageUrl") as string;
  const markdownContent = formData.get("markdownContent") as string;
  const prompt = formData.get("prompt") as string;
  
  if (!pageUrl) throw new Error("Page URL is required");
  if (!markdownContent) throw new Error("Markdown content is required");

  await api.extractPage(pageUrl, markdownContent, prompt || undefined);
  await revalidate("sources");
  return {};
}, "extractPage");

export default function PageDetail() {
  const params = useParams();
  const decodedUrl = decodeURIComponent(params.url);
  const sources = createAsync(() => getSources());
  const [extractPrompt, setExtractPrompt] = createSignal("");
  const extractSubmission = useSubmission(extractAction);

  usePolling(getSources.key);

  const currentPage = createMemo(() => {
    const allSources = sources();
    if (!allSources) return null;

    for (const source of allSources) {
      const page = source.pages.find((p) => p.url === decodedUrl);
      if (page) return page;
    }
    return null;
  });

  const scrapeResult = createMemo(() => {
    const page = currentPage();
    if (!page) return null;

    const scrapeJobs = page.jobs.filter(
      (job) => job.outcome && "markdown" in job.outcome
    );
    const lastScrapeJob = scrapeJobs[scrapeJobs.length - 1];
    return lastScrapeJob?.outcome as api.ScrapeJobOutcome | undefined;
  });

  const extractResult = createMemo(() => {
    const page = currentPage();
    if (!page) return null;

    const extractJobs = page.jobs.filter(
      (job) =>
        job.outcome &&
        "summary" in job.outcome &&
        "internal_links" in job.outcome
    );
    const lastExtractJob = extractJobs[extractJobs.length - 1];
    return lastExtractJob?.outcome as api.ExtractJobOutcome | undefined;
  });

  const getJobStatus = () => {
    const page = currentPage();
    if (!page || page.jobs.length === 0) return "No jobs";

    const hasRunning = page.jobs.some((job) => !job.outcome);
    const allCompleted = page.jobs.every((job) => job.outcome);

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

        <Show when={scrapeResult()?.markdown}>
          <section
            style={{
              "margin-bottom": "24px",
              padding: "16px",
              border: "1px solid #ddd",
              "border-radius": "8px",
              "background-color": "#f9f9f9",
            }}
          >
            <p>
              <strong>Extract Links & Summary:</strong>
            </p>
            <form action={extractAction} method="post">
              <input type="hidden" name="pageUrl" value={decodedUrl} />
              <input type="hidden" name="markdownContent" value={scrapeResult()?.markdown || ""} />
              
              <textarea
                name="prompt"
                value={extractPrompt()}
                onInput={(e) => setExtractPrompt(e.target.value)}
                placeholder="Enter custom extraction prompt (optional)"
                style={{
                  width: "100%",
                  height: "80px",
                  "margin-bottom": "12px",
                  padding: "8px",
                  "border-radius": "4px",
                  border: "1px solid #ccc",
                  "font-family": "monospace",
                  "font-size": "12px",
                }}
                aria-invalid={extractSubmission.error && !!extractSubmission.error}
              />
              <button
                type="submit"
                disabled={extractSubmission.pending}
                aria-busy={extractSubmission.pending}
                style={{
                  padding: "8px 16px",
                  "background-color": "#007bff",
                  color: "white",
                  border: "none",
                  "border-radius": "4px",
                  cursor: extractSubmission.pending ? "not-allowed" : "pointer",
                  opacity: extractSubmission.pending ? 0.6 : 1,
                }}
              >
                {extractSubmission.pending ? "Extracting..." : "Extract"}
              </button>

              {extractSubmission.error && (
                <div style={{ 
                  "margin-top": "12px", 
                  color: "#dc3545",
                  "font-size": "14px"
                }}>
                  Error: {extractSubmission.error.message}
                </div>
              )}
            </form>
          </section>
        </Show>

        <Show when={currentPage()?.jobs && currentPage()!.jobs.length > 0}>
          <section>
            <p>
              <strong>Jobs:</strong>
            </p>
            <ul>
              <For each={currentPage()!.jobs}>
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

        <Show
          when={
            extractResult()?.file_links &&
            extractResult()!.file_links.length > 0
          }
        >
          <section>
            <p>
              <strong>Extracted Files:</strong>
            </p>
            <ul>
              <For each={extractResult()!.file_links}>
                {(fileUrl) => (
                  <li>
                    <a href={fileUrl} target="_blank" rel="noopener noreferrer">
                      {fileUrl}
                    </a>
                  </li>
                )}
              </For>
            </ul>
          </section>
        </Show>

        <Show
          when={
            extractResult()?.internal_links &&
            extractResult()!.internal_links.length > 0
          }
        >
          <section>
            <p>
              <strong>Internal Links:</strong>
            </p>
            <ul>
              <For each={extractResult()!.internal_links}>
                {(link) => (
                  <li>
                    <a href={link} target="_blank" rel="noopener noreferrer">
                      {link}
                    </a>
                  </li>
                )}
              </For>
            </ul>
          </section>
        </Show>

        <Show
          when={
            extractResult()?.external_links &&
            extractResult()!.external_links.length > 0
          }
        >
          <section>
            <p>
              <strong>External Links:</strong>
            </p>
            <ul>
              <For each={extractResult()!.external_links}>
                {(link) => (
                  <li>
                    <a href={link} target="_blank" rel="noopener noreferrer">
                      {link}
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
