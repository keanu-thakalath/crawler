import { action, useSubmission } from "@solidjs/router";
import { Show } from "solid-js";
import * as api from "~/api";

const crawlUrlAction = action(async (formData: FormData) => {
  const url = formData.get("url") as string;
  const maxPages = parseInt(formData.get("maxPages") as string) || 3;
  const extractPrompt = (formData.get("extractPrompt") as string) || undefined;

  if (!url) throw new Error("URL is required");

  await api.crawlUrl(url, maxPages, extractPrompt);
  return { success: true, message: "Crawl job started successfully!" };
}, "crawlUrl");

export default function Index() {
  const crawlSubmission = useSubmission(crawlUrlAction);

  return (
    <section>
      <h2>Crawl Website</h2>
      <form action={crawlUrlAction} method="post">
        <fieldset>
          <label for="url">Website URL:</label>
          <input
            id="url"
            type="url"
            name="url"
            placeholder="https://example.com"
            required
            aria-invalid={crawlSubmission.error && !!crawlSubmission.error}
          />

          <label for="maxPages">Max Pages to Crawl:</label>
          <input
            id="maxPages"
            type="number"
            name="maxPages"
            min="1"
            max="50"
            value="10"
          />

          <label for="extractPrompt">Custom Extract Prompt (Optional):</label>
          <textarea
            id="extractPrompt"
            name="extractPrompt"
            placeholder="Optional custom prompt for content extraction..."
            rows="3"
          ></textarea>

          <input
            disabled={crawlSubmission.pending}
            aria-busy={crawlSubmission.pending}
            type="submit"
            value={
              crawlSubmission.pending ? "Starting Crawl..." : "Start Crawl"
            }
          />
        </fieldset>

        <Show when={crawlSubmission.error}>
          <small style="color: red;">{crawlSubmission.error.message}</small>
        </Show>

        <Show when={crawlSubmission.result?.success}>
          <small style="color: green;">{crawlSubmission.result?.message}</small>
        </Show>
      </form>
    </section>
  );
}
