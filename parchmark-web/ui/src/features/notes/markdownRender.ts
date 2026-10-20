import createDOMPurify from "dompurify";
import { marked } from "marked";

import { stripTitle } from "./noteMockHelpers";

const sanitizer = createDOMPurify(window);

marked.use({
  gfm: true,
});

export interface RenderOptions {
  /** Open every link except a fragment-only one (#section) in a new tab, with rel="noopener noreferrer". */
  linksInNewTab?: boolean;
}

/** Render Markdown as-is (no title stripping), sanitized with DOMPurify. */
export function renderMarkdown(
  markdown: string,
  options: RenderOptions = {},
): string {
  const raw = markdown.trim();
  if (!raw) return "";

  const parsed = marked.parse(raw, { async: false }) as string;
  const withDiagrams = parsed.replace(
    /<pre><code class="language-mermaid">([\s\S]*?)<\/code><\/pre>/g,
    '<div class="mermaid">$1</div>',
  );

  const clean = sanitizer.sanitize(withDiagrams, {
    ADD_TAGS: ["input"],
    ADD_ATTR: ["checked", "disabled", "type"],
  });
  return options.linksInNewTab ? openLinksInNewTab(clean) : clean;
}

/**
 * A pass over already-sanitized HTML rather than a DOMPurify hook: hooks on the shared sanitizer would apply to
 * every caller, notes included. It only adds target and rel, so the sanitizer's verdict on each href stands.
 */
function openLinksInNewTab(html: string): string {
  const template = document.createElement("template");
  template.innerHTML = html;
  for (const link of template.content.querySelectorAll("a[href]")) {
    if (link.getAttribute("href")?.startsWith("#")) continue;
    link.setAttribute("target", "_blank");
    link.setAttribute("rel", "noopener noreferrer");
  }
  return template.innerHTML;
}

/** Notes: the leading H1 is the title, shown separately, so drop it. */
export function renderMarkdownBody(
  markdown: string,
  options: RenderOptions = {},
): string {
  return renderMarkdown(stripTitle(markdown), options);
}
