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
  "use server";
  return await api.getSources();
}, "sources");

const addSourceAction = action(async (formData: FormData) => {
  "use server";
  const url = formData.get("url") as string;
  if (!url) throw new Error("URL is required");

  await api.addSource(url);
  await revalidate(getSources.key);
  return {};
}, "addSource");

export default function Index() {
  const sources = createAsync(() => getSources());
  const addSourceSubmission = useSubmission(addSourceAction);

  usePolling(getSources.key);

  return (
    <>
      <h2>Add New Source</h2>
      <form action={addSourceAction} method="post">
        <fieldset
          role="group"
          aria-invalid={
            addSourceSubmission.error && !!addSourceSubmission.error
          }
        >
          <input
            type="text"
            name="url"
            placeholder="Enter URL to add as source"
            aria-invalid={
              addSourceSubmission.error && !!addSourceSubmission.error
            }
          />

          <button
            disabled={addSourceSubmission.pending}
            aria-busy={addSourceSubmission.pending}
            type="submit"
          >
            Add Source
          </button>
        </fieldset>

        <Show when={addSourceSubmission.error}>
          <small>{addSourceSubmission.error.message}</small>{" "}
        </Show>
      </form>

      <h2>Sources</h2>
      <Suspense fallback={<ul aria-busy="true">Loading...</ul>}>
        <ul style={{ "list-style": "none", padding: "0" }}>
          <For each={sources()}>
            {(source) => <SourceItem source={source} />}
          </For>
        </ul>
      </Suspense>
    </>
  );
}
