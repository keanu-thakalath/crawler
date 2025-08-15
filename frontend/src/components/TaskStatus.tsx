import { createAsync, query } from "@solidjs/router";
import * as api from "~/api";
import { usePolling } from "~/utils/polling";

interface TaskStatusProps {
  taskId: string;
}

const getTaskStatus = query(async (taskId: string) => {
  return await api.getTaskStatus(taskId);
}, "taskStatus");

export default function TaskStatus(props: TaskStatusProps) {
  const taskStatus = createAsync(() => getTaskStatus(props.taskId));

  usePolling(getTaskStatus.keyFor(props.taskId));

  const getStatusColor = (status: string) => {
    switch (status) {
      case "SUCCESS":
        return { backgroundColor: "#d4edda", color: "#19a239ff" };
      case "RUNNING":
        return { backgroundColor: "#fff3cd", color: "#bb8e06ff" };
      default:
        return { backgroundColor: "#f8d7da", color: "#b11f2dff" };
    }
  };

  return (
    <span
      style={{
        "margin-left": "8px",
        padding: "2px 6px",
        "border-radius": "4px",
        ...getStatusColor(taskStatus()?.status || "UNKNOWN"),
      }}
    >
      {taskStatus()?.status || "UNKNOWN"}
    </span>
  );
}
