import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import { MoreIcon, PlusIcon, SearchIcon } from ".";

describe("design-system icons", () => {
  it("renders decorative SVGs by default", () => {
    const wrapper = mount(PlusIcon);

    expect(wrapper.get("svg").attributes("aria-hidden")).toBe("true");
    expect(wrapper.get("path").attributes("d")).toBe("M12 5v14M5 12h14");
  });

  it("renders accessible titles when provided", () => {
    const wrapper = mount(SearchIcon, {
      props: { title: "Search notes" },
    });

    expect(wrapper.get("svg").attributes("role")).toBe("img");
    expect(wrapper.get("title").text()).toBe("Search notes");
  });

  it("supports filled icon geometry", () => {
    const wrapper = mount(MoreIcon);

    expect(wrapper.findAll("circle")).toHaveLength(3);
    expect(wrapper.get("svg").attributes("fill")).toBe("currentColor");
  });
});
