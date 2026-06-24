import { request } from "./http";

export type AuthProvider = "local" | "oidc" | (string & {});

export interface UserInfoDTO {
  username: string;
  email: string | null;
  created_at: string;
  notes_count: number;
  auth_provider: AuthProvider;
}

/** Fetch account details for the current authenticated user. */
export function getUserInfo(): Promise<UserInfoDTO> {
  return request<UserInfoDTO>("/settings/user-info", { method: "GET" });
}
