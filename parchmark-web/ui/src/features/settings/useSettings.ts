import { ref } from "vue";

import { ApiError } from "../../services/http";
import {
  changePassword as changePasswordRequest,
  deleteAccount as deleteAccountRequest,
  exportNotes as exportNotesRequest,
  getUserInfo,
  type ExportNotesDownload,
  type MessageResponseDTO,
  type UserInfoDTO,
} from "../../services/settings";
import { useAuth } from "../auth/useAuth";

const userInfo = ref<UserInfoDTO | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);
const changingPassword = ref(false);
const passwordError = ref<string | null>(null);
const passwordSuccess = ref<string | null>(null);
const exportingNotes = ref(false);
const exportError = ref<string | null>(null);
const deletingAccount = ref(false);
const deleteError = ref<string | null>(null);

function errorDetail(caught: unknown): string {
  return caught instanceof ApiError ? caught.detail : String(caught);
}

export async function fetchUserInfo(): Promise<void> {
  loading.value = true;
  error.value = null;

  try {
    userInfo.value = await getUserInfo();
  } catch (caught) {
    error.value = errorDetail(caught);
  } finally {
    loading.value = false;
  }
}

export function clearSettingsError(): void {
  error.value = null;
}

export function clearPasswordStatus(): void {
  passwordError.value = null;
  passwordSuccess.value = null;
}

export function clearExportStatus(): void {
  exportError.value = null;
}

export function clearDeleteStatus(): void {
  deleteError.value = null;
}

export async function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<MessageResponseDTO> {
  changingPassword.value = true;
  clearPasswordStatus();

  try {
    const response = await changePasswordRequest({
      current_password: currentPassword,
      new_password: newPassword,
    });
    passwordSuccess.value = response.message;
    return response;
  } catch (caught) {
    passwordError.value = errorDetail(caught);
    throw caught;
  } finally {
    changingPassword.value = false;
  }
}

export async function exportNotes(): Promise<ExportNotesDownload> {
  exportingNotes.value = true;
  clearExportStatus();

  try {
    return await exportNotesRequest();
  } catch (caught) {
    exportError.value = errorDetail(caught);
    throw caught;
  } finally {
    exportingNotes.value = false;
  }
}

export async function deleteAccount(password: string): Promise<void> {
  deletingAccount.value = true;
  clearDeleteStatus();

  try {
    await deleteAccountRequest({ password });
    // Account is gone: clear the local session so App.vue returns to the login
    // gate. logout is best-effort and clears pm_auth even if the server call fails.
    await useAuth().logout();
  } catch (caught) {
    deleteError.value = errorDetail(caught);
    throw caught;
  } finally {
    deletingAccount.value = false;
  }
}

export function useSettings() {
  return {
    userInfo,
    loading,
    error,
    changingPassword,
    passwordError,
    passwordSuccess,
    exportingNotes,
    exportError,
    deletingAccount,
    deleteError,
    fetchUserInfo,
    clearSettingsError,
    clearPasswordStatus,
    clearExportStatus,
    clearDeleteStatus,
    changePassword,
    exportNotes,
    deleteAccount,
  };
}
