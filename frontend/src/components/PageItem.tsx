import { A } from "@solidjs/router";
import { type Page } from "~/api";

interface PageItemProps {
  page: Page;
}

export default function PageItem(props: PageItemProps) {
  const getPageStatus = () => {
    const hasJobs = props.page.jobs.length > 0;
    if (!hasJobs) return "";
    
    const hasRunningJobs = props.page.jobs.some(job => !job.outcome);
    const allJobsComplete = props.page.jobs.every(job => job.outcome);
    
    if (hasRunningJobs) return " (Processing)";
    if (allJobsComplete) return " (Completed)";
    return " (Pending)";
  };

  return (
    <li>
      <A href={`/page/${encodeURIComponent(props.page.url)}`}>
        {props.page.url}
      </A>
      <span style={{ color: "#666", "font-size": "0.9em" }}>
        {getPageStatus()}
      </span>
    </li>
  );
}
