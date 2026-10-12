import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

import UserFooter from "./UserFooter.vue";

// Controllable auth state shared with the mocked `useAuth` composable.
const user = ref<{ username: string } | null>(null);
const logout = vi.fn().mockResolvedValue(undefined);

vi.mock("@/features/auth/useAuth", () => ({
  useAuth: () => ({ user, logout }),
}));

beforeEach(() => {
  user.value = null;
  logout.mockClear();
});

describe("UserFooter", () => {
  it("shows the authenticated username from the store", () => {
    user.value = { username: "jamie" };
    const wrapper = mount(UserFooter);

    expect(wrapper.get(".user-footer__identity").text()).toBe("jamie");
    expect(wrapper.get(".user-footer__avatar").text()).toBe("JA");
  });

  it("falls back gracefully when no user is present", () => {
    const wrapper = mount(UserFooter);

    expect(wrapper.get(".user-footer__identity").text()).toBe("Account");
  });

  it("emits openSettings when the identity control is clicked", async () => {
    const wrapper = mount(UserFooter);

    await wrapper.get(".user-footer__main").trigger("click");

    expect(wrapper.emitted("openSettings")).toBeTruthy();
  });

  it("calls logout when the sign-out control is clicked", async () => {
    const wrapper = mount(UserFooter);

    await wrapper.get('[aria-label="Sign out"]').trigger("click");

    expect(logout).toHaveBeenCalledTimes(1);
  });
});
