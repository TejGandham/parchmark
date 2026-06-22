import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

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

    expect(wrapper.emitted("addTag")?.[0]).toEqual(["  #Daily Log  "]);
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

    expect(wrapper.emitted("addTag")).toBeUndefined();
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

    expect(wrapper.emitted("removeTag")?.[0]).toEqual(["work"]);
  });

  it("disables add and remove controls while saving", () => {
    const wrapper = mount(NoteTagEditor, {
      props: {
        tags: ["draft"],
        saving: true,
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
});
