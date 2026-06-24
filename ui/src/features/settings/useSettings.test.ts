import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../services/settings", () => ({
  getUserInfo: vi.fn(),
}));

import { ApiError } from "../../services/http";
import { getUserInfo, type UserInfoDTO } from "../../services/settings";

import { useSettings } from "./useSettings";

const getUserInfoMock = vi.mocked(getUserInfo);

function dto(overrides: Partial<UserInfoDTO> = {}): UserInfoDTO {
  return {
    username: "ada",
    email: "ada@example.com",
    created_at: "2024-01-15T10:30:00.000Z",
    notes_count: 7,
    auth_provider: "local",
    ...overrides,
  };
}

describe("useSettings", () => {
  beforeEach(() => {
    const { userInfo, loading, error } = useSettings();
    userInfo.value = null;
    loading.value = false;
    error.value = null;
    getUserInfoMock.mockReset();
  });

  it("fetchUserInfo stores the returned account details", async () => {
    getUserInfoMock.mockResolvedValue(dto({ auth_provider: "oidc" }));

    await useSettings().fetchUserInfo();

    expect(getUserInfoMock).toHaveBeenCalledOnce();
    expect(useSettings().userInfo.value).toEqual(
      dto({ auth_provider: "oidc" }),
    );
  });

  it("fetchUserInfo toggles loading true during the call and false after success", async () => {
    const { loading } = useSettings();
    let resolveInfo!: (value: UserInfoDTO) => void;
    getUserInfoMock.mockReturnValue(
      new Promise<UserInfoDTO>((resolve) => {
        resolveInfo = resolve;
      }),
    );

    const pending = useSettings().fetchUserInfo();
    expect(loading.value).toBe(true);

    resolveInfo(dto());
    await pending;

    expect(loading.value).toBe(false);
  });

  it("on getUserInfo rejection, error is set to ApiError.detail and prior data is left unchanged", async () => {
    const { userInfo, error } = useSettings();
    userInfo.value = dto({ username: "seed" });
    getUserInfoMock.mockRejectedValue(new ApiError(500, "account failed"));

    await useSettings().fetchUserInfo();

    expect(error.value).toBe("account failed");
    expect(userInfo.value).toEqual(dto({ username: "seed" }));
  });

  it("clearSettingsError clears the current error", () => {
    const { error, clearSettingsError } = useSettings();
    error.value = "stale";

    clearSettingsError();

    expect(error.value).toBeNull();
  });

  it("useSettings returns the same refs across calls", () => {
    const a = useSettings();
    const b = useSettings();

    expect(a.userInfo).toBe(b.userInfo);
    expect(a.loading).toBe(b.loading);
    expect(a.error).toBe(b.error);
    expect(a.fetchUserInfo).toBe(b.fetchUserInfo);
    expect(a.clearSettingsError).toBe(b.clearSettingsError);
  });
});
