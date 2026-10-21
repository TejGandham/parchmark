import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import MarkdownProse from "../MarkdownProse.vue";
import { mockNotes } from "../mockNotes";

describe("MarkdownProse", () => {
  it("renders Morning Pages markdown without duplicating the title", () => {
    const wrapper = mount(MarkdownProse, {
      props: { markdown: mockNotes[0].content },
    });

    expect(wrapper.find("h1").exists()).toBe(false);
    expect(wrapper.find("h2").text()).toBe("What it's for");
    expect(wrapper.find("blockquote").text()).toContain(
      "The page asks for nothing back.",
    );
    expect(wrapper.findAll("li")).toHaveLength(3);
  });

  it("renders table notes as table markup", () => {
    const wrapper = mount(MarkdownProse, {
      props: { markdown: mockNotes[2].content },
    });

    expect(wrapper.find("table").exists()).toBe(true);
    expect(wrapper.findAll("th").map((cell) => cell.text())).toEqual([
      "Title",
      "Author",
      "Why",
    ]);
  });

  it("renders task list checkboxes as disabled inputs", () => {
    const wrapper = mount(MarkdownProse, {
      props: { markdown: mockNotes[1].content },
    });
    const checkboxes = wrapper.findAll('input[type="checkbox"]');

    expect(checkboxes).toHaveLength(3);
    expect(checkboxes[0].attributes("checked")).toBeDefined();
    expect(
      checkboxes.every(
        (checkbox) => checkbox.attributes("disabled") !== undefined,
      ),
    ).toBe(true);
  });

  it("leaves a note's links as plain same-tab links", () => {
    const wrapper = mount(MarkdownProse, {
      props: { markdown: "# Note\n\n[Example link](https://example.com/)" },
    });
    const link = wrapper.get("a");

    expect(link.attributes("target")).toBeUndefined();
    expect(link.attributes("rel")).toBeUndefined();
  });

  it("opens links in a new tab when linksInNewTab is set", () => {
    const wrapper = mount(MarkdownProse, {
      props: {
        markdown: "[Example link](https://example.com/)\n\n[Jump](#section)",
        keepTitle: true,
        linksInNewTab: true,
      },
    });
    const [external, fragment] = wrapper.findAll("a");

    expect(external.attributes("target")).toBe("_blank");
    expect(external.attributes("rel")).toBe("noopener noreferrer");
    expect(fragment.attributes("target")).toBeUndefined();
  });
});
