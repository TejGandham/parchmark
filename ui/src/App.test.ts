import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import App from "./App.vue";

describe("App", () => {
  it("renders the V2 toolbar with design-system controls", () => {
    const wrapper = mount(App);

    expect(wrapper.get(".v2-brand").text()).toBe("ParchMark");
    expect(wrapper.find('[aria-label="New note"]').exists()).toBe(true);
    expect(wrapper.find('[role="radiogroup"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("Reading");
  });

  it("updates mode and toggles the overflow menu", async () => {
    const wrapper = mount(App);

    await wrapper.findAll('[role="radio"]')[1].trigger("click");
    expect(wrapper.text()).toContain("Editing");

    await wrapper.get('[aria-label="More actions"]').trigger("click");
    expect(wrapper.get('[role="menu"]').text()).toContain("Download");

    await wrapper.findAll('[role="menuitem"]')[0].trigger("click");
    expect(wrapper.find('[role="menu"]').exists()).toBe(false);
  });
});
