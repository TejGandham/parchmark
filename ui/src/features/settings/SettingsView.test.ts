import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../services/settings", () => ({
  getUserInfo: vi.fn(),
}));

import { getUserInfo, type UserInfoDTO } from "../../services/settings";

import SettingsView from "./SettingsView.vue";
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

describe("SettingsView", () => {
  beforeEach(() => {
    const { userInfo, loading, error } = useSettings();
    userInfo.value = null;
    loading.value = false;
    error.value = null;
    getUserInfoMock.mockReset();
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
});
