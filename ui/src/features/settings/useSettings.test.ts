import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../services/settings", () => ({
  changePassword: vi.fn(),
  getUserInfo: vi.fn(),
}));

import { ApiError } from "../../services/http";
import {
  changePassword,
  getUserInfo,
  type UserInfoDTO,
} from "../../services/settings";

import { useSettings } from "./useSettings";

const getUserInfoMock = vi.mocked(getUserInfo);
const changePasswordMock = vi.mocked(changePassword);

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
    const {
      userInfo,
      loading,
      error,
      changingPassword,
      passwordError,
      passwordSuccess,
    } = useSettings();
    userInfo.value = null;
    loading.value = false;
    error.value = null;
    changingPassword.value = false;
    passwordError.value = null;
    passwordSuccess.value = null;
    getUserInfoMock.mockReset();
    changePasswordMock.mockReset();
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
    expect(a.changingPassword).toBe(b.changingPassword);
    expect(a.passwordError).toBe(b.passwordError);
    expect(a.passwordSuccess).toBe(b.passwordSuccess);
    expect(a.fetchUserInfo).toBe(b.fetchUserInfo);
    expect(a.clearSettingsError).toBe(b.clearSettingsError);
    expect(a.clearPasswordStatus).toBe(b.clearPasswordStatus);
    expect(a.changePassword).toBe(b.changePassword);
  });

  it("changePassword posts the supplied passwords and records the success message", async () => {
    const { passwordSuccess } = useSettings();
    changePasswordMock.mockResolvedValue({
      message: "Password changed successfully",
    });

    await useSettings().changePassword("oldpass123", "newpass456");

    expect(changePasswordMock).toHaveBeenCalledWith({
      current_password: "oldpass123",
      new_password: "newpass456",
    });
    expect(passwordSuccess.value).toBe("Password changed successfully");
  });

  it("changePassword toggles changingPassword during the request", async () => {
    const { changingPassword } = useSettings();
    let resolveChange!: (value: { message: string }) => void;
    changePasswordMock.mockReturnValue(
      new Promise<{ message: string }>((resolve) => {
        resolveChange = resolve;
      }),
    );

    const pending = useSettings().changePassword("oldpass123", "newpass456");
    expect(changingPassword.value).toBe(true);

    resolveChange({ message: "Password changed successfully" });
    await pending;

    expect(changingPassword.value).toBe(false);
  });

  it("on changePassword rejection, passwordError is set and success is cleared", async () => {
    const { passwordError, passwordSuccess } = useSettings();
    passwordSuccess.value = "stale success";
    changePasswordMock.mockRejectedValue(
      new ApiError(401, "Current password is incorrect"),
    );

    await expect(
      useSettings().changePassword("wrongpass", "newpass456"),
    ).rejects.toBeInstanceOf(ApiError);

    expect(passwordError.value).toBe("Current password is incorrect");
    expect(passwordSuccess.value).toBeNull();
  });

  it("clearPasswordStatus clears password mutation messages", () => {
    const { passwordError, passwordSuccess, clearPasswordStatus } =
      useSettings();
    passwordError.value = "stale error";
    passwordSuccess.value = "stale success";

    clearPasswordStatus();

    expect(passwordError.value).toBeNull();
    expect(passwordSuccess.value).toBeNull();
  });
});
