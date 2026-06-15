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
  it("renders the note breadcrumb and read/edit segment", () => {
    const wrapper = mountTopbar();

    expect(wrapper.text()).toContain("All notes");
    expect(wrapper.text()).toContain("Morning Pages");
    expect(wrapper.find('[aria-checked="true"]').text()).toContain("Read");
  });

  it("emits drawer, edit, theme, menu, and note-action events", async () => {
    const wrapper = mountTopbar();

    await wrapper.get('[aria-label="Menu"]').trigger("click");
    await wrapper.findAll('[role="radio"]')[1].trigger("click");
    await wrapper.get('[aria-label="Switch to Desk lamp"]').trigger("click");
    await wrapper.get('[aria-label="More"]').trigger("click");
    await wrapper.setProps({ menuOpen: true });
    await wrapper.findAll('[role="menuitem"]')[1].trigger("click");

    expect(wrapper.emitted("openDrawer")).toBeTruthy();
    expect(wrapper.emitted("update:mode")?.[0]).toEqual(["edit"]);
    expect(wrapper.emitted("startEdit")).toBeTruthy();
    expect(wrapper.emitted("toggleTheme")).toBeTruthy();
    expect(wrapper.emitted("update:menuOpen")?.[0]).toEqual([true]);
    expect(wrapper.emitted("noteAction")?.[0]).toEqual(["copy"]);
  });

  it("shows the editing flag instead of note actions in edit mode", () => {
    const wrapper = mountTopbar({ mode: "edit" });

    expect(wrapper.get(".editing-flag").text()).toContain("Editing");
    expect(wrapper.find('[aria-label="More"]').exists()).toBe(false);
    expect(wrapper.find('[role="radiogroup"]').exists()).toBe(false);
  });
});
