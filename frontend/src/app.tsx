import { Show, Suspense } from "solid-js";
import { Router, A, createAsync } from "@solidjs/router";
import { FileRoutes } from "@solidjs/start/router";
import AuthForm, { getAuthToken } from "./components/AuthForm";

function Layout(props: any) {
  const auth_token = createAsync(() => getAuthToken(), { deferStream: true });

  return (
    <main>
      <nav>
        <ul>
          <li>
            <A href="/">Home</A>
          </li>
        </ul>
      </nav>
      <Show when={auth_token()} fallback={<AuthForm />}>
        <Suspense fallback={<section aria-busy="true">Loading...</section>}>
          {props.children}
        </Suspense>
      </Show>
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
