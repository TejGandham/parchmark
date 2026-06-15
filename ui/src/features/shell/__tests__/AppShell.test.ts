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
    expect(wrapper.get(".editing-flag").text()).toContain("Editing");
  });

  it("opens settings from the user footer", async () => {
    const wrapper = mount(AppShell);

    await wrapper.get(".user-footer").trigger("click");

    expect(wrapper.text()).toContain("Settings");
    expect(wrapper.get(".user-footer").classes()).toContain("is-active");
  });

  it("uses the overflow edit item to switch modes", async () => {
    const wrapper = mount(AppShell);

    await wrapper.get('[aria-label="More"]').trigger("click");
    await wrapper.findAll('[role="menuitem"]')[0].trigger("click");

    expect(wrapper.get(".editing-flag").text()).toContain("Editing");
  });
});
