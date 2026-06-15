import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import { mockNotes } from "@/features/notes/mockNotes";
import { extractTitle } from "@/features/notes/noteMockHelpers";

import AppTopbar from "../AppTopbar.vue";

function mountTopbar(options = {}) {
  const note = mockNotes[0];
  return mount(AppTopbar, {
    props: {
      activeNote: note,
      activeTags: [],
      title: extractTitle(note.content),
      mode: "read",
      theme: "light",
      menuOpen: false,
      ...options,
    },
  });
}

describe("AppTopbar", () => {
  it("renders the note breadcrumb and mode action", () => {
    const wrapper = mountTopbar();

    expect(wrapper.text()).toContain("All notes");
    expect(wrapper.text()).toContain("Morning Pages");
    expect(wrapper.get(".mode-switch__status").text()).toContain("Reading");
    expect(wrapper.get('[aria-label="Switch to edit mode"]').text()).toContain(
      "Edit",
    );
  });

  it("emits drawer, edit, theme, menu, and note-action events", async () => {
    const wrapper = mountTopbar();

    await wrapper.get('[aria-label="Menu"]').trigger("click");
    await wrapper.get('[aria-label="Switch to edit mode"]').trigger("click");
    await wrapper.get('[aria-label="Switch to Desk lamp"]').trigger("click");
    await wrapper.get('[aria-label="More"]').trigger("click");
    await wrapper.setProps({ menuOpen: true });
    await wrapper.findAll('[role="menuitem"]')[0].trigger("click");

    expect(wrapper.emitted("openDrawer")).toBeTruthy();
    expect(wrapper.emitted("update:mode")?.[0]).toEqual(["edit"]);
    expect(wrapper.emitted("startEdit")).toBeTruthy();
    expect(wrapper.emitted("toggleTheme")).toBeTruthy();
    expect(wrapper.emitted("update:menuOpen")?.[0]).toEqual([true]);
    expect(wrapper.emitted("noteAction")?.[0]).toEqual(["copy"]);
  });

  it("keeps note controls available in edit mode", () => {
    const wrapper = mountTopbar({ mode: "edit" });

    expect(wrapper.get(".mode-switch__status").text()).toContain("Editing");
    expect(wrapper.get('[aria-label="Return to read mode"]').text()).toContain(
      "Read",
    );
    expect(wrapper.find('[aria-label="More"]').exists()).toBe(true);
    expect(wrapper.find('[aria-label="Switch to edit mode"]').exists()).toBe(
      false,
    );
  });
});
