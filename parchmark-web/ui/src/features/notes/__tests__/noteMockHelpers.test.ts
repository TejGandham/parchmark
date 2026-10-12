import { describe, expect, it } from "vitest";

import type { NoteMock } from "../mockNotes";
import {
  allTags,
  extractTitle,
  groupByTime,
  plainPreview,
  readingTime,
  relTime,
  stripTitle,
  wordCount,
} from "../noteMockHelpers";

const day = 86_400_000;
const now = new Date("2026-06-14T12:00:00Z").getTime();

const notes: NoteMock[] = [
  {
    id: "today",
    tags: ["draft", "work"],
    createdAt: now,
    updatedAt: now - 60_000,
    content: "# Today\n\nBody text",
  },
  {
    id: "yesterday",
    tags: ["work"],
    createdAt: now - day,
    updatedAt: now - day,
    content: "# Yesterday\n\nBody text",
  },
  {
    id: "week",
    tags: ["ideas"],
    createdAt: now - 3 * day,
    updatedAt: now - 3 * day,
    content: "# Week\n\nBody text",
  },
  {
    id: "earlier",
    tags: [],
    createdAt: now - 10 * day,
    updatedAt: now - 10 * day,
    content: "# Earlier\n\nBody text",
  },
];

describe("note mock helpers", () => {
  it("extracts titles, strips titles, and builds plain previews", () => {
    const markdown = "# Heading\n\n- **Strong** [link](https://example.com)";

    expect(extractTitle(markdown)).toBe("Heading");
    expect(stripTitle(markdown)).toBe(
      "- **Strong** [link](https://example.com)",
    );
    expect(plainPreview(markdown)).toBe("Strong link");
  });

  it("counts words and reading time", () => {
    expect(wordCount("# Title\n\nOne two three")).toBe(3);
    expect(readingTime("# Title\n\nOne two three")).toBe(1);
  });

  it("sorts tag counts by frequency then name", () => {
    expect(allTags(notes)).toEqual([
      { tag: "work", count: 2 },
      { tag: "draft", count: 1 },
      { tag: "ideas", count: 1 },
    ]);
  });

  it("groups notes into prototype time buckets", () => {
    expect(groupByTime(notes, now).map((group) => group.label)).toEqual([
      "Today",
      "Yesterday",
      "Earlier this week",
      "Earlier",
    ]);
  });

  it("formats relative time", () => {
    expect(relTime(now - 30_000, now)).toBe("just now");
    expect(relTime(now - 5 * 60_000, now)).toBe("5m ago");
    expect(relTime(now - 2 * 60 * 60_000, now)).toBe("2h ago");
    expect(relTime(now - day, now)).toBe("yesterday");
  });
});
