import { createSignal, createEffect } from "solid-js";
import { action, revalidate, useSubmission } from "@solidjs/router";
import * as api from "~/api";

const approveJobAction = action(async (formData: FormData) => {
  const jobId = formData.get("jobId") as string;
  const summary = formData.get("summary") as string;
  
  if (!jobId) throw new Error("Job ID is required");
  if (!summary || !summary.trim()) throw new Error("Summary is required");

  // First update the summary, then approve the job
  await api.editJobSummary(jobId, summary);
  await api.approveJob(jobId);
  await revalidate("sources");
  return {};
}, "approveJob");

interface EditableSummaryProps {
  initialSummary: string;
  jobId: string;
}

export default function EditableSummary(props: EditableSummaryProps) {
  const [summary, setSummary] = createSignal("");
  const [initialized, setInitialized] = createSignal(false);
  const approveSubmission = useSubmission(approveJobAction);
  
  // Initialize the summary only once when the component receives data
  createEffect(() => {
    if (props.initialSummary && !initialized()) {
      setSummary(props.initialSummary);
      setInitialized(true);
    }
  });

  // Reset initialization after successful submission so it can pick up the next job
  createEffect(() => {
    if (approveSubmission.result && !approveSubmission.pending) {
      setInitialized(false);
    }
  });

  return (
    <form action={approveJobAction} method="post">
      <input type="hidden" name="jobId" value={props.jobId} />
      
      <div style={{ "margin-bottom": "16px" }}>
        <label for="summary" style={{ 
          display: "block", 
          "margin-bottom": "8px", 
          "font-weight": "bold" 
        }}>
          Summary (editable):
        </label>
        <textarea
          id="summary"
          name="summary"
          value={summary()}
          onInput={(e) => setSummary(e.target.value)}
          style={{
            width: "100%",
            "min-height": "120px",
            padding: "8px",
            "border-radius": "4px",
            border: "1px solid #ddd",
            "font-family": "inherit",
            "font-size": "14px"
          }}
          aria-invalid={approveSubmission.error && !!approveSubmission.error}
        />
      </div>

      <button
        type="submit"
        disabled={approveSubmission.pending || !summary().trim()}
        aria-busy={approveSubmission.pending}
        style={{
          padding: "10px 20px",
          "background-color": "#28a745",
          color: "white",
          border: "none",
          "border-radius": "4px",
          cursor: (approveSubmission.pending || !summary().trim()) ? "not-allowed" : "pointer",
          opacity: (approveSubmission.pending || !summary().trim()) ? "0.7" : "1"
        }}
      >
        {approveSubmission.pending ? "Approving..." : "Approve Job"}
      </button>

      {approveSubmission.error && (
        <div style={{ 
          "margin-top": "12px", 
          color: "#dc3545",
          "font-size": "14px"
        }}>
          Error: {approveSubmission.error.message}
        </div>
      )}
    </form>
  );
}