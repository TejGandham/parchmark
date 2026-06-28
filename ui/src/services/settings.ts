import { request, requestRaw } from "./http";

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

export interface ExportNotesDownload {
  blob: Blob;
  filename: string;
}

const fallbackExportFilename = "parchmark_notes.zip";

function parseExportFilename(contentDisposition: string | null): string {
  if (!contentDisposition) {
    return fallbackExportFilename;
  }

  const encodedMatch = /filename\*=UTF-8''([^;]+)/i.exec(contentDisposition);
  if (encodedMatch?.[1]) {
    return decodeURIComponent(encodedMatch[1].replace(/^"|"$/g, ""));
  }

  const filenameMatch = /filename="?([^";]+)"?/i.exec(contentDisposition);
  return filenameMatch?.[1] ?? fallbackExportFilename;
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

/** Download all notes for the current authenticated user as a ZIP Blob. */
export async function exportNotes(): Promise<ExportNotesDownload> {
  const response = await requestRaw("/settings/export-notes", {
    method: "GET",
  });

  return {
    blob: await response.blob(),
    filename: parseExportFilename(response.headers.get("Content-Disposition")),
  };
}
