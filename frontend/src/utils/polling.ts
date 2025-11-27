import { revalidate } from "@solidjs/router";
import { onMount, onCleanup } from "solid-js";

export function usePolling(queryKey: string, interval: number = 10000) {
  onMount(() => {
    const intervalId = setInterval(() => {
      revalidate(queryKey);
    }, interval);

    onCleanup(() => clearInterval(intervalId));
  });
}
