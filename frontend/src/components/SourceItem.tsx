import { A, action, revalidate, useSubmission } from "@solidjs/router";
import { For, Show } from "solid-js";
import * as api from "~/api";
import PageItem from "~/components/PageItem";

const crawlAction = action(async (formData: FormData) => {
  "use server";
  const url = formData.get("url") as string;
  const maxPages = parseInt(formData.get("maxPages") as string) || 3;
  if (!url) throw new Error("URL is required");

  await api.crawlUrl(url, maxPages);
  await revalidate("sources");
  return {};
}, "crawl");

interface SourceItemProps {
  source: api.Source;
}

export default function SourceItem(props: SourceItemProps) {
  const crawlSubmission = useSubmission(crawlAction);

  const getSourceStatus = () => {
    const hasJobs = props.source.jobs.length > 0;
    if (!hasJobs) return "No jobs";
    
    const hasRunningJobs = props.source.jobs.some(job => !job.outcome);
    const allJobsComplete = props.source.jobs.every(job => job.outcome);
    
    if (hasRunningJobs) return "Processing";
    if (allJobsComplete) return "Completed";
    return "Pending";
  };

  return (
    <li style={{ "margin-bottom": "20px", padding: "10px", border: "1px solid #ccc" }}>
      <div style={{ display: "flex", "justify-content": "space-between", "align-items": "center" }}>
        <h5>
          <A href={`/source/${encodeURIComponent(props.source.url)}`}>
            {props.source.url}
          </A>
          <span style={{ "margin-left": "10px", "font-weight": "normal", color: "#666" }}>
            ({getSourceStatus()})
          </span>
        </h5>
        <form action={crawlAction} method="post" style={{ margin: "0" }}>
          <input type="hidden" name="url" value={props.source.url} />
          <input type="hidden" name="maxPages" value="3" />
          <button 
            type="submit"
            disabled={crawlSubmission.pending}
            aria-busy={crawlSubmission.pending}
            style={{ padding: "5px 10px", "background-color": "#007bff", color: "white", border: "none", "border-radius": "3px" }}
          >
            Crawl
          </button>
        </form>
      </div>
      <Show when={crawlSubmission.error}>
        <div style={{ color: "red", "margin-top": "5px", "font-size": "0.9em" }}>
          Error: {crawlSubmission.error.message}
        </div>
      </Show>
      <ul>
        <For each={props.source.pages}>
          {(page) => <PageItem page={page} />}
        </For>
      </ul>
    </li>
  );
}
