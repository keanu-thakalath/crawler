import { Show, Suspense } from "solid-js";
import { Router, A, createAsync } from "@solidjs/router";
import { FileRoutes } from "@solidjs/start/router";
import AuthForm, { getAuthToken } from "./components/AuthForm";

function Layout(props: any) {
  const auth_token = createAsync(() => getAuthToken());
  return (
    <main>
      <nav>
        <ul>
          <li>
            <A href="/">Home</A>
          </li>
        </ul>
      </nav>
      <Suspense fallback={<section aria-busy="true">Loading...</section>}>
        <Show when={auth_token()} fallback={<AuthForm />}>
          {props.children}
        </Show>
      </Suspense>
    </main>
  );
}

export default function App() {
  return (
    <Router root={Layout}>
      <FileRoutes />
    </Router>
  );
}
