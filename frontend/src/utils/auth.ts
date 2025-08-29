import { useSession } from "vinxi/http";
import { exchangeKey } from "~/api";

type AuthToken = {
  token?: string;
};

async function useAuthSession() {
  "use server";
  const session = await useSession<AuthToken>({
    password: process.env.SESSION_SECRET as string,
    name: "authToken",
  });

  return session;
}

export async function getAuthToken() {
  "use server";
  const session = await useAuthSession();

  return session.data.token;
}

export async function setAuthToken(key: string) {
  "use server";
  const session = await useAuthSession();
  const tokenResponse = await exchangeKey(key);
  if (tokenResponse) {
    await session.update(tokenResponse);
  }
  return tokenResponse;
}
