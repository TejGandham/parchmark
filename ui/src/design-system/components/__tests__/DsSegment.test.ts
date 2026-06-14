import { mount } from "@vue/test-utils";
import { markRaw } from "vue";
import { describe, expect, it } from "vitest";

import DsSegment from "../DsSegment.vue";
import { EditIcon, EyeIcon } from "../../icons";

const options = [
  { value: "read", label: "Read", icon: markRaw(EyeIcon) },
  { value: "edit", label: "Edit", icon: markRaw(EditIcon) },
];

describe("DsSegment", () => {
  it("renders radiogroup options and active state", () => {
    const wrapper = mount(DsSegment, {
      props: { modelValue: "read", options, ariaLabel: "Note mode" },
    });

    expect(wrapper.attributes("role")).toBe("radiogroup");
    expect(wrapper.attributes("aria-label")).toBe("Note mode");
    expect(wrapper.findAll('[role="radio"]')).toHaveLength(2);
    expect(wrapper.find('[aria-checked="true"]').text()).toContain("Read");
  });

  it("emits model updates for enabled options", async () => {
    const wrapper = mount(DsSegment, {
      props: { modelValue: "read", options, ariaLabel: "Note mode" },
    });

    await wrapper.findAll("button")[1].trigger("click");

    expect(wrapper.emitted("update:modelValue")).toEqual([["edit"]]);
  });

  it("skips disabled options", async () => {
    const wrapper = mount(DsSegment, {
      props: {
        modelValue: "read",
        options: [{ ...options[0] }, { ...options[1], disabled: true }],
        ariaLabel: "Note mode",
      },
    });

    await wrapper.findAll("button")[1].trigger("click");

    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
  });

  it("moves focus with roving keyboard controls", async () => {
    const wrapper = mount(DsSegment, {
      attachTo: document.body,
      props: { modelValue: "read", options, ariaLabel: "Note mode" },
    });

    const buttons = wrapper.findAll("button");
    await buttons[0].trigger("keydown", { key: "ArrowRight" });
    expect(document.activeElement).toBe(buttons[1].element);

    await buttons[1].trigger("keydown", { key: "ArrowLeft" });
    expect(document.activeElement).toBe(buttons[0].element);

    await buttons[0].trigger("keydown", { key: "End" });
    expect(document.activeElement).toBe(buttons[1].element);

    await buttons[1].trigger("keydown", { key: "Home" });
    expect(document.activeElement).toBe(buttons[0].element);

    wrapper.unmount();
  });
});
