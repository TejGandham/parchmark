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

  it("renders the active note body as structured markdown", () => {
    const wrapper = mount(AppShell);

    expect(wrapper.get(".doc-title").text()).toBe("Morning Pages");
    expect(wrapper.get(".prose h2").text()).toBe("What it's for");
    expect(wrapper.find(".prose blockquote").exists()).toBe(true);
    expect(wrapper.findAll(".prose li")).toHaveLength(3);
    expect(wrapper.find(".note-body").exists()).toBe(false);
  });

  it("renders table and task-list markdown when selecting notes", async () => {
    const wrapper = mount(AppShell);
    const cards = wrapper.findAll(".note-card");

    await cards
      .find((card) => card.text().includes("Reading list"))
      ?.trigger("click");
    expect(wrapper.find(".prose table").exists()).toBe(true);
    expect(wrapper.findAll(".prose th").map((cell) => cell.text())).toEqual([
      "Title",
      "Author",
      "Why",
    ]);

    await cards
      .find((card) => card.text().includes("Standup notes"))
      ?.trigger("click");
    const checkboxes = wrapper.findAll('.prose input[type="checkbox"]');
    expect(checkboxes).toHaveLength(3);
    expect(checkboxes[0].attributes("checked")).toBeDefined();
    expect(checkboxes[0].attributes("disabled")).toBeDefined();
  });
});
