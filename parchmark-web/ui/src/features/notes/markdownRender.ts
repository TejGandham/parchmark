import createDOMPurify from "dompurify";
import { marked } from "marked";

import { stripTitle } from "./noteMockHelpers";

const sanitizer = createDOMPurify(window);

marked.use({
  gfm: true,
});

/** Render Markdown as-is (no title stripping), sanitized with DOMPurify. */
export function renderMarkdown(markdown: string): string {
  const raw = markdown.trim();
  if (!raw) return "";

  const parsed = marked.parse(raw, { async: false }) as string;
  const withDiagrams = parsed.replace(
    /<pre><code class="language-mermaid">([\s\S]*?)<\/code><\/pre>/g,
    '<div class="mermaid">$1</div>',
  );

  return sanitizer.sanitize(withDiagrams, {
    ADD_TAGS: ["input"],
    ADD_ATTR: ["checked", "disabled", "type"],
  });
}

/** Notes: the leading H1 is the title, shown separately, so drop it. */
export function renderMarkdownBody(markdown: string): string {
  return renderMarkdown(stripTitle(markdown));
}
