import { describe, expect, it } from "vitest";

import { renderMarkdown, renderMarkdownBody } from "../markdownRender";

describe("renderMarkdownBody", () => {
  it("strips the first H1 title and preserves markdown structure", () => {
    const html = renderMarkdownBody(`# Morning Pages

## What it's for

> The page asks for nothing back.

- Don't stop moving the pen`);

    expect(html).not.toContain("<h1");
    expect(html).not.toContain("Morning Pages");
    expect(html).toContain("<h2>What it's for</h2>");
    expect(html).toContain("<blockquote>");
    expect(html).toContain("<li>Don't stop moving the pen</li>");
  });

  it("renders GFM tables and task-list checkboxes", () => {
    const html = renderMarkdownBody(`# Reading list

| Title | Author | Why |
| --- | --- | --- |
| The Craftsman | Sennett | Making as thinking |

- [x] Write up the rollout plan
- [ ] Review Sam's PR`);

    expect(html).toContain("<table>");
    expect(html).toContain("<th>Title</th>");
    expect(html).toContain("<th>Author</th>");
    expect(html).toContain("<th>Why</th>");
    expect(html).toContain('type="checkbox"');
    expect(html).toContain("checked");
    expect(html).toContain("disabled");
  });

  it("sanitizes scripts and event handler attributes", () => {
    const html = renderMarkdownBody(`# Unsafe

<script>alert("bad")</script>
<img src="x" onerror="alert('bad')" />
<a href="javascript:alert('bad')">bad link</a>`);

    expect(html).not.toContain("<script");
    expect(html).not.toContain("onerror");
    expect(html).not.toContain("javascript:");
    expect(html).toContain("<img");
    expect(html).toContain(">bad link</a>");
  });
});

describe("renderMarkdown links", () => {
  const LINKS = `[Example link](https://example.com/page)

[Jump](#section)

<a href="javascript:alert('bad')">bad link</a>`;

  function anchors(html: string): HTMLAnchorElement[] {
    const template = document.createElement("template");
    template.innerHTML = html;
    return [...template.content.querySelectorAll("a")];
  }

  it("opens a link to another page in a new tab when linksInNewTab is set", () => {
    const [external] = anchors(renderMarkdown(LINKS, { linksInNewTab: true }));

    expect(external.getAttribute("href")).toBe("https://example.com/page");
    expect(external.getAttribute("target")).toBe("_blank");
    expect(external.getAttribute("rel")).toBe("noopener noreferrer");
  });

  it("leaves a fragment-only link alone", () => {
    const [, fragment] = anchors(
      renderMarkdown(LINKS, { linksInNewTab: true }),
    );

    expect(fragment.getAttribute("href")).toBe("#section");
    expect(fragment.hasAttribute("target")).toBe(false);
    expect(fragment.hasAttribute("rel")).toBe(false);
  });

  it("still strips a javascript: href when linksInNewTab is set", () => {
    const html = renderMarkdown(LINKS, { linksInNewTab: true });

    expect(html).not.toContain("javascript:");
    expect(html).toContain(">bad link</a>");
  });

  it("leaves note links unchanged", () => {
    const links = [
      ...anchors(renderMarkdown(LINKS)),
      ...anchors(renderMarkdownBody(`# Title\n\n${LINKS}`)),
    ];

    expect(links).toHaveLength(6);
    for (const link of links) {
      expect(link.hasAttribute("target")).toBe(false);
      expect(link.hasAttribute("rel")).toBe(false);
    }
  });
});
