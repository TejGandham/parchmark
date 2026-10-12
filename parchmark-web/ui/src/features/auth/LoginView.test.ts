import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

import LoginView from "./LoginView.vue";

// Controllable store state shared with the mocked `useAuth` composable.
const error = ref<string | null>(null);
const pending = ref(false);
const login = vi.fn().mockResolvedValue(true);

vi.mock("./useAuth", () => ({
  useAuth: () => ({ error, pending, login }),
}));

beforeEach(() => {
  error.value = null;
  pending.value = false;
  login.mockClear();
});

describe("LoginView", () => {
  it("renders the brand aside and a sign-in form", () => {
    const wrapper = mount(LoginView);

    const brand = wrapper.get(".auth-brand");
    expect(brand.text()).toContain("Parch");
    expect(brand.get(".mk").text()).toBe("Mark");

    // Three feature rows in the brand panel.
    expect(wrapper.findAll(".auth-feats .af")).toHaveLength(3);

    expect(wrapper.find('input[autocomplete="username"]').exists()).toBe(true);
    expect(
      wrapper.find('input[autocomplete="current-password"]').exists(),
    ).toBe(true);

    const submit = wrapper.get('button[type="submit"]');
    expect(submit.text()).toContain("Sign in");
  });

  it("toggles the password field between password and text", async () => {
    const wrapper = mount(LoginView);

    const pwInput = wrapper.get('input[autocomplete="current-password"]');
    expect(pwInput.attributes("type")).toBe("password");

    await wrapper.get(".pw-toggle").trigger("click");
    expect(pwInput.attributes("type")).toBe("text");

    await wrapper.get(".pw-toggle").trigger("click");
    expect(pwInput.attributes("type")).toBe("password");
  });

  it("submitting the form calls login with the entered credentials", async () => {
    const wrapper = mount(LoginView);

    await wrapper.get('input[autocomplete="username"]').setValue("jamie");
    await wrapper
      .get('input[autocomplete="current-password"]')
      .setValue("s3cret");
    await wrapper.get("form").trigger("submit");

    expect(login).toHaveBeenCalledWith("jamie", "s3cret");
  });

  it("renders the store error in the .auth-err region", async () => {
    const wrapper = mount(LoginView);
    expect(wrapper.find(".auth-err").exists()).toBe(false);

    error.value = "Invalid username or password";
    await wrapper.vm.$nextTick();

    const err = wrapper.get(".auth-err");
    expect(err.text()).toContain("Invalid username or password");
  });

  it("disables inputs and submit while pending", async () => {
    pending.value = true;
    const wrapper = mount(LoginView);

    expect(
      wrapper.get('input[autocomplete="username"]').attributes("disabled"),
    ).toBeDefined();
    expect(
      wrapper
        .get('input[autocomplete="current-password"]')
        .attributes("disabled"),
    ).toBeDefined();
    expect(
      wrapper.get('button[type="submit"]').attributes("disabled"),
    ).toBeDefined();
    expect(wrapper.find(".spin").exists()).toBe(true);
  });

  it("does not render SSO, forgot-password, or create-account affordances", () => {
    const wrapper = mount(LoginView);
    const text = wrapper.text();

    expect(text).not.toContain("Forgot");
    expect(text).not.toContain("Create an account");
    expect(text.toLowerCase()).not.toContain("sso");
    expect(text.toLowerCase()).not.toContain("single sign-on");
    expect(wrapper.find(".sso").exists()).toBe(false);
    expect(wrapper.find(".auth-or").exists()).toBe(false);
    expect(wrapper.find(".auth-switch").exists()).toBe(false);
  });
});
