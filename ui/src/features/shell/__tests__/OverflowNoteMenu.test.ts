import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import { mockNotes } from "@/features/notes/mockNotes";

import OverflowNoteMenu from "../OverflowNoteMenu.vue";

describe("OverflowNoteMenu", () => {
  it("emits menu actions and keeps the danger row separated", async () => {
    const wrapper = mount(OverflowNoteMenu, {
      props: {
        open: true,
        note: mockNotes[0],
      },
      attachTo: document.body,
    });

    const items = wrapper.findAll('[role="menuitem"]');

    expect(wrapper.find('[role="separator"]').exists()).toBe(true);
    expect(items[2].classes()).toContain("is-danger");

    await items[0].trigger("click");
    await items[1].trigger("click");
    await items[2].trigger("click");

    expect(wrapper.emitted("select")).toEqual([
      ["copy"],
      ["export"],
      ["delete"],
    ]);

    wrapper.unmount();
  });

  it("closes on Escape and outside pointerdown", async () => {
    const wrapper = mount(OverflowNoteMenu, {
      props: {
        open: true,
        note: mockNotes[0],
      },
      attachTo: document.body,
    });

    await wrapper.find('[role="menuitem"]').trigger("keydown", {
      key: "Escape",
    });
    document.body.dispatchEvent(new Event("pointerdown", { bubbles: true }));

    expect(wrapper.emitted("update:open")).toEqual([[false], [false]]);

    wrapper.unmount();
  });
});
