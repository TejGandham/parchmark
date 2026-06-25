import { ref } from "vue";

import { ApiError } from "../../services/http";
import {
  changePassword as changePasswordRequest,
  exportNotes as exportNotesRequest,
  getUserInfo,
  type ExportNotesDownload,
  type MessageResponseDTO,
  type UserInfoDTO,
} from "../../services/settings";

const userInfo = ref<UserInfoDTO | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);
const changingPassword = ref(false);
const passwordError = ref<string | null>(null);
const passwordSuccess = ref<string | null>(null);
const exportingNotes = ref(false);
const exportError = ref<string | null>(null);

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
    fetchUserInfo,
    clearSettingsError,
    clearPasswordStatus,
    clearExportStatus,
    changePassword,
    exportNotes,
  };
}
