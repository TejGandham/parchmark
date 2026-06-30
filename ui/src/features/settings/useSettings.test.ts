import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../services/settings", () => ({
  changePassword: vi.fn(),
  deleteAccount: vi.fn(),
  exportNotes: vi.fn(),
  getUserInfo: vi.fn(),
}));

const { logoutMock } = vi.hoisted(() => ({ logoutMock: vi.fn() }));
vi.mock("../auth/useAuth", () => ({
  useAuth: () => ({ logout: logoutMock }),
}));

import { ApiError } from "../../services/http";
import {
  changePassword,
  deleteAccount,
  exportNotes,
  getUserInfo,
  type ExportNotesDownload,
  type UserInfoDTO,
} from "../../services/settings";

import { useSettings } from "./useSettings";

const getUserInfoMock = vi.mocked(getUserInfo);
const changePasswordMock = vi.mocked(changePassword);
const exportNotesMock = vi.mocked(exportNotes);
const deleteAccountMock = vi.mocked(deleteAccount);

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
      exportingNotes,
      exportError,
      deletingAccount,
      deleteError,
    } = useSettings();
    userInfo.value = null;
    loading.value = false;
    error.value = null;
    changingPassword.value = false;
    passwordError.value = null;
    passwordSuccess.value = null;
    exportingNotes.value = false;
    exportError.value = null;
    deletingAccount.value = false;
    deleteError.value = null;
    getUserInfoMock.mockReset();
    changePasswordMock.mockReset();
    exportNotesMock.mockReset();
    deleteAccountMock.mockReset();
    logoutMock.mockReset();
    logoutMock.mockResolvedValue(undefined);
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
    expect(a.exportingNotes).toBe(b.exportingNotes);
    expect(a.exportError).toBe(b.exportError);
    expect(a.deletingAccount).toBe(b.deletingAccount);
    expect(a.deleteError).toBe(b.deleteError);
    expect(a.fetchUserInfo).toBe(b.fetchUserInfo);
    expect(a.clearSettingsError).toBe(b.clearSettingsError);
    expect(a.clearPasswordStatus).toBe(b.clearPasswordStatus);
    expect(a.clearExportStatus).toBe(b.clearExportStatus);
    expect(a.clearDeleteStatus).toBe(b.clearDeleteStatus);
    expect(a.changePassword).toBe(b.changePassword);
    expect(a.exportNotes).toBe(b.exportNotes);
    expect(a.deleteAccount).toBe(b.deleteAccount);
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

  it("exportNotes returns the download payload and clears stale export errors", async () => {
    const { exportError } = useSettings();
    const download: ExportNotesDownload = {
      blob: new Blob(["zip"], { type: "application/zip" }),
      filename: "parchmark_notes.zip",
    };
    exportError.value = "stale error";
    exportNotesMock.mockResolvedValue(download);

    await expect(useSettings().exportNotes()).resolves.toBe(download);

    expect(exportNotesMock).toHaveBeenCalledOnce();
    expect(exportError.value).toBeNull();
  });

  it("exportNotes toggles exportingNotes during the request", async () => {
    const { exportingNotes } = useSettings();
    let resolveExport!: (value: ExportNotesDownload) => void;
    exportNotesMock.mockReturnValue(
      new Promise<ExportNotesDownload>((resolve) => {
        resolveExport = resolve;
      }),
    );

    const pending = useSettings().exportNotes();
    expect(exportingNotes.value).toBe(true);

    resolveExport({
      blob: new Blob(["zip"], { type: "application/zip" }),
      filename: "parchmark_notes.zip",
    });
    await pending;

    expect(exportingNotes.value).toBe(false);
  });

  it("on exportNotes rejection, exportError is set to ApiError.detail", async () => {
    const { exportError } = useSettings();
    exportNotesMock.mockRejectedValue(new ApiError(500, "export failed"));

    await expect(useSettings().exportNotes()).rejects.toBeInstanceOf(ApiError);

    expect(exportError.value).toBe("export failed");
  });

  it("clearExportStatus clears the current export error", () => {
    const { exportError, clearExportStatus } = useSettings();
    exportError.value = "stale";

    clearExportStatus();

    expect(exportError.value).toBeNull();
  });

  it("deleteAccount sends the password then clears the session via logout", async () => {
    const { deleteError } = useSettings();
    deleteError.value = "stale error";
    deleteAccountMock.mockResolvedValue({ message: "Account deleted" });

    await useSettings().deleteAccount("confirm pass");

    expect(deleteAccountMock).toHaveBeenCalledWith({
      password: "confirm pass",
    });
    expect(logoutMock).toHaveBeenCalledOnce();
    expect(deleteError.value).toBeNull();
  });

  it("deleteAccount toggles deletingAccount during the request", async () => {
    const { deletingAccount } = useSettings();
    let resolveDelete!: (value: { message: string }) => void;
    deleteAccountMock.mockReturnValue(
      new Promise<{ message: string }>((resolve) => {
        resolveDelete = resolve;
      }),
    );

    const pending = useSettings().deleteAccount("confirm pass");
    expect(deletingAccount.value).toBe(true);

    resolveDelete({ message: "Account deleted" });
    await pending;

    expect(deletingAccount.value).toBe(false);
  });

  it("on deleteAccount rejection, deleteError is set and logout is not called", async () => {
    const { deleteError } = useSettings();
    deleteAccountMock.mockRejectedValue(
      new ApiError(401, "Password is incorrect"),
    );

    await expect(useSettings().deleteAccount("wrong")).rejects.toBeInstanceOf(
      ApiError,
    );

    expect(deleteError.value).toBe("Password is incorrect");
    expect(logoutMock).not.toHaveBeenCalled();
  });

  it("clearDeleteStatus clears the current delete error", () => {
    const { deleteError, clearDeleteStatus } = useSettings();
    deleteError.value = "stale";

    clearDeleteStatus();

    expect(deleteError.value).toBeNull();
  });
});
