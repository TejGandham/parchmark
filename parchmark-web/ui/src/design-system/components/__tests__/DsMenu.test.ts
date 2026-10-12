import { mount } from "@vue/test-utils";
import { markRaw } from "vue";
import { describe, expect, it } from "vitest";

import DsMenu from "../DsMenu.vue";
import { CopyIcon, TrashIcon } from "../../icons";

const items = [
  { id: "copy", label: "Copy link", icon: markRaw(CopyIcon) },
  {
    id: "delete",
    label: "Delete note",
    icon: markRaw(TrashIcon),
    danger: true,
    separatorBefore: true,
  },
];

describe("DsMenu", () => {
  it("renders menu items with separators and danger state", () => {
    const wrapper = mount(DsMenu, {
      props: { open: true, items, labelledBy: "menu-trigger" },
    });

    expect(wrapper.attributes("role")).toBe("menu");
    expect(wrapper.attributes("aria-labelledby")).toBe("menu-trigger");
    expect(wrapper.findAll('[role="menuitem"]')).toHaveLength(2);
    expect(wrapper.find('[role="separator"]').exists()).toBe(true);
    expect(wrapper.findAll("button")[1].classes()).toContain("is-danger");
  });

  it("emits select and close interactions", async () => {
    const wrapper = mount(DsMenu, {
      props: { open: true, items, labelledBy: "menu-trigger" },
    });

    await wrapper.findAll("button")[0].trigger("click");
    await wrapper.findAll("button")[1].trigger("keydown", { key: "Escape" });

    expect(wrapper.emitted("select")).toEqual([["copy"]]);
    expect(wrapper.emitted("close")).toEqual([[]]);
  });

  it("does not render when closed", () => {
    const wrapper = mount(DsMenu, {
      props: { open: false, items, labelledBy: "menu-trigger" },
    });

    expect(wrapper.find('[role="menu"]').exists()).toBe(false);
  });

  it("moves focus with keyboard controls", async () => {
    const wrapper = mount(DsMenu, {
      attachTo: document.body,
      props: { open: true, items, labelledBy: "menu-trigger" },
    });

    const buttons = wrapper.findAll("button");
    await buttons[0].trigger("keydown", { key: "ArrowDown" });
    expect(document.activeElement).toBe(buttons[1].element);

    await buttons[1].trigger("keydown", { key: "ArrowUp" });
    expect(document.activeElement).toBe(buttons[0].element);

    await buttons[0].trigger("keydown", { key: "End" });
    expect(document.activeElement).toBe(buttons[1].element);

    await buttons[1].trigger("keydown", { key: "Home" });
    expect(document.activeElement).toBe(buttons[0].element);

    wrapper.unmount();
  });
});
