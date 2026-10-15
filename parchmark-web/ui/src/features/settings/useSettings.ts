import { ref } from "vue";

import {
  createApiToken as createApiTokenRequest,
  listApiTokens,
  revokeApiToken as revokeApiTokenRequest,
  type ApiTokenCreatedDTO,
  type ApiTokenDTO,
} from "../../services/auth";
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
// Token metadata only: the plaintext of a new token is handed back to the
// caller and never kept in this module-level store.
const apiTokens = ref<ApiTokenDTO[]>([]);
const apiTokensLoading = ref(false);
const apiTokensError = ref<string | null>(null);
const creatingApiToken = ref(false);
const revokingApiTokenId = ref<number | null>(null);
const apiTokenActionError = ref<string | null>(null);

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

export async function fetchApiTokens(): Promise<void> {
  apiTokensLoading.value = true;
  apiTokensError.value = null;

  try {
    apiTokens.value = await listApiTokens();
  } catch (caught) {
    apiTokensError.value = errorDetail(caught);
  } finally {
    apiTokensLoading.value = false;
  }
}

export async function createApiToken(
  name: string,
): Promise<ApiTokenCreatedDTO> {
  creatingApiToken.value = true;
  apiTokenActionError.value = null;

  try {
    const created = await createApiTokenRequest(name);
    const { id, created_at } = created;
    apiTokens.value = [
      { id, name: created.name, created_at },
      ...apiTokens.value,
    ];
    return created;
  } catch (caught) {
    apiTokenActionError.value = errorDetail(caught);
    throw caught;
  } finally {
    creatingApiToken.value = false;
  }
}

export async function revokeApiToken(id: number): Promise<void> {
  revokingApiTokenId.value = id;
  apiTokenActionError.value = null;

  try {
    await revokeApiTokenRequest(id);
    apiTokens.value = apiTokens.value.filter((token) => token.id !== id);
  } catch (caught) {
    apiTokenActionError.value = errorDetail(caught);
    throw caught;
  } finally {
    revokingApiTokenId.value = null;
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
    apiTokens,
    apiTokensLoading,
    apiTokensError,
    creatingApiToken,
    revokingApiTokenId,
    apiTokenActionError,
    fetchUserInfo,
    fetchApiTokens,
    createApiToken,
    revokeApiToken,
    clearSettingsError,
    clearPasswordStatus,
    clearExportStatus,
    clearDeleteStatus,
    changePassword,
    exportNotes,
    deleteAccount,
  };
}
