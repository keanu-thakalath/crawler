import { A } from "@solidjs/router";
import { For } from "solid-js";
import * as api from "~/api";
import PageItem from "~/components/PageItem";

interface SourceItemProps {
  source: api.SourceWithoutContent;
}

export default function SourceItem(props: SourceItemProps) {

  return (
    <li>
      <h5>
        <A href={`/source/${encodeURIComponent(props.source.url)}`}>
          {props.source.url}
        </A>
      </h5>
      <ul>
        <For each={props.source.pages}>
          {(page) => <PageItem page={page} />}
        </For>
      </ul>
    </li>
  );
}
