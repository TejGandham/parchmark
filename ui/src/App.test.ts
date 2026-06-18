import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

import App from "./App.vue";

// Controllable auth state shared with the mocked `useAuth` composable. App
// renders AppShell only once the session is restored AND the user is
// authenticated; otherwise it shows LoginView.
const isAuthenticated = ref(false);
const user = ref<{ username: string } | null>(null);
const error = ref<string | null>(null);
const pending = ref(false);
const restoreSession = vi.fn().mockResolvedValue(undefined);
const login = vi.fn().mockResolvedValue(true);
const logout = vi.fn().mockResolvedValue(undefined);

vi.mock("@/features/auth/useAuth", () => ({
  useAuth: () => ({
    isAuthenticated,
    user,
    error,
    pending,
    restoreSession,
    login,
    logout,
  }),
}));

beforeEach(() => {
  localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
  isAuthenticated.value = false;
  user.value = null;
  error.value = null;
  pending.value = false;
  restoreSession.mockClear();
});

describe("App", () => {
  it("restores the session on mount", async () => {
    mount(App);
    await flushPromises();

    expect(restoreSession).toHaveBeenCalledTimes(1);
  });

  it("renders LoginView, not the app shell, when unauthenticated", async () => {
    const wrapper = mount(App);
    await flushPromises();

    expect(wrapper.find(".auth-shell").exists()).toBe(true);
    expect(wrapper.find(".app-shell").exists()).toBe(false);
    expect(wrapper.find(".wordmark").exists()).toBe(false);
  });

  it("renders the V2 app shell with notes and topbar controls when authenticated", async () => {
    isAuthenticated.value = true;
    user.value = { username: "jamie" };

    const wrapper = mount(App);
    await flushPromises();

    expect(wrapper.find(".auth-shell").exists()).toBe(false);
    expect(wrapper.get(".wordmark").text()).toBe("ParchMark");
    expect(wrapper.get(".doc-title").text()).toBe("Morning Pages");
    expect(wrapper.get(".mode-switch__status").text()).toContain("Reading");
    expect(wrapper.find('[aria-label="Switch to edit mode"]').exists()).toBe(
      true,
    );
    expect(wrapper.get(".prose").text()).toContain("Today");
    expect(wrapper.find(".prose blockquote").exists()).toBe(true);
  });
});
