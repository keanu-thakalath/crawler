import { Suspense } from "solid-js";
import { Router, A } from "@solidjs/router";
import { FileRoutes } from "@solidjs/start/router";

function Layout(props: any) {
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
        {props.children}
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
