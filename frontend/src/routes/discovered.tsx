import {
  createAsync,
  query,
  action,
  useSubmission,
  revalidate,
} from "@solidjs/router";
import { For, Show, Suspense } from "solid-js";
import * as api from "~/api";
import { usePolling } from "~/utils/polling";

const getDiscoveredSources = query(async () => {
  return await api.getDiscoveredSources();
}, "discoveredSources");

const crawlSourceAction = action(async (formData: FormData) => {
  const url = formData.get("url") as string;
  const maxPages = parseInt(formData.get("maxPages") as string) || 3;

  if (!url) throw new Error("URL is required");

  await api.crawlUrl(url, maxPages);
  revalidate(getDiscoveredSources.key);
  return { success: true, message: `Crawl job started for ${url}!` };
}, "crawlSource");

const deleteSourceAction = action(async (formData: FormData) => {
  const url = formData.get("url") as string;

  if (!url) throw new Error("URL is required");

  if (
    !confirm(
      `Are you sure you want to delete this source?\n\n${url}\n\nThis will permanently delete the source and all its data.`
    )
  ) {
    return { cancelled: true };
  }

  await api.deleteSource(url);
  revalidate(getDiscoveredSources.key);
  return { success: true, message: `Source deleted successfully!` };
}, "deleteSource");

export default function Discovered() {
  const sources = createAsync(() => getDiscoveredSources());
  const crawlSubmission = useSubmission(crawlSourceAction);
  const deleteSubmission = useSubmission(deleteSourceAction);

  usePolling(getDiscoveredSources.key);

  return (
    <section>
      <h2>Discovered Sources</h2>
      <p style={{ color: "#666", "margin-bottom": "20px" }}>
        These sources have been discovered but not yet crawled. Start a crawl
        job to begin processing.
      </p>

      <Suspense
        fallback={<div aria-busy="true">Loading discovered sources...</div>}
      >
        <Show
          when={sources() && sources()!.length > 0}
          fallback={
            <div
              style={{
                padding: "20px",
                "border-radius": "8px",
                "text-align": "center",
              }}
            >
              <p>🔍 No discovered sources found!</p>
              <p style={{ color: "#666", "font-size": "0.9em" }}>
                All discovered sources have been crawled or no new sources have
                been found yet.
              </p>
            </div>
          }
        >
          <div
            style={{
              border: "1px solid #ddd",
              "border-radius": "8px",
              "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
              overflow: "hidden",
            }}
          >
            <For each={sources()}>
              {(source, index) => (
                <div
                  style={{
                    padding: "12px 16px",
                    "border-bottom":
                      index() < sources()!.length - 1
                        ? "1px solid #eee"
                        : "none",
                    display: "flex",
                    "align-items": "center",
                    gap: "16px",
                  }}
                >
                  <div style={{ flex: "1", "min-width": "0" }}>
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        color: "#4443cd",
                        "text-decoration": "none",
                        "word-break": "break-all",
                        "font-weight": "500",
                      }}
                    >
                      {source.url}
                    </a>
                  </div>

                  <div
                    style={{
                      display: "flex",
                      "align-items": "center",
                      gap: "12px",
                    }}
                  >
                    <form
                      action={crawlSourceAction}
                      method="post"
                      style={{
                        display: "flex",
                        "align-items": "center",
                        gap: "12px",
                      }}
                    >
                      <input type="hidden" name="url" value={source.url} />

                      <div
                        style={{
                          display: "flex",
                          "align-items": "center",
                          gap: "8px",
                        }}
                      >
                        <label
                          for={`maxPages-${source.url}`}
                          style={{
                            "font-size": "0.9em",
                            "white-space": "nowrap",
                          }}
                        >
                          Max Pages:
                        </label>
                        <input
                          id={`maxPages-${source.url}`}
                          type="number"
                          name="maxPages"
                          min="1"
                          max="50"
                          value="10"
                          style={{
                            width: "50px",
                            padding: "4px",
                            "font-size": "0.9em",
                          }}
                        />
                      </div>

                      <button
                        type="submit"
                        disabled={crawlSubmission.pending}
                        aria-busy={crawlSubmission.pending}
                        style={{
                          padding: "6px 12px",
                          "background-color": "#28a745",
                          color: "white",
                          border: "none",
                          "border-radius": "4px",
                          cursor: crawlSubmission.pending
                            ? "not-allowed"
                            : "pointer",
                          opacity: crawlSubmission.pending ? "0.7" : "1",
                          "font-size": "0.9em",
                          "white-space": "nowrap",
                        }}
                      >
                        {crawlSubmission.pending
                          ? "Starting..."
                          : "Start Crawl"}
                      </button>
                    </form>

                    <form action={deleteSourceAction} method="post">
                      <input type="hidden" name="url" value={source.url} />
                      <button
                        type="submit"
                        disabled={deleteSubmission.pending}
                        aria-busy={deleteSubmission.pending}
                        style={{
                          padding: "6px 12px",
                          "background-color": "#dc3545",
                          color: "white",
                          border: "none",
                          "border-radius": "4px",
                          cursor: deleteSubmission.pending
                            ? "not-allowed"
                            : "pointer",
                          opacity: deleteSubmission.pending ? "0.7" : "1",
                          "font-size": "0.9em",
                          "white-space": "nowrap",
                        }}
                      >
                        {deleteSubmission.pending ? "Deleting..." : "Delete"}
                      </button>
                    </form>
                  </div>
                </div>
              )}
            </For>
          </div>

          <Show when={crawlSubmission.error}>
            <div
              style={{
                "margin-top": "12px",
                color: "#dc3545",
                "font-size": "14px",
                padding: "8px",
                "background-color": "#f8d7da",
                "border-radius": "4px",
              }}
            >
              Error: {crawlSubmission.error.message}
            </div>
          </Show>

          <Show when={crawlSubmission.result?.success}>
            <div
              style={{
                "margin-top": "12px",
                color: "#28a745",
                "font-size": "14px",
                padding: "8px",
                "background-color": "#d4edda",
                "border-radius": "4px",
              }}
            >
              ✓ {crawlSubmission.result?.message}
            </div>
          </Show>

          <Show when={deleteSubmission.error}>
            <div
              style={{
                "margin-top": "12px",
                color: "#dc3545",
                "font-size": "14px",
                padding: "8px",
                "background-color": "#f8d7da",
                "border-radius": "4px",
              }}
            >
              Error: {deleteSubmission.error.message}
            </div>
          </Show>

          <Show when={deleteSubmission.result?.success}>
            <div
              style={{
                "margin-top": "12px",
                color: "#dc3545",
                "font-size": "14px",
                padding: "8px",
                "background-color": "#f8d7da",
                "border-radius": "4px",
              }}
            >
              ✓ {deleteSubmission.result?.message}
            </div>
          </Show>
        </Show>
      </Suspense>
    </section>
  );
}
