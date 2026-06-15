import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it } from "vitest";

import App from "./App.vue";

describe("App", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  it("renders the V2 app shell with notes and topbar controls", () => {
    const wrapper = mount(App);

    expect(wrapper.get(".wordmark").text()).toBe("ParchMark");
    expect(wrapper.get(".doc-title").text()).toBe("Morning Pages");
    expect(wrapper.get(".mode-switch__status").text()).toContain("Reading");
    expect(wrapper.find('[aria-label="Switch to edit mode"]').exists()).toBe(
      true,
    );
    expect(wrapper.text()).toContain("Today");
  });

  it("filters notes by search and tag, then selects the remaining note", async () => {
    const wrapper = mount(App);

    await wrapper.get('input[type="search"]').setValue("standup");
    const noteList = wrapper.get(".note-list");
    expect(noteList.text()).toContain("Standup notes");
    expect(noteList.text()).not.toContain("Morning Pages");

    const logTag = wrapper
      .findAll(".tag-filter__tag")
      .find((button) => button.text().includes("log"));
    expect(logTag).toBeTruthy();
    await logTag?.trigger("click");
    expect(wrapper.text()).toContain("#log");

    await wrapper.get(".note-card").trigger("click");
    expect(wrapper.get(".doc-title").text()).toBe("Standup notes");
  });

  it("opens the mobile drawer state and toggles the theme", async () => {
    const wrapper = mount(App);

    await wrapper.get('[aria-label="Menu"]').trigger("click");
    expect(wrapper.get(".sidebar-drawer").classes()).toContain("is-open");

    await wrapper.get('[aria-label="Close navigation"]').trigger("click");
    expect(wrapper.get(".sidebar-drawer").classes()).not.toContain("is-open");

    await wrapper.get('[aria-label="Switch to Desk lamp"]').trigger("click");
    expect(document.documentElement.dataset.theme).toBe("dark");
  });
});
