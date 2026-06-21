import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../services/notes", () => ({
  listNotes: vi.fn(),
}));

import { ApiError } from "../../services/http";
import type { NoteDTO } from "../../services/notes";
import { listNotes } from "../../services/notes";

import { useNotes } from "./useNotes";

const listNotesMock = vi.mocked(listNotes);

function dto(overrides: Partial<NoteDTO> = {}): NoteDTO {
  return {
    id: "n1",
    title: "Unused by adapter",
    content: "# Hello",
    tags: [],
    createdAt: "2024-01-15T10:30:00Z",
    updatedAt: "2024-02-20T08:00:00Z",
    ...overrides,
  };
}

describe("useNotes", () => {
  beforeEach(() => {
    const { notes, loading, error } = useNotes();
    notes.value = [];
    loading.value = false;
    error.value = null;
    listNotesMock.mockReset();
  });

  it("fetchNotes maps NoteDTO[] to NoteMock[]: ISO strings to epoch ms, backend tags preserved", async () => {
    listNotesMock.mockResolvedValue([
      dto({
        id: "a",
        tags: ["draft", "work"],
        createdAt: "2024-01-15T10:30:00Z",
        updatedAt: "2024-02-20T08:00:00Z",
      }),
      dto({
        id: "b",
        content: "# Two",
        tags: ["ideas"],
        createdAt: "2023-12-01T00:00:00Z",
        updatedAt: "2023-12-02T12:00:00Z",
      }),
    ]);

    await useNotes().fetchNotes();

    const { notes } = useNotes();
    expect(notes.value).toEqual([
      {
        id: "a",
        content: "# Hello",
        tags: ["draft", "work"],
        createdAt: Date.parse("2024-01-15T10:30:00Z"),
        updatedAt: Date.parse("2024-02-20T08:00:00Z"),
      },
      {
        id: "b",
        content: "# Two",
        tags: ["ideas"],
        createdAt: Date.parse("2023-12-01T00:00:00Z"),
        updatedAt: Date.parse("2023-12-02T12:00:00Z"),
      },
    ]);
    // Explicit epoch-ms equality assertions for the oracle.
    expect(notes.value[0].createdAt).toBe(Date.parse("2024-01-15T10:30:00Z"));
    expect(notes.value[0].updatedAt).toBe(Date.parse("2024-02-20T08:00:00Z"));
    expect(notes.value[0].tags).toEqual(["draft", "work"]);
  });

  it("fetchNotes toggles loading true during the call and false after success", async () => {
    const { loading } = useNotes();
    expect(loading.value).toBe(false);

    let resolveList!: (value: NoteDTO[]) => void;
    listNotesMock.mockReturnValue(
      new Promise<NoteDTO[]>((resolve) => {
        resolveList = resolve;
      }),
    );

    const pending = useNotes().fetchNotes();
    expect(loading.value).toBe(true);

    resolveList([dto()]);
    await pending;

    expect(loading.value).toBe(false);
  });

  it("fetchNotes resets loading to false on rejection too", async () => {
    const { loading } = useNotes();
    listNotesMock.mockRejectedValue(new ApiError(500, "boom"));

    await useNotes().fetchNotes();

    expect(loading.value).toBe(false);
  });

  it("on listNotes rejection, error is set to ApiError.detail and notes are left unchanged", async () => {
    const { notes, error } = useNotes();
    notes.value = [
      {
        id: "seed",
        content: "# seeded",
        tags: ["x"],
        createdAt: 1,
        updatedAt: 2,
      },
    ];
    const before = [...notes.value];

    listNotesMock.mockRejectedValue(new ApiError(500, "boom"));

    await useNotes().fetchNotes();

    expect(error.value).toBe("boom");
    expect(notes.value).toEqual(before);
  });

  it("useNotes returns the same refs across calls (module-singleton)", () => {
    const a = useNotes();
    const b = useNotes();

    expect(a.notes).toBe(b.notes);
    expect(a.loading).toBe(b.loading);
    expect(a.error).toBe(b.error);
    expect(a.fetchNotes).toBe(b.fetchNotes);
  });
});
