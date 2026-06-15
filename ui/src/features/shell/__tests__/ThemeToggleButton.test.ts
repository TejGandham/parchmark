import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ThemeToggleButton from "../ThemeToggleButton.vue";

describe("ThemeToggleButton", () => {
  it("labels the light and dark theme states", async () => {
    const wrapper = mount(ThemeToggleButton, {
      props: {
        theme: "light",
      },
    });

    expect(wrapper.get("button").attributes("aria-label")).toBe(
      "Switch to Desk lamp",
    );

    await wrapper.get("button").trigger("click");
    expect(wrapper.emitted("toggle")).toBeTruthy();

    await wrapper.setProps({ theme: "dark" });
    expect(wrapper.get("button").attributes("aria-label")).toBe(
      "Switch to Parchment",
    );
  });
});
