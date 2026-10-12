import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import { mockNotes } from "@/features/notes/mockNotes";
import { allTags } from "@/features/notes/noteMockHelpers";

import SidebarDrawer from "../SidebarDrawer.vue";

function mountDrawerProps() {
  return {
    notes: mockNotes.slice(0, 3),
    activeId: "n1",
    search: "",
    tags: allTags(mockNotes),
    activeTags: [],
    open: true,
  };
}

function mountDrawer() {
  return mount(SidebarDrawer, {
    props: mountDrawerProps(),
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

  it("shows a loading indicator when loading=true", () => {
    const wrapper = mount(SidebarDrawer, {
      props: {
        ...mountDrawerProps(),
        loading: true,
      },
    });

    expect(wrapper.find(".note-list__loading").exists()).toBe(true);
    expect(wrapper.find(".note-card").exists()).toBe(false);
  });

  it("shows an error line with retry when error is set and loading=false", () => {
    const wrapper = mount(SidebarDrawer, {
      props: {
        ...mountDrawerProps(),
        loading: false,
        error: "Failed to load notes",
      },
    });

    expect(wrapper.find(".note-list__error").exists()).toBe(true);
    expect(wrapper.text()).toContain("Failed to load notes");
    expect(wrapper.find(".note-list__retry").exists()).toBe(true);
    expect(wrapper.find(".note-card").exists()).toBe(false);
  });

  it("shows the normal note list when loading=false and error is null", () => {
    const wrapper = mount(SidebarDrawer, {
      props: {
        ...mountDrawerProps(),
        loading: false,
        error: null,
      },
    });

    expect(wrapper.find(".note-list__loading").exists()).toBe(false);
    expect(wrapper.find(".note-list__error").exists()).toBe(false);
    expect(wrapper.find(".note-card").exists()).toBe(true);
  });

  it("emits retry when the retry button is clicked", async () => {
    const wrapper = mount(SidebarDrawer, {
      props: {
        ...mountDrawerProps(),
        loading: false,
        error: "Failed to load notes",
      },
    });

    await wrapper.get(".note-list__retry").trigger("click");

    expect(wrapper.emitted("retry")).toBeTruthy();
    expect(wrapper.emitted("retry")?.length).toBe(1);
  });
});
