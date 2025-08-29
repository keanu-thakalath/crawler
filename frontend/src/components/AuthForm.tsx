import { action, query, revalidate, useSubmission } from "@solidjs/router";
import { Show } from "solid-js";
import * as auth from "~/utils/auth";

export const getAuthToken = query(async () => {
  return await auth.getAuthToken();
}, "authToken");

const setAuthTokenAction = action(async (formData: FormData) => {
  const key = formData.get("key") as string;
  if (!key) throw new Error("Auth key is required");
  const tokenResponse = await auth.setAuthToken(key);
  if (!tokenResponse) throw new Error("Invalid key");
  await revalidate(getAuthToken.key);
  return {};
}, "setAuthToken");

export default function AuthForm() {
  const setAuthTokenSubmission = useSubmission(setAuthTokenAction);

  return (
    <section>
      <h2>Authentication Required</h2>
      <p>Please enter your authentication key to continue.</p>

      <form action={setAuthTokenAction} method="post">
        <fieldset
          role="group"
          aria-invalid={
            setAuthTokenSubmission.error && !!setAuthTokenSubmission.error
          }
        >
          <input
            type="password"
            placeholder="Enter auth key"
            name="key"
            aria-invalid={
              setAuthTokenSubmission.error && !!setAuthTokenSubmission.error
            }
          />
          <input type="submit" aria-busy={setAuthTokenSubmission.pending}>
            Set Token
          </input>
        </fieldset>

        <Show when={setAuthTokenSubmission.error}>
          <small>{setAuthTokenSubmission.error.message}</small>{" "}
        </Show>
      </form>
    </section>
  );
}
