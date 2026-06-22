import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../services/notes", () => ({
  createNote: vi.fn(),
  deleteNote: vi.fn(),
  listNotes: vi.fn(),
  updateNote: vi.fn(),
}));

import { ApiError } from "../../services/http";
import type { NoteDTO } from "../../services/notes";
import {
  createNote,
  deleteNote,
  listNotes,
  updateNote,
} from "../../services/notes";

import { useNotes } from "./useNotes";

const listNotesMock = vi.mocked(listNotes);
const createNoteMock = vi.mocked(createNote);
const deleteNoteMock = vi.mocked(deleteNote);
const updateNoteMock = vi.mocked(updateNote);

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
    const {
      notes,
      loading,
      error,
      creating,
      updating,
      deletingId,
      mutationError,
    } = useNotes();
    notes.value = [];
    loading.value = false;
    error.value = null;
    creating.value = false;
    updating.value = false;
    deletingId.value = null;
    mutationError.value = null;
    listNotesMock.mockReset();
    createNoteMock.mockReset();
    deleteNoteMock.mockReset();
    updateNoteMock.mockReset();
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
    expect(a.creating).toBe(b.creating);
    expect(a.updating).toBe(b.updating);
    expect(a.deletingId).toBe(b.deletingId);
    expect(a.mutationError).toBe(b.mutationError);
    expect(a.fetchNotes).toBe(b.fetchNotes);
    expect(a.createNote).toBe(b.createNote);
    expect(a.updateNote).toBe(b.updateNote);
    expect(a.deleteNote).toBe(b.deleteNote);
    expect(a.clearMutationError).toBe(b.clearMutationError);
  });

  it("createNote maps the returned NoteDTO, prepends it, and preserves backend fields", async () => {
    const { notes } = useNotes();
    notes.value = [
      {
        id: "existing",
        content: "# Existing",
        tags: ["old"],
        createdAt: 1,
        updatedAt: 2,
      },
    ];
    createNoteMock.mockResolvedValue(
      dto({
        id: "backend-id",
        content: "# Untitled\n\n",
        tags: ["draft"],
        createdAt: "2026-06-21T10:00:00Z",
        updatedAt: "2026-06-21T10:00:01Z",
      }),
    );

    const created = await useNotes().createNote({
      content: "# Untitled\n\n",
      tags: ["draft"],
    });

    expect(createNoteMock).toHaveBeenCalledWith({
      content: "# Untitled\n\n",
      tags: ["draft"],
    });
    expect(created).toEqual({
      id: "backend-id",
      content: "# Untitled\n\n",
      tags: ["draft"],
      createdAt: Date.parse("2026-06-21T10:00:00Z"),
      updatedAt: Date.parse("2026-06-21T10:00:01Z"),
    });
    expect(notes.value[0]).toEqual(created);
    expect(notes.value[1].id).toBe("existing");
  });

  it("createNote toggles creating and resets it after success", async () => {
    const { creating } = useNotes();
    let resolveCreate!: (value: NoteDTO) => void;
    createNoteMock.mockReturnValue(
      new Promise<NoteDTO>((resolve) => {
        resolveCreate = resolve;
      }),
    );

    const pending = useNotes().createNote();
    expect(creating.value).toBe(true);

    resolveCreate(dto({ id: "created" }));
    await pending;

    expect(creating.value).toBe(false);
  });

  it("on createNote rejection, mutationError is set and notes are left unchanged", async () => {
    const { notes, mutationError } = useNotes();
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
    createNoteMock.mockRejectedValue(new ApiError(500, "create failed"));

    await expect(useNotes().createNote()).rejects.toBeInstanceOf(ApiError);

    expect(mutationError.value).toBe("create failed");
    expect(notes.value).toEqual(before);
  });

  it("updateNote replaces only the matching note with the returned backend fields", async () => {
    const { notes } = useNotes();
    notes.value = [
      {
        id: "target",
        content: "# Old",
        tags: ["keep"],
        createdAt: 1,
        updatedAt: 2,
      },
      {
        id: "other",
        content: "# Other",
        tags: [],
        createdAt: 3,
        updatedAt: 4,
      },
    ];
    updateNoteMock.mockResolvedValue(
      dto({
        id: "target",
        content: "# Updated\n\nSaved.",
        tags: ["keep"],
        createdAt: "2026-06-21T10:00:00Z",
        updatedAt: "2026-06-21T10:30:00Z",
      }),
    );

    const updated = await useNotes().updateNote("target", {
      content: "# Updated\n\nSaved.",
    });

    expect(updateNoteMock).toHaveBeenCalledWith("target", {
      content: "# Updated\n\nSaved.",
    });
    expect(notes.value).toEqual([
      updated,
      {
        id: "other",
        content: "# Other",
        tags: [],
        createdAt: 3,
        updatedAt: 4,
      },
    ]);
  });

  it("updateNote passes raw tags through and stores backend-normalized returned tags", async () => {
    const { notes } = useNotes();
    notes.value = [
      {
        id: "target",
        content: "# Old",
        tags: ["draft"],
        createdAt: 1,
        updatedAt: 2,
      },
    ];
    updateNoteMock.mockResolvedValue(
      dto({
        id: "target",
        content: "# Old",
        tags: ["daily-log", "draft"],
        createdAt: "2026-06-21T10:00:00Z",
        updatedAt: "2026-06-21T10:30:00Z",
      }),
    );

    const payload = { tags: ["draft", "  #Daily Log  "] };
    const updated = await useNotes().updateNote("target", payload);

    expect(updateNoteMock).toHaveBeenCalledWith("target", payload);
    expect(updated.tags).toEqual(["daily-log", "draft"]);
    expect(notes.value[0].tags).toEqual(["daily-log", "draft"]);
  });

  it("on updateNote rejection, mutationError is set and notes are left unchanged", async () => {
    const { notes, mutationError } = useNotes();
    notes.value = [
      {
        id: "target",
        content: "# Old",
        tags: [],
        createdAt: 1,
        updatedAt: 2,
      },
    ];
    const before = [...notes.value];
    updateNoteMock.mockRejectedValue(new ApiError(500, "save failed"));

    await expect(
      useNotes().updateNote("target", { content: "# Updated" }),
    ).rejects.toBeInstanceOf(ApiError);

    expect(mutationError.value).toBe("save failed");
    expect(notes.value).toEqual(before);
  });

  it("clearMutationError resets mutationError", () => {
    const { mutationError, clearMutationError } = useNotes();
    mutationError.value = "boom";

    clearMutationError();

    expect(mutationError.value).toBeNull();
  });

  it("deleteNote removes the note only after backend success", async () => {
    const { notes } = useNotes();
    notes.value = [
      {
        id: "target",
        content: "# Old",
        tags: [],
        createdAt: 1,
        updatedAt: 2,
      },
      {
        id: "other",
        content: "# Other",
        tags: [],
        createdAt: 3,
        updatedAt: 4,
      },
    ];
    deleteNoteMock.mockResolvedValue({
      message: "Note deleted successfully",
      deleted_id: "target",
    });

    await useNotes().deleteNote("target");

    expect(deleteNoteMock).toHaveBeenCalledWith("target");
    expect(notes.value.map((note) => note.id)).toEqual(["other"]);
  });

  it("deleteNote leaves notes unchanged on backend failure", async () => {
    const { notes, mutationError } = useNotes();
    notes.value = [
      {
        id: "target",
        content: "# Old",
        tags: [],
        createdAt: 1,
        updatedAt: 2,
      },
    ];
    const before = [...notes.value];
    deleteNoteMock.mockRejectedValue(new ApiError(500, "delete failed"));

    await expect(useNotes().deleteNote("target")).rejects.toBeInstanceOf(
      ApiError,
    );

    expect(mutationError.value).toBe("delete failed");
    expect(notes.value).toEqual(before);
  });

  it("deleteNote rejects and preserves notes when backend confirms a different id", async () => {
    const { notes, mutationError } = useNotes();
    notes.value = [
      {
        id: "target",
        content: "# Old",
        tags: [],
        createdAt: 1,
        updatedAt: 2,
      },
    ];
    deleteNoteMock.mockResolvedValue({
      message: "Note deleted successfully",
      deleted_id: "other",
    });

    await expect(useNotes().deleteNote("target")).rejects.toMatchObject({
      status: 500,
      detail: "Delete response did not match requested note",
    });

    expect(mutationError.value).toBe(
      "Delete response did not match requested note",
    );
    expect(notes.value.map((note) => note.id)).toEqual(["target"]);
  });
});
