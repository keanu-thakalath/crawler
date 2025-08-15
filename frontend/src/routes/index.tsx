import {
  createAsync,
  query,
  action,
  revalidate,
  useSubmission,
} from "@solidjs/router";
import { For, Show, Suspense } from "solid-js";
import * as api from "~/api";
import SourceItem from "~/components/SourceItem";
import { usePolling } from "~/utils/polling";

const getSources = query(async () => {
  return await api.getSources();
}, "sources");

const crawlAction = action(async (formData: FormData) => {
  "use server";
  const url = formData.get("url") as string;
  if (!url) throw new Error("URL is required");

  await api.crawlUrl(url);
  await revalidate(getSources.key);
  return {};
}, "crawl");

export default function Index() {
  const sources = createAsync(() => getSources());
  const submission = useSubmission(crawlAction);

  usePolling(getSources.key);

  return (
    <>
      <form action={crawlAction} method="post">
        <fieldset
          role="group"
          aria-invalid={submission.error && !!submission.error}
        >
          <input
            type="text"
            name="url"
            aria-invalid={submission.error && !!submission.error}
          />

          <button
            disabled={submission.pending}
            aria-busy={submission.pending}
            type="submit"
          >
            Crawl
          </button>
        </fieldset>

        <Show when={submission.error}>
          <small>{submission.error.message}</small>{" "}
        </Show>
      </form>

      <Suspense fallback={<ul aria-busy="true">Loading...</ul>}>
        <ul>
          <For each={sources()}>
            {(source) => <SourceItem source={source} />}
          </For>
        </ul>
      </Suspense>
    </>
  );
}
