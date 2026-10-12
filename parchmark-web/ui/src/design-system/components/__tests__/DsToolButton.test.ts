import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import DsToolButton from "../DsToolButton.vue";

describe("DsToolButton", () => {
  it("renders an accessible icon button", () => {
    const wrapper = mount(DsToolButton, {
      props: { label: "New note" },
      slots: { default: '<span data-test="icon" />' },
    });

    const button = wrapper.get("button");
    expect(button.attributes("aria-label")).toBe("New note");
    expect(button.attributes("type")).toBe("button");
    expect(wrapper.find('[data-test="icon"]').exists()).toBe(true);
  });

  it("reflects active and disabled states", () => {
    const wrapper = mount(DsToolButton, {
      props: { label: "More actions", active: true, disabled: true },
    });

    const button = wrapper.get("button");
    expect(button.classes()).toContain("is-active");
    expect(button.attributes("aria-pressed")).toBe("true");
    expect(button.attributes("disabled")).toBeDefined();
  });
});
