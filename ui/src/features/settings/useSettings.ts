import { ref } from "vue";

import { ApiError } from "../../services/http";
import { getUserInfo, type UserInfoDTO } from "../../services/settings";

const userInfo = ref<UserInfoDTO | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

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

export function useSettings() {
  return {
    userInfo,
    loading,
    error,
    fetchUserInfo,
    clearSettingsError,
  };
}
