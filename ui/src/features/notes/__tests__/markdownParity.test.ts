import { describe, expect, it } from "vitest";

import cases from "../../../../../testdata/markdown-parity.json";
import { extractTitle, stripTitle } from "../noteMockHelpers";

describe("markdown title parity fixture", () => {
  it.each(cases)(
    "extractTitle/stripTitle match the shared fixture for $name",
    ({ markdown, title, stripped }) => {
      expect(extractTitle(markdown)).toBe(title);
      expect(stripTitle(markdown)).toBe(stripped);
    },
  );

  it("covers every agreed title/strip category", () => {
    const names = new Set(cases.map((c) => c.name));
    expect(names).toEqual(
      new Set([
        "plain-h1-with-body",
        "h1-extra-whitespace-and-trailing-spaces",
        "blank-lines-before-h1",
        "h1-only-document",
        "multiple-h1s",
        "sub-headings-preserved",
        "hash-in-code-fence-after-h1",
      ]),
    );
  });
});
