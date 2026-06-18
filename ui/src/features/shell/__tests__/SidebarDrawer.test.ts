import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import { mockNotes } from "@/features/notes/mockNotes";
import { allTags } from "@/features/notes/noteMockHelpers";

import SidebarDrawer from "../SidebarDrawer.vue";

function mountDrawer() {
  return mount(SidebarDrawer, {
    props: {
      notes: mockNotes.slice(0, 3),
      activeId: "n1",
      search: "",
      tags: allTags(mockNotes),
      activeTags: [],
      open: true,
    },
  });
}

describe("SidebarDrawer", () => {
  it("renders grouped note cards and active state", () => {
    const wrapper = mountDrawer();

    expect(wrapper.text()).toContain("Today");
    expect(wrapper.text()).toContain("Yesterday");
    expect(wrapper.get(".note-card.is-active").text()).toContain(
      "Morning Pages",
    );
  });

  it("emits shell events for search, tag, note, new note, and settings", async () => {
    const wrapper = mountDrawer();

    await wrapper.get('input[type="search"]').setValue("reading");
    await wrapper.findAll(".tag-filter__tag")[0].trigger("click");
    await wrapper.findAll(".note-card")[1].trigger("click");
    await wrapper.get(".new-note-button").trigger("click");
    await wrapper.get(".user-footer__main").trigger("click");

    expect(wrapper.emitted("update:search")?.[0]).toEqual(["reading"]);
    expect(wrapper.emitted("toggleTag")).toBeTruthy();
    expect(wrapper.emitted("select")?.[0]).toEqual(["n2"]);
    expect(wrapper.emitted("newNote")).toBeTruthy();
    expect(wrapper.emitted("openSettings")).toBeTruthy();
  });
});
