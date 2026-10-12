import createDOMPurify from "dompurify";
import { marked } from "marked";

import { stripTitle } from "./noteMockHelpers";

const sanitizer = createDOMPurify(window);

marked.use({
  gfm: true,
});

export function renderMarkdownBody(markdown: string): string {
  const raw = stripTitle(markdown).trim();
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
