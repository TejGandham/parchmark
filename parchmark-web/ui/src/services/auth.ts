import { request } from "./http";

/** Token pair returned by the login and refresh endpoints. */
export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/** The authenticated user as reported by `GET /auth/me`. */
export interface CurrentUser {
  username: string;
}

/** Exchange credentials for a fresh token pair. */
export function login(username: string, password: string): Promise<TokenPair> {
  return request<TokenPair>("/auth/login", {
    method: "POST",
    body: { username, password },
  });
}

/** Exchange a refresh token for a new token pair. */
export function refreshToken(refresh_token: string): Promise<TokenPair> {
  return request<TokenPair>("/auth/refresh", {
    method: "POST",
    body: { refresh_token },
  });
}

/** Fetch the currently authenticated user. */
export function getCurrentUser(): Promise<CurrentUser> {
  return request<CurrentUser>("/auth/me", { method: "GET" });
}

/** Best-effort server-side logout; swallows any error. */
export async function logout(): Promise<void> {
  try {
    await request<{ message: string }>("/auth/logout", { method: "POST" });
  } catch {
    // Logout is best-effort: a failed call must never block the client.
  }
}
