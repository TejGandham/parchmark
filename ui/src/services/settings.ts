import { request } from "./http";

export type AuthProvider = "local" | "oidc" | (string & {});

export interface UserInfoDTO {
  username: string;
  email: string | null;
  created_at: string;
  notes_count: number;
  auth_provider: AuthProvider;
}

export interface PasswordChangePayload {
  current_password: string;
  new_password: string;
}

export interface MessageResponseDTO {
  message: string;
}

/** Fetch account details for the current authenticated user. */
export function getUserInfo(): Promise<UserInfoDTO> {
  return request<UserInfoDTO>("/settings/user-info", { method: "GET" });
}

/** Change the current local-auth user's password. */
export function changePassword(
  payload: PasswordChangePayload,
): Promise<MessageResponseDTO> {
  return request<MessageResponseDTO>("/settings/change-password", {
    method: "POST",
    body: payload,
  });
}
