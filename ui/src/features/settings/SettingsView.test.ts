import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../services/settings", () => ({
  changePassword: vi.fn(),
  exportNotes: vi.fn(),
  getUserInfo: vi.fn(),
}));

import { ApiError } from "../../services/http";
import {
  changePassword,
  exportNotes,
  getUserInfo,
  type ExportNotesDownload,
  type UserInfoDTO,
} from "../../services/settings";

import SettingsView from "./SettingsView.vue";
import { useSettings } from "./useSettings";

const getUserInfoMock = vi.mocked(getUserInfo);
const changePasswordMock = vi.mocked(changePassword);
const exportNotesMock = vi.mocked(exportNotes);

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

describe("SettingsView", () => {
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
    } = useSettings();
    userInfo.value = null;
    loading.value = false;
    error.value = null;
    changingPassword.value = false;
    passwordError.value = null;
    passwordSuccess.value = null;
    exportingNotes.value = false;
    exportError.value = null;
    getUserInfoMock.mockReset();
    changePasswordMock.mockReset();
    exportNotesMock.mockReset();
  });

  it("fetches account info on mount and renders returned facts", async () => {
    getUserInfoMock.mockResolvedValue(dto());

    const wrapper = mount(SettingsView);
    await flushPromises();

    expect(getUserInfoMock).toHaveBeenCalledOnce();
    expect(wrapper.text()).toContain("Settings");
    expect(wrapper.text()).toContain("ada");
    expect(wrapper.text()).toContain("ada@example.com");
    expect(wrapper.text()).toContain("7");
    expect(wrapper.text()).toContain("Local password");
    expect(wrapper.text()).toContain("Jan 15, 2024");
  });

  it("omits the email row when the backend returns no email", async () => {
    getUserInfoMock.mockResolvedValue(dto({ email: null }));

    const wrapper = mount(SettingsView);
    await flushPromises();

    expect(wrapper.text()).not.toContain("Email");
    expect(wrapper.text()).not.toContain("ada@example.com");
  });

  it("shows loading state while the request is pending", async () => {
    getUserInfoMock.mockReturnValue(new Promise<UserInfoDTO>(() => {}));

    const wrapper = mount(SettingsView);
    await flushPromises();

    expect(wrapper.get('[role="status"]').text()).toContain(
      "Loading account details",
    );
  });

  it("shows API errors and retries the fetch", async () => {
    getUserInfoMock
      .mockRejectedValueOnce(new Error("network down"))
      .mockResolvedValueOnce(dto({ username: "grace", auth_provider: "oidc" }));

    const wrapper = mount(SettingsView);
    await flushPromises();

    expect(wrapper.get('[role="alert"]').text()).toContain("network down");

    await wrapper.get("button").trigger("click");
    await flushPromises();

    expect(getUserInfoMock).toHaveBeenCalledTimes(2);
    expect(wrapper.text()).toContain("grace");
    expect(wrapper.text()).toContain("OIDC");
  });

  it("renders a local-account password form and submits typed passwords", async () => {
    getUserInfoMock.mockResolvedValue(dto({ auth_provider: "local" }));
    changePasswordMock.mockResolvedValue({
      message: "Password changed successfully",
    });

    const wrapper = mount(SettingsView);
    await flushPromises();

    await wrapper
      .get('input[name="current-password"]')
      .setValue("old pass typed");
    await wrapper.get('input[name="new-password"]').setValue("new pass typed");
    await wrapper
      .get('input[name="confirm-new-password"]')
      .setValue("new pass typed");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(changePasswordMock).toHaveBeenCalledWith({
      current_password: "old pass typed",
      new_password: "new pass typed",
    });
    expect(wrapper.text()).toContain("Password changed successfully");
    expect(
      (
        wrapper.get('input[name="current-password"]')
          .element as HTMLInputElement
      ).value,
    ).toBe("");
    expect(
      (wrapper.get('input[name="new-password"]').element as HTMLInputElement)
        .value,
    ).toBe("");
  });

  it("downloads the exported ZIP through a temporary object URL", async () => {
    getUserInfoMock.mockResolvedValue(dto({ auth_provider: "local" }));
    const download: ExportNotesDownload = {
      blob: new Blob(["zip-data"], { type: "application/zip" }),
      filename: "parchmark_notes_20260625_120000.zip",
    };
    exportNotesMock.mockResolvedValue(download);
    const createObjectURL = vi.fn().mockReturnValue("blob:notes-export");
    const revokeObjectURL = vi.fn();
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: createObjectURL,
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      value: revokeObjectURL,
    });
    const anchorClick = vi.fn();
    const originalCreateElement = document.createElement.bind(document);
    const createElementSpy = vi
      .spyOn(document, "createElement")
      .mockImplementation((tagName, options) => {
        const element = originalCreateElement(tagName, options);
        if (String(tagName).toLowerCase() === "a") {
          Object.defineProperty(element, "click", {
            configurable: true,
            value: anchorClick,
          });
        }
        return element;
      });

    const wrapper = mount(SettingsView);
    await flushPromises();

    await wrapper.get("button.settings-view__action-button").trigger("click");
    await flushPromises();

    expect(exportNotesMock).toHaveBeenCalledOnce();
    expect(createObjectURL).toHaveBeenCalledWith(download.blob);
    expect(anchorClick).toHaveBeenCalledOnce();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:notes-export");
    expect(createElementSpy).toHaveBeenCalledWith("a");

    createElementSpy.mockRestore();
  });

  it("disables the export button while the download is pending", async () => {
    getUserInfoMock.mockResolvedValue(dto({ auth_provider: "local" }));
    exportNotesMock.mockReturnValue(new Promise<ExportNotesDownload>(() => {}));

    const wrapper = mount(SettingsView);
    await flushPromises();

    await wrapper.get("button.settings-view__action-button").trigger("click");
    await flushPromises();

    const button = wrapper.get("button.settings-view__action-button");
    expect(button.attributes("disabled")).toBeDefined();
    expect(button.text()).toContain("Preparing download");
  });

  it("shows export errors inline without clearing account details", async () => {
    getUserInfoMock.mockResolvedValue(dto({ auth_provider: "local" }));
    exportNotesMock.mockRejectedValue(new ApiError(500, "export failed"));

    const wrapper = mount(SettingsView);
    await flushPromises();

    await wrapper.get("button.settings-view__action-button").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("ada");
    expect(wrapper.get('[role="alert"]').text()).toContain("export failed");
  });

  it("blocks mismatched confirmation before calling the API", async () => {
    getUserInfoMock.mockResolvedValue(dto({ auth_provider: "local" }));

    const wrapper = mount(SettingsView);
    await flushPromises();

    await wrapper.get('input[name="current-password"]').setValue("oldpass123");
    await wrapper.get('input[name="new-password"]').setValue("newpass456");
    await wrapper
      .get('input[name="confirm-new-password"]')
      .setValue("different456");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(changePasswordMock).not.toHaveBeenCalled();
    expect(wrapper.get('[role="alert"]').text()).toContain(
      "New password and confirmation must match",
    );
  });

  it("shows backend password-change errors without clearing account details or fields", async () => {
    getUserInfoMock.mockResolvedValue(dto({ auth_provider: "local" }));
    changePasswordMock.mockRejectedValue(
      new ApiError(401, "Current password is incorrect"),
    );

    const wrapper = mount(SettingsView);
    await flushPromises();

    await wrapper.get('input[name="current-password"]').setValue("wrongpass");
    await wrapper.get('input[name="new-password"]').setValue("newpass456");
    await wrapper
      .get('input[name="confirm-new-password"]')
      .setValue("newpass456");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(wrapper.text()).toContain("ada");
    expect(wrapper.get('[role="alert"]').text()).toContain(
      "Current password is incorrect",
    );
    expect(
      (
        wrapper.get('input[name="current-password"]')
          .element as HTMLInputElement
      ).value,
    ).toBe("wrongpass");
  });

  it("renders an identity-provider note and no password inputs for OIDC users", async () => {
    getUserInfoMock.mockResolvedValue(dto({ auth_provider: "oidc" }));

    const wrapper = mount(SettingsView);
    await flushPromises();

    expect(wrapper.text()).toContain("This account signs in through OIDC");
    expect(wrapper.find('input[type="password"]').exists()).toBe(false);
    expect(changePasswordMock).not.toHaveBeenCalled();
  });
});
