import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../services/settings", () => ({
  changePassword: vi.fn(),
  deleteAccount: vi.fn(),
  exportNotes: vi.fn(),
  getUserInfo: vi.fn(),
}));

vi.mock("../../services/auth", () => ({
  createApiToken: vi.fn(),
  listApiTokens: vi.fn(),
  revokeApiToken: vi.fn(),
}));

const { logoutMock } = vi.hoisted(() => ({ logoutMock: vi.fn() }));
vi.mock("../auth/useAuth", () => ({
  useAuth: () => ({ logout: logoutMock }),
}));

import {
  createApiToken,
  listApiTokens,
  revokeApiToken,
  type ApiTokenDTO,
} from "../../services/auth";
import { ApiError } from "../../services/http";
import {
  changePassword,
  deleteAccount,
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
const deleteAccountMock = vi.mocked(deleteAccount);
const listApiTokensMock = vi.mocked(listApiTokens);
const createApiTokenMock = vi.mocked(createApiToken);
const revokeApiTokenMock = vi.mocked(revokeApiToken);

function token(overrides: Partial<ApiTokenDTO> = {}): ApiTokenDTO {
  return {
    id: 1,
    name: "laptop",
    created_at: "2026-01-01T12:00:00.000Z",
    ...overrides,
  };
}

function buttonWithText(wrapper: VueWrapper, text: string) {
  const button = wrapper
    .findAll("button")
    .find((candidate) => candidate.text().includes(text));
  if (!button) throw new Error(`No button with text "${text}"`);
  return button;
}

function setClipboard(writeText: ((text: string) => Promise<void>) | null) {
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: writeText ? { writeText } : undefined,
  });
}

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
      deletingAccount,
      deleteError,
      apiTokens,
      apiTokensLoading,
      apiTokensError,
      creatingApiToken,
      revokingApiTokenId,
      apiTokenActionError,
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
    apiTokens.value = [];
    apiTokensLoading.value = false;
    apiTokensError.value = null;
    creatingApiToken.value = false;
    revokingApiTokenId.value = null;
    apiTokenActionError.value = null;
    listApiTokensMock.mockReset();
    listApiTokensMock.mockResolvedValue([]);
    createApiTokenMock.mockReset();
    revokeApiTokenMock.mockReset();
    setClipboard(null);
    getUserInfoMock.mockReset();
    changePasswordMock.mockReset();
    exportNotesMock.mockReset();
    deleteAccountMock.mockReset();
    logoutMock.mockReset();
    logoutMock.mockResolvedValue(undefined);
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

  it("renders raw creation dates and provider labels when the backend sends unknown values", async () => {
    getUserInfoMock.mockResolvedValue(
      dto({
        auth_provider: "saml",
        created_at: "not-a-real-date",
        email: null,
      }),
    );

    const wrapper = mount(SettingsView);
    await flushPromises();

    expect(wrapper.text()).toContain("not-a-real-date");
    expect(wrapper.text()).toContain("saml");
    expect(wrapper.text()).toContain("This account signs in through saml");
    expect(wrapper.find('input[type="password"]').exists()).toBe(false);
  });

  it("falls back to generic identity-provider copy when no provider label is available", async () => {
    getUserInfoMock.mockResolvedValue(dto({ auth_provider: "" }));

    const wrapper = mount(SettingsView);
    await flushPromises();

    expect(wrapper.text()).toContain(
      "This account signs in through your identity provider",
    );
    expect(wrapper.find('input[type="password"]').exists()).toBe(false);
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

  it("blocks too-short new passwords before calling the API", async () => {
    getUserInfoMock.mockResolvedValue(dto({ auth_provider: "local" }));

    const wrapper = mount(SettingsView);
    await flushPromises();

    await wrapper.get('input[name="current-password"]').setValue("oldpass123");
    await wrapper.get('input[name="new-password"]').setValue("abc");
    await wrapper.get('input[name="confirm-new-password"]').setValue("abc");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(changePasswordMock).not.toHaveBeenCalled();
    expect(wrapper.get('[role="alert"]').text()).toContain(
      "New password must be at least 4 characters",
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

  it("keeps the delete button disabled until a local user supplies password and confirmation", async () => {
    getUserInfoMock.mockResolvedValue(dto({ auth_provider: "local" }));

    const wrapper = mount(SettingsView);
    await flushPromises();

    const button = wrapper.get("button.settings-view__danger-button");
    expect(button.attributes("disabled")).toBeDefined();

    await wrapper.get('input[name="delete-password"]').setValue("oldpass123");
    expect(button.attributes("disabled")).toBeDefined();

    await wrapper.get('input[name="delete-confirm"]').setValue("DELETE");
    expect(button.attributes("disabled")).toBeUndefined();
  });

  it("keeps the delete button disabled until an OIDC user types the confirmation", async () => {
    getUserInfoMock.mockResolvedValue(dto({ auth_provider: "oidc" }));

    const wrapper = mount(SettingsView);
    await flushPromises();

    expect(wrapper.find('input[name="delete-password"]').exists()).toBe(false);
    const button = wrapper.get("button.settings-view__danger-button");
    expect(button.attributes("disabled")).toBeDefined();

    await wrapper.get('input[name="delete-confirm"]').setValue("nope");
    expect(button.attributes("disabled")).toBeDefined();

    await wrapper.get('input[name="delete-confirm"]').setValue("DELETE");
    expect(button.attributes("disabled")).toBeUndefined();
  });

  it("deletes the account with the password and clears the session via logout", async () => {
    getUserInfoMock.mockResolvedValue(dto({ auth_provider: "local" }));
    deleteAccountMock.mockResolvedValue({ message: "Account deleted" });

    const wrapper = mount(SettingsView);
    await flushPromises();

    await wrapper.get('input[name="delete-password"]').setValue("oldpass123");
    await wrapper.get('input[name="delete-confirm"]').setValue("DELETE");
    await wrapper.get("form.settings-view__danger-form").trigger("submit");
    await flushPromises();

    expect(deleteAccountMock).toHaveBeenCalledWith({ password: "oldpass123" });
    expect(logoutMock).toHaveBeenCalledOnce();
  });

  it("sends the typed confirmation as the password for accounts without a local password", async () => {
    getUserInfoMock.mockResolvedValue(dto({ auth_provider: "oidc" }));
    deleteAccountMock.mockResolvedValue({ message: "Account deleted" });

    const wrapper = mount(SettingsView);
    await flushPromises();

    await wrapper.get('input[name="delete-confirm"]').setValue("DELETE");
    await wrapper.get("form.settings-view__danger-form").trigger("submit");
    await flushPromises();

    expect(deleteAccountMock).toHaveBeenCalledWith({ password: "DELETE" });
    expect(logoutMock).toHaveBeenCalledOnce();
  });

  it("shows backend delete errors inline and preserves the session", async () => {
    getUserInfoMock.mockResolvedValue(dto({ auth_provider: "local" }));
    deleteAccountMock.mockRejectedValue(
      new ApiError(401, "Password is incorrect"),
    );

    const wrapper = mount(SettingsView);
    await flushPromises();

    await wrapper.get('input[name="delete-password"]').setValue("wrongpass");
    await wrapper.get('input[name="delete-confirm"]').setValue("DELETE");
    await wrapper.get("form.settings-view__danger-form").trigger("submit");
    await flushPromises();

    expect(
      wrapper
        .get("form.settings-view__danger-form")
        .get('[role="alert"]')
        .text(),
    ).toContain("Password is incorrect");
    expect(logoutMock).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain("ada");
  });

  it("renders the signed-in user's API tokens", async () => {
    getUserInfoMock.mockResolvedValue(dto());
    listApiTokensMock.mockResolvedValue([
      token({ id: 2, name: "ci runner" }),
      token(),
    ]);

    const wrapper = mount(SettingsView);
    await flushPromises();

    expect(listApiTokensMock).toHaveBeenCalledOnce();
    const rows = wrapper.findAll(".settings-view__token-row");
    expect(rows).toHaveLength(2);
    expect(rows[0].text()).toContain("ci runner");
    expect(rows[1].text()).toContain("laptop");
    expect(rows[1].text()).toContain("Created Jan 1, 2026");
    expect(wrapper.text()).not.toContain("No API tokens yet");
  });

  it("shows an empty state when the user has no API tokens", async () => {
    getUserInfoMock.mockResolvedValue(dto());

    const wrapper = mount(SettingsView);
    await flushPromises();

    expect(wrapper.text()).toContain("No API tokens yet");
    expect(wrapper.find(".settings-view__token-list").exists()).toBe(false);
  });

  it("shows token list errors and retries the fetch", async () => {
    getUserInfoMock.mockResolvedValue(dto());
    listApiTokensMock
      .mockRejectedValueOnce(new ApiError(500, "tokens unavailable"))
      .mockResolvedValueOnce([token()]);

    const wrapper = mount(SettingsView);
    await flushPromises();

    const tokens = wrapper.get(".settings-view__tokens");
    expect(tokens.get('[role="alert"]').text()).toContain("tokens unavailable");

    await buttonWithText(wrapper, "Retry").trigger("click");
    await flushPromises();

    expect(listApiTokensMock).toHaveBeenCalledTimes(2);
    expect(wrapper.find(".settings-view__token-row").text()).toContain(
      "laptop",
    );
  });

  it("keeps the create button disabled until a token name is typed", async () => {
    getUserInfoMock.mockResolvedValue(dto());

    const wrapper = mount(SettingsView);
    await flushPromises();

    const button = wrapper.get("form.settings-view__token-form button");
    expect(button.attributes("disabled")).toBeDefined();

    await wrapper.get('input[name="token-name"]').setValue("   ");
    expect(button.attributes("disabled")).toBeDefined();

    await wrapper.get('input[name="token-name"]').setValue("laptop");
    expect(button.attributes("disabled")).toBeUndefined();
  });

  it("creates a token through the API client and shows the plaintext until dismissed", async () => {
    getUserInfoMock.mockResolvedValue(dto());
    createApiTokenMock.mockResolvedValue({
      ...token({ id: 5, name: "laptop" }),
      token: "pm_secret_plaintext",
    });

    const wrapper = mount(SettingsView);
    await flushPromises();

    await wrapper.get('input[name="token-name"]').setValue("  laptop  ");
    await wrapper.get("form.settings-view__token-form").trigger("submit");
    await flushPromises();

    expect(createApiTokenMock).toHaveBeenCalledWith("laptop");
    expect(wrapper.get(".settings-view__token-value").text()).toBe(
      "pm_secret_plaintext",
    );
    expect(wrapper.text()).toContain("You won't be able to see it again");
    expect(wrapper.find(".settings-view__token-row").text()).toContain(
      "laptop",
    );
    expect(
      (wrapper.get('input[name="token-name"]').element as HTMLInputElement)
        .value,
    ).toBe("");

    await buttonWithText(wrapper, "Done").trigger("click");

    expect(wrapper.find(".settings-view__token-value").exists()).toBe(false);
    expect(wrapper.text()).not.toContain("pm_secret_plaintext");
  });

  it("does not show the plaintext again after Settings is reopened", async () => {
    getUserInfoMock.mockResolvedValue(dto());
    createApiTokenMock.mockResolvedValue({
      ...token({ id: 5 }),
      token: "pm_secret_plaintext",
    });

    const first = mount(SettingsView);
    await flushPromises();
    await first.get('input[name="token-name"]').setValue("laptop");
    await first.get("form.settings-view__token-form").trigger("submit");
    await flushPromises();
    expect(first.text()).toContain("pm_secret_plaintext");
    first.unmount();

    listApiTokensMock.mockResolvedValue([token({ id: 5 })]);
    const second = mount(SettingsView);
    await flushPromises();

    expect(second.find(".settings-view__token-row").text()).toContain("laptop");
    expect(second.text()).not.toContain("pm_secret_plaintext");
  });

  it("copies the new token to the clipboard", async () => {
    getUserInfoMock.mockResolvedValue(dto());
    createApiTokenMock.mockResolvedValue({
      ...token(),
      token: "pm_secret_plaintext",
    });
    const writeText = vi.fn().mockResolvedValue(undefined);
    setClipboard(writeText);

    const wrapper = mount(SettingsView);
    await flushPromises();
    await wrapper.get('input[name="token-name"]').setValue("laptop");
    await wrapper.get("form.settings-view__token-form").trigger("submit");
    await flushPromises();

    await buttonWithText(wrapper, "Copy token").trigger("click");
    await flushPromises();

    expect(writeText).toHaveBeenCalledWith("pm_secret_plaintext");
    expect(
      wrapper.get('.settings-view__new-token [role="status"]').text(),
    ).toContain("Copied");
  });

  it("tells the user to copy by hand when the clipboard is unavailable", async () => {
    getUserInfoMock.mockResolvedValue(dto());
    createApiTokenMock.mockResolvedValue({
      ...token(),
      token: "pm_secret_plaintext",
    });

    const wrapper = mount(SettingsView);
    await flushPromises();
    await wrapper.get('input[name="token-name"]').setValue("laptop");
    await wrapper.get("form.settings-view__token-form").trigger("submit");
    await flushPromises();

    await buttonWithText(wrapper, "Copy token").trigger("click");
    await flushPromises();

    expect(
      wrapper.get('.settings-view__new-token [role="status"]').text(),
    ).toContain("copy it by hand");
    expect(wrapper.get(".settings-view__token-value").text()).toBe(
      "pm_secret_plaintext",
    );
  });

  it("shows create errors inline and keeps the typed name", async () => {
    getUserInfoMock.mockResolvedValue(dto());
    createApiTokenMock.mockRejectedValue(new ApiError(422, "Name too long"));

    const wrapper = mount(SettingsView);
    await flushPromises();
    await wrapper.get('input[name="token-name"]').setValue("laptop");
    await wrapper.get("form.settings-view__token-form").trigger("submit");
    await flushPromises();

    expect(
      wrapper.get('.settings-view__tokens [role="alert"]').text(),
    ).toContain("Name too long");
    expect(wrapper.find(".settings-view__token-value").exists()).toBe(false);
    expect(
      (wrapper.get('input[name="token-name"]').element as HTMLInputElement)
        .value,
    ).toBe("laptop");
  });

  it("revokes a token through the API client and removes it from the list", async () => {
    getUserInfoMock.mockResolvedValue(dto());
    listApiTokensMock.mockResolvedValue([token()]);
    revokeApiTokenMock.mockResolvedValue(undefined);

    const wrapper = mount(SettingsView);
    await flushPromises();

    await wrapper.get('button[aria-label="Revoke laptop"]').trigger("click");
    await flushPromises();

    expect(revokeApiTokenMock).toHaveBeenCalledWith(1);
    expect(wrapper.find(".settings-view__token-row").exists()).toBe(false);
    expect(wrapper.text()).toContain("No API tokens yet");
  });

  it("hides the plaintext when the just-created token is revoked", async () => {
    getUserInfoMock.mockResolvedValue(dto());
    createApiTokenMock.mockResolvedValue({
      ...token({ id: 5 }),
      token: "pm_secret_plaintext",
    });
    revokeApiTokenMock.mockResolvedValue(undefined);

    const wrapper = mount(SettingsView);
    await flushPromises();
    await wrapper.get('input[name="token-name"]').setValue("laptop");
    await wrapper.get("form.settings-view__token-form").trigger("submit");
    await flushPromises();

    await wrapper.get('button[aria-label="Revoke laptop"]').trigger("click");
    await flushPromises();

    expect(revokeApiTokenMock).toHaveBeenCalledWith(5);
    expect(wrapper.text()).not.toContain("pm_secret_plaintext");
  });

  it("shows revoke errors inline and keeps the token listed", async () => {
    getUserInfoMock.mockResolvedValue(dto());
    listApiTokensMock.mockResolvedValue([token()]);
    revokeApiTokenMock.mockRejectedValue(new ApiError(404, "Token not found"));

    const wrapper = mount(SettingsView);
    await flushPromises();

    await wrapper.get('button[aria-label="Revoke laptop"]').trigger("click");
    await flushPromises();

    expect(
      wrapper.get('.settings-view__tokens [role="alert"]').text(),
    ).toContain("Token not found");
    expect(wrapper.find(".settings-view__token-row").text()).toContain(
      "laptop",
    );
  });
});
