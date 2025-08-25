import { type Job } from "~/api";

interface TaskStatusProps {
  job: Job;
}

export default function TaskStatus(props: TaskStatusProps) {
  const getStatusColor = (hasOutcome: boolean) => {
    if (hasOutcome) {
      return { backgroundColor: "#d4edda", color: "#19a239ff" };
    } else {
      return { backgroundColor: "#fff3cd", color: "#bb8e06ff" };
    }
  };

  const getStatusText = (job: Job) => {
    return job.outcome ? "COMPLETED" : "RUNNING";
  };

  return (
    <span
      style={{
        "margin-left": "8px",
        padding: "2px 6px",
        "border-radius": "4px",
        ...getStatusColor(!!props.job.outcome),
      }}
    >
      {getStatusText(props.job)}
    </span>
  );
}
