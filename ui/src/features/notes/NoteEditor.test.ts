import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import NoteEditor from "./NoteEditor.vue";

describe("NoteEditor", () => {
  it("emits draft updates, save, and cancel", async () => {
    const wrapper = mount(NoteEditor, {
      props: {
        modelValue: "# Draft",
        canSave: true,
      },
    });

    await wrapper.get("textarea").setValue("# Updated");
    await wrapper.get("form").trigger("submit");
    await wrapper.get('button[type="button"]').trigger("click");

    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual(["# Updated"]);
    expect(wrapper.emitted("save")).toBeTruthy();
    expect(wrapper.emitted("cancel")).toBeTruthy();
  });

  it("disables save while saving or when save is not allowed", () => {
    const wrapper = mount(NoteEditor, {
      props: {
        modelValue: "# Draft",
        canSave: false,
        saving: false,
      },
    });

    expect(
      wrapper.get('button[type="submit"]').attributes("disabled"),
    ).toBeDefined();
  });

  it("renders an error message", () => {
    const wrapper = mount(NoteEditor, {
      props: {
        modelValue: "# Draft",
        canSave: true,
        error: "save failed",
      },
    });

    expect(wrapper.get('[role="alert"]').text()).toBe("save failed");
  });
});
