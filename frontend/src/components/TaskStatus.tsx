import {
  type Job,
  type ExtractJobOutcome,
  type SummarizeJobOutcome,
  type JobError,
} from "~/api";

interface TaskStatusProps {
  job: Job;
}

export default function TaskStatus(props: TaskStatusProps) {
  const getStatusColor = (job: Job) => {
    if (!job.outcome) {
      return { backgroundColor: "#fff3cd", color: "#bb8e06ff" };
    }
    if ("message" in job.outcome) {
      return { backgroundColor: "#f8d7da", color: "#721c24" };
    }
    return { backgroundColor: "#d4edda", color: "#19a239ff" };
  };

  const getReviewStatusColor = (reviewStatus: string) => {
    if (reviewStatus === "Approved") {
      return { backgroundColor: "#d1ecf1", color: "#0c5460" };
    } else {
      return { backgroundColor: "#f8d7da", color: "#721c24" };
    }
  };

  const getStatusText = (job: Job) => {
    if (!job.outcome) {
      return "RUNNING";
    }
    if ("message" in job.outcome) {
      return "ERROR";
    }
    return "COMPLETED";
  };

  const hasReviewStatus = (
    outcome: any
  ): outcome is ExtractJobOutcome | SummarizeJobOutcome => {
    return outcome && "review_status" in outcome;
  };

  return (
    <span style={{ "margin-left": "8px" }}>
      <span
        style={{
          padding: "2px 6px",
          "border-radius": "4px",
          ...getStatusColor(props.job),
        }}
      >
        {getStatusText(props.job)}
      </span>
      {props.job.outcome && hasReviewStatus(props.job.outcome) && (
        <span
          style={{
            "margin-left": "4px",
            padding: "2px 6px",
            "border-radius": "4px",
            ...getReviewStatusColor(props.job.outcome.review_status),
          }}
        >
          {props.job.outcome.review_status.toUpperCase()}
        </span>
      )}
    </span>
  );
}
