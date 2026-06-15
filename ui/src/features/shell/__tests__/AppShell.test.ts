import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it } from "vitest";

import AppShell from "../AppShell.vue";

describe("AppShell", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  it("creates a new mock note and switches to edit mode", async () => {
    const wrapper = mount(AppShell);

    await wrapper.get(".new-note-button").trigger("click");

    expect(wrapper.get(".doc-title").text()).toBe("Untitled");
    expect(wrapper.get(".mode-switch__status").text()).toContain("Editing");
  });

  it("opens settings from the user footer", async () => {
    const wrapper = mount(AppShell);

    await wrapper.get(".user-footer").trigger("click");

    expect(wrapper.text()).toContain("Settings");
    expect(wrapper.get(".user-footer").classes()).toContain("is-active");
  });

  it("uses the header edit action to switch modes", async () => {
    const wrapper = mount(AppShell);

    await wrapper.get('[aria-label="Switch to edit mode"]').trigger("click");

    expect(wrapper.get(".mode-switch__status").text()).toContain("Editing");
  });

  it("returns from edit mode to read mode from the header action", async () => {
    const wrapper = mount(AppShell);

    await wrapper.get('[aria-label="Switch to edit mode"]').trigger("click");
    await wrapper.get('[aria-label="Return to read mode"]').trigger("click");

    expect(wrapper.get(".mode-switch__status").text()).toContain("Reading");
    expect(wrapper.find('[aria-label="Return to read mode"]').exists()).toBe(
      false,
    );
  });
});
