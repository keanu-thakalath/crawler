import { A } from "@solidjs/router";
import type { PageWithoutSource } from "~/api";

interface PageItemProps {
  page: PageWithoutSource;
}

export default function PageItem(props: PageItemProps) {
  return (
    <li>
      <A href={`/page/${encodeURIComponent(props.page.url)}`}>
        {props.page.url}
      </A>
    </li>
  );
}
