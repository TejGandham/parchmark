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

/** Personal API token metadata from `GET /auth/tokens`; never carries the plaintext. */
export interface ApiTokenDTO {
  id: number;
  name: string;
  created_at: string;
}

/** `POST /auth/tokens` response: metadata plus the plaintext, returned only this once. */
export interface ApiTokenCreatedDTO extends ApiTokenDTO {
  token: string;
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

/** List the current user's personal API tokens, newest first. */
export function listApiTokens(): Promise<ApiTokenDTO[]> {
  return request<ApiTokenDTO[]>("/auth/tokens", { method: "GET" });
}

/** Create a named personal API token; the response holds the plaintext once. */
export function createApiToken(name: string): Promise<ApiTokenCreatedDTO> {
  return request<ApiTokenCreatedDTO>("/auth/tokens", {
    method: "POST",
    body: { name },
  });
}

/** Revoke one of the current user's personal API tokens. */
export async function revokeApiToken(id: number): Promise<void> {
  await request<{ message: string; deleted_id: string }>(`/auth/tokens/${id}`, {
    method: "DELETE",
  });
}

/** Best-effort server-side logout; swallows any error. */
export async function logout(): Promise<void> {
  try {
    await request<{ message: string }>("/auth/logout", { method: "POST" });
  } catch {
    // Logout is best-effort: a failed call must never block the client.
  }
}
