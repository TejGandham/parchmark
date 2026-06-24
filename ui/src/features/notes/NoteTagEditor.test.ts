import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import { PlusIcon, XIcon } from "@/design-system/icons";

import NoteTagEditor from "./NoteTagEditor.vue";

describe("NoteTagEditor", () => {
  it("emits raw tag input without normalization", async () => {
    const wrapper = mount(NoteTagEditor, {
      props: {
        tags: ["draft"],
      },
    });

    await wrapper.get("input").setValue("  #Daily Log  ");
    await wrapper.get("form").trigger("submit");

    expect(wrapper.emitted("add-tag")?.[0]).toEqual(["  #Daily Log  "]);
    expect((wrapper.get("input").element as HTMLInputElement).value).toBe("");
  });

  it("does not emit an add event for blank input", async () => {
    const wrapper = mount(NoteTagEditor, {
      props: {
        tags: [],
      },
    });

    await wrapper.get("input").setValue("   ");
    await wrapper.get("form").trigger("submit");

    expect(wrapper.emitted("add-tag")).toBeUndefined();
    expect(
      wrapper.get('button[type="submit"]').attributes("disabled"),
    ).toBeDefined();
  });

  it("emits the selected existing tag for removal", async () => {
    const wrapper = mount(NoteTagEditor, {
      props: {
        tags: ["draft", "work"],
      },
    });

    await wrapper.get('[aria-label="Remove #work"]').trigger("click");

    expect(wrapper.emitted("remove-tag")?.[0]).toEqual(["work"]);
  });

  it("disables add and remove controls when disabled", () => {
    const wrapper = mount(NoteTagEditor, {
      props: {
        tags: ["draft"],
        disabled: true,
      },
    });

    expect(
      wrapper.get('[aria-label="Remove #draft"]').attributes("disabled"),
    ).toBeDefined();
    expect(wrapper.get("input").attributes("disabled")).toBeDefined();
    expect(
      wrapper.get('button[type="submit"]').attributes("disabled"),
    ).toBeDefined();
  });

  it("renders backend mutation errors and local add/remove icons", () => {
    const wrapper = mount(NoteTagEditor, {
      props: {
        tags: ["draft"],
        error: "Tag may contain only lowercase letters",
      },
    });

    expect(wrapper.get('[role="alert"]').text()).toContain(
      "Tag may contain only lowercase letters",
    );
    expect(wrapper.findComponent(PlusIcon).exists()).toBe(true);
    expect(wrapper.findComponent(XIcon).exists()).toBe(true);
  });
});
