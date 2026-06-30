import { enableAutoUnmount, flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useAuth } from "@/features/auth/useAuth";

// Unmount every mounted wrapper after each test. Without this, AppShell
// instances from earlier tests stay alive and their watch(isAuthenticated)
// hooks react to the shared auth ref, opening extra event streams.
enableAutoUnmount(afterEach);
import { mockNotes } from "@/features/notes/mockNotes";
import { extractTitle } from "@/features/notes/noteMockHelpers";
import { useSettings } from "@/features/settings/useSettings";

import AppShell from "../AppShell.vue";

// The note-events service is mocked so AppShell's live-refresh wiring can be
// driven directly (capture the handlers it registers, fire events, assert
// teardown) without opening a real stream.
const noteEventsMock = vi.hoisted(() => ({ open: vi.fn() }));
vi.mock("@/services/noteEvents", () => ({
  NOTE_EVENTS_PATH: "/notes/events",
  openNoteEventStream: noteEventsMock.open,
}));

// useAuth is mocked with a controllable, reactive isAuthenticated (default
// false, so the existing unauthenticated tests never start the stream).
vi.mock("@/features/auth/useAuth", async () => {
  const { ref } = await import("vue");
  const isAuthenticated = ref(false);
  const user = ref<{ username: string } | null>(null);
  const logout = vi.fn().mockResolvedValue(undefined);
  return { useAuth: () => ({ isAuthenticated, user, logout }) };
});

/** Mutate the mocked, reactive auth state. */
function setAuthenticated(value: boolean): void {
  (
    useAuth() as unknown as { isAuthenticated: { value: boolean } }
  ).isAuthenticated.value = value;
}

interface CapturedStreamHandlers {
  onEvent: (event: { kind: string; note_id: string }) => void;
  onError?: (error: unknown) => void;
}

/** Read back the handlers AppShell's composable passed to the opened stream. */
function lastStreamHandlers(): CapturedStreamHandlers {
  const calls = noteEventsMock.open.mock.calls;
  return calls[calls.length - 1][0] as CapturedStreamHandlers;
}

/** Count GET requests to the notes collection in a stubbed fetch mock. */
function noteListGetCount(fetchMock: ReturnType<typeof vi.fn>): number {
  return fetchMock.mock.calls.filter(
    ([url, init]) =>
      (init?.method ?? "GET").toUpperCase() === "GET" &&
      String(url).includes("/notes/"),
  ).length;
}

const noteDtos = mockNotes.map((note) => ({
  id: note.id,
  title: extractTitle(note.content),
  content: note.content,
  tags: note.tags,
  createdAt: new Date(note.createdAt).toISOString(),
  updatedAt: new Date(note.updatedAt).toISOString(),
}));

const createdNoteDto = {
  id: "note-created-by-backend",
  title: "Backend Created",
  content: "# Backend Created\n\nFrom the server.",
  tags: [],
  createdAt: "2026-06-21T10:00:00.000Z",
  updatedAt: "2026-06-21T10:00:01.000Z",
};

const accountInfoDto = {
  username: "ada",
  email: "ada@example.com",
  created_at: "2024-01-15T10:30:00.000Z",
  notes_count: 7,
  auth_provider: "local",
};

function fetchStub(url: string | URL | Request, init?: RequestInit) {
  const method = (init?.method ?? "GET").toUpperCase();
  if (method === "GET" && String(url).includes("/notes/")) {
    return Promise.resolve(
      new Response(JSON.stringify(noteDtos), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  }
  if (method === "GET" && String(url).includes("/settings/user-info")) {
    return Promise.resolve(
      new Response(JSON.stringify(accountInfoDto), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  }
  if (method === "POST" && String(url).includes("/notes/")) {
    return Promise.resolve(
      new Response(JSON.stringify(createdNoteDto), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  }
  if (method === "PUT" && String(url).includes("/notes/")) {
    const body = JSON.parse(String(init?.body ?? "{}")) as {
      content?: string;
      tags?: string[];
    };
    return Promise.resolve(
      new Response(
        JSON.stringify({
          id: "n1",
          title: "Updated",
          content: body.content ?? "# Updated\n\nSaved.",
          tags: ["draft", "journal"],
          createdAt: new Date(mockNotes[0].createdAt).toISOString(),
          updatedAt: "2026-06-21T10:30:00.000Z",
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );
  }
  if (method === "DELETE" && String(url).includes("/notes/")) {
    return Promise.resolve(
      new Response(
        JSON.stringify({
          message: "Note deleted successfully",
          deleted_id: String(url).split("/").pop(),
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );
  }
  return Promise.resolve(new Response("{}", { status: 200 }));
}

describe("AppShell", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
    const { userInfo, loading, error } = useSettings();
    userInfo.value = null;
    loading.value = false;
    error.value = null;
    setAuthenticated(false);
    noteEventsMock.open.mockReset();
    noteEventsMock.open.mockReturnValue({ close: vi.fn() });
    vi.stubGlobal("fetch", fetchStub);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("creates a backend note and switches to edit mode", async () => {
    const fetchMock = vi.fn(fetchStub);
    vi.stubGlobal("fetch", fetchMock);
    const wrapper = mount(AppShell);
    await flushPromises();

    await wrapper.get(".new-note-button").trigger("click");
    await flushPromises();

    expect(wrapper.get(".doc-title").text()).toBe("Backend Created");
    expect(wrapper.get(".mode-switch__status").text()).toContain("Editing");
    expect(wrapper.get(".note-card.is-active").text()).toContain(
      "Backend Created",
    );
    const postCall = fetchMock.mock.calls.find(
      ([url, init]) =>
        String(url).includes("/notes/") &&
        (init?.method ?? "GET").toUpperCase() === "POST",
    );
    expect(postCall).toBeTruthy();
    expect(JSON.parse(String(postCall?.[1]?.body))).toEqual({
      content: "# Untitled\n\n",
      tags: [],
    });
  });

  it("leaves the active note unchanged and shows an error when create fails", async () => {
    const fetchMock = vi.fn(
      (url: string | URL | Request, init?: RequestInit) => {
        const method = (init?.method ?? "GET").toUpperCase();
        if (method === "POST" && String(url).includes("/notes/")) {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: "create failed" }), {
              status: 500,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        return fetchStub(url, init);
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const wrapper = mount(AppShell);
    await flushPromises();

    const beforeTitle = wrapper.get(".doc-title").text();
    await wrapper.get(".new-note-button").trigger("click");
    await flushPromises();

    expect(wrapper.get(".doc-title").text()).toBe(beforeTitle);
    expect(wrapper.get(".action-error").text()).toBe("create failed");
  });

  it("opens settings from the user footer", async () => {
    const fetchMock = vi.fn(fetchStub);
    vi.stubGlobal("fetch", fetchMock);
    const wrapper = mount(AppShell);
    await flushPromises();

    await wrapper.get(".user-footer__main").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("Settings");
    expect(wrapper.text()).toContain("ada");
    expect(wrapper.text()).toContain("ada@example.com");
    expect(wrapper.text()).toContain("Local password");
    expect(wrapper.get(".user-footer").classes()).toContain("is-active");
    expect(
      fetchMock.mock.calls.some(([url]) =>
        String(url).includes("/settings/user-info"),
      ),
    ).toBe(true);
  });

  it("uses the header edit action to switch modes", async () => {
    const wrapper = mount(AppShell);
    await flushPromises();

    await wrapper.get('[aria-label="Switch to edit mode"]').trigger("click");

    expect(wrapper.get(".mode-switch__status").text()).toContain("Editing");
    expect(
      (
        wrapper.get('textarea[aria-label="Markdown content"]')
          .element as HTMLTextAreaElement
      ).value,
    ).toBe(mockNotes[0].content);
  });

  it("returns from edit mode to read mode from the header action", async () => {
    const wrapper = mount(AppShell);
    await flushPromises();

    await wrapper.get('[aria-label="Switch to edit mode"]').trigger("click");
    await wrapper.get('[aria-label="Return to read mode"]').trigger("click");

    expect(wrapper.get(".mode-switch__status").text()).toContain("Reading");
    expect(wrapper.find('[aria-label="Return to read mode"]').exists()).toBe(
      false,
    );
    expect(wrapper.find("textarea").exists()).toBe(false);
  });

  it("saves edited markdown through the backend and returns to read mode", async () => {
    const fetchMock = vi.fn(fetchStub);
    vi.stubGlobal("fetch", fetchMock);
    const wrapper = mount(AppShell);
    await flushPromises();

    await wrapper.get('[aria-label="Switch to edit mode"]').trigger("click");
    await wrapper
      .get('textarea[aria-label="Markdown content"]')
      .setValue("# Updated\n\nSaved body.");
    await wrapper.get(".note-editor").trigger("submit");
    await flushPromises();

    const putCall = fetchMock.mock.calls.find(
      ([url, init]) =>
        String(url).includes("/notes/n1") &&
        (init?.method ?? "GET").toUpperCase() === "PUT",
    );
    expect(putCall).toBeTruthy();
    expect(JSON.parse(String(putCall?.[1]?.body))).toEqual({
      content: "# Updated\n\nSaved body.",
    });
    expect(wrapper.get(".mode-switch__status").text()).toContain("Reading");
    expect(wrapper.get(".doc-title").text()).toBe("Updated");
    expect(wrapper.find("textarea").exists()).toBe(false);
  });

  it("discards draft edits when canceling", async () => {
    const wrapper = mount(AppShell);
    await flushPromises();

    await wrapper.get('[aria-label="Switch to edit mode"]').trigger("click");
    await wrapper
      .get('textarea[aria-label="Markdown content"]')
      .setValue("# Unsaved\n\nDraft.");
    const cancelButton = wrapper
      .findAll("button")
      .find((button) => button.text() === "Cancel");
    expect(cancelButton).toBeTruthy();
    await cancelButton!.trigger("click");

    expect(wrapper.get(".mode-switch__status").text()).toContain("Reading");
    expect(wrapper.get(".doc-title").text()).toBe("Morning Pages");
    expect(wrapper.text()).not.toContain("Unsaved");
  });

  it("keeps the draft visible and saved note unchanged when save fails", async () => {
    const fetchMock = vi.fn(
      (url: string | URL | Request, init?: RequestInit) => {
        const method = (init?.method ?? "GET").toUpperCase();
        if (method === "PUT" && String(url).includes("/notes/")) {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: "save failed" }), {
              status: 500,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        return fetchStub(url, init);
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const wrapper = mount(AppShell);
    await flushPromises();

    await wrapper.get('[aria-label="Switch to edit mode"]').trigger("click");
    await wrapper
      .get('textarea[aria-label="Markdown content"]')
      .setValue("# Failed save\n\nDraft.");
    await wrapper.get(".note-editor").trigger("submit");
    await flushPromises();

    expect(wrapper.get(".mode-switch__status").text()).toContain("Editing");
    expect((wrapper.get("textarea").element as HTMLTextAreaElement).value).toBe(
      "# Failed save\n\nDraft.",
    );
    expect(wrapper.get(".action-error").text()).toBe("save failed");

    await wrapper.get('[aria-label="Return to read mode"]').trigger("click");
    expect(wrapper.get(".doc-title").text()).toBe("Morning Pages");
  });

  it("renders the active note body as structured markdown", async () => {
    const wrapper = mount(AppShell);
    await flushPromises();

    expect(wrapper.get(".doc-title").text()).toBe("Morning Pages");
    expect(wrapper.get(".prose h2").text()).toBe("What it's for");
    expect(wrapper.find(".prose blockquote").exists()).toBe(true);
    expect(wrapper.findAll(".prose li")).toHaveLength(3);
    expect(wrapper.find(".note-body").exists()).toBe(false);
  });

  it("renders table and task-list markdown when selecting notes", async () => {
    const wrapper = mount(AppShell);
    await flushPromises();
    const cards = wrapper.findAll(".note-card");

    await cards
      .find((card) => card.text().includes("Reading list"))
      ?.trigger("click");
    expect(wrapper.find(".prose table").exists()).toBe(true);
    expect(wrapper.findAll(".prose th").map((cell) => cell.text())).toEqual([
      "Title",
      "Author",
      "Why",
    ]);

    await cards
      .find((card) => card.text().includes("Standup notes"))
      ?.trigger("click");
    const checkboxes = wrapper.findAll('.prose input[type="checkbox"]');
    expect(checkboxes).toHaveLength(3);
    expect(checkboxes[0].attributes("checked")).toBeDefined();
    expect(checkboxes[0].attributes("disabled")).toBeDefined();
  });

  it("filters notes by search and tag, then selects the remaining note", async () => {
    const wrapper = mount(AppShell);
    await flushPromises();

    await wrapper.get('input[type="search"]').setValue("standup");
    const noteList = wrapper.get(".note-list");
    expect(noteList.text()).toContain("Standup notes");
    expect(noteList.text()).not.toContain("Morning Pages");

    const logTag = wrapper
      .findAll(".tag-filter__tag")
      .find((button) => button.text().includes("log"));
    expect(logTag).toBeTruthy();
    await logTag?.trigger("click");
    expect(wrapper.text()).toContain("#log");

    await wrapper.get(".note-card").trigger("click");
    expect(wrapper.get(".doc-title").text()).toBe("Standup notes");
  });

  it("toggles a tag filter from the active note's meta row", async () => {
    const wrapper = mount(AppShell);
    await flushPromises();

    const metaTag = wrapper.get(".doc-tags .mini-tag-button");
    const tagLabel = metaTag.text();
    await metaTag.trigger("click");

    expect(wrapper.get(".tag-filter").text()).toContain(tagLabel.slice(1));
  });

  it("adds a raw tag from edit mode and trusts backend-normalized returned tags", async () => {
    const fetchMock = vi.fn(
      (url: string | URL | Request, init?: RequestInit) => {
        const method = (init?.method ?? "GET").toUpperCase();
        if (method === "PUT" && String(url).includes("/notes/n1")) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                id: "n1",
                title: "Morning Pages",
                content: mockNotes[0].content,
                tags: ["daily-log", "draft", "journal"],
                createdAt: new Date(mockNotes[0].createdAt).toISOString(),
                updatedAt: "2026-06-21T10:30:00.000Z",
              }),
              {
                status: 200,
                headers: { "Content-Type": "application/json" },
              },
            ),
          );
        }
        return fetchStub(url, init);
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const wrapper = mount(AppShell);
    await flushPromises();

    await wrapper.get('[aria-label="Switch to edit mode"]').trigger("click");
    await wrapper.get(".note-tag-editor input").setValue("  #Daily Log  ");
    await wrapper.get(".note-tag-editor__form").trigger("submit");
    await flushPromises();

    const putCall = fetchMock.mock.calls.find(
      ([url, init]) =>
        String(url).includes("/notes/n1") &&
        (init?.method ?? "GET").toUpperCase() === "PUT",
    );
    expect(putCall).toBeTruthy();
    expect(JSON.parse(String(putCall?.[1]?.body))).toEqual({
      tags: ["draft", "journal", "  #Daily Log  "],
    });
    expect(wrapper.get(".note-tag-editor").text()).toContain("#daily-log");
  });

  it("removes a tag from edit mode and prunes stale active filters", async () => {
    const fetchMock = vi.fn(
      (url: string | URL | Request, init?: RequestInit) => {
        const method = (init?.method ?? "GET").toUpperCase();
        if (method === "PUT" && String(url).includes("/notes/n1")) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                id: "n1",
                title: "Morning Pages",
                content: mockNotes[0].content,
                tags: ["draft"],
                createdAt: new Date(mockNotes[0].createdAt).toISOString(),
                updatedAt: "2026-06-21T10:30:00.000Z",
              }),
              {
                status: 200,
                headers: { "Content-Type": "application/json" },
              },
            ),
          );
        }
        return fetchStub(url, init);
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const wrapper = mount(AppShell);
    await flushPromises();

    const journalTag = wrapper
      .findAll(".doc-tags .mini-tag-button")
      .find((button) => button.text() === "#journal");
    expect(journalTag).toBeTruthy();
    await journalTag!.trigger("click");
    expect(wrapper.get(".tag-filter__tag.is-active").text()).toContain(
      "journal",
    );

    await wrapper.get('[aria-label="Switch to edit mode"]').trigger("click");
    await wrapper.get('[aria-label="Remove #journal"]').trigger("click");
    await flushPromises();

    const putCall = fetchMock.mock.calls.find(
      ([url, init]) =>
        String(url).includes("/notes/n1") &&
        (init?.method ?? "GET").toUpperCase() === "PUT",
    );
    expect(putCall).toBeTruthy();
    expect(JSON.parse(String(putCall?.[1]?.body))).toEqual({
      tags: ["draft"],
    });
    expect(wrapper.get(".note-tag-editor").text()).not.toContain("#journal");
    expect(wrapper.find(".tag-filter__tag.is-active").exists()).toBe(false);
  });

  it("leaves tags unchanged and shows an error when tag update fails", async () => {
    const fetchMock = vi.fn(
      (url: string | URL | Request, init?: RequestInit) => {
        const method = (init?.method ?? "GET").toUpperCase();
        if (method === "PUT" && String(url).includes("/notes/n1")) {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: "tag update failed" }), {
              status: 422,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        return fetchStub(url, init);
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const wrapper = mount(AppShell);
    await flushPromises();

    await wrapper.get('[aria-label="Switch to edit mode"]').trigger("click");
    await wrapper.get(".note-tag-editor input").setValue("bad/tag");
    await wrapper.get(".note-tag-editor__form").trigger("submit");
    await flushPromises();

    expect(wrapper.get(".action-error").text()).toBe("tag update failed");
    expect(wrapper.get(".note-tag-editor [role='alert']").text()).toBe(
      "tag update failed",
    );
    expect(wrapper.get(".note-tag-editor").text()).toContain("#draft");
    expect(wrapper.get(".note-tag-editor").text()).toContain("#journal");
  });

  it("opens the mobile drawer state and toggles the theme", async () => {
    const wrapper = mount(AppShell);
    await flushPromises();

    await wrapper.get('[aria-label="Menu"]').trigger("click");
    expect(wrapper.get(".sidebar-drawer").classes()).toContain("is-open");

    await wrapper.get('[aria-label="Close navigation"]').trigger("click");
    expect(wrapper.get(".sidebar-drawer").classes()).not.toContain("is-open");

    await wrapper.get('[aria-label="Switch to Desk lamp"]').trigger("click");
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  it("runs copy, export, and delete actions from the note overflow menu", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText } });

    const createObjectURL = vi.fn().mockReturnValue("blob:note");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { createObjectURL, revokeObjectURL });
    const anchorClick = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);

    const wrapper = mount(AppShell);
    await flushPromises();

    const openMenu = async () => {
      await wrapper.get('[aria-label="More"]').trigger("click");
    };
    const menuItem = (label: string) =>
      wrapper
        .findAll('[role="menuitem"]')
        .find((item) => item.text().includes(label));

    await openMenu();
    await menuItem("Copy")?.trigger("click");
    expect(writeText).toHaveBeenCalledOnce();

    await openMenu();
    await menuItem("Export")?.trigger("click");
    expect(createObjectURL).toHaveBeenCalledOnce();
    expect(anchorClick).toHaveBeenCalledOnce();

    await openMenu();
    await menuItem("Delete")?.trigger("click");
    await flushPromises();
    expect(wrapper.get(".doc-title").text()).not.toBe("Morning Pages");

    vi.unstubAllGlobals();
  });

  it("keeps the active note visible and shows an error when delete fails", async () => {
    const fetchMock = vi.fn(
      (url: string | URL | Request, init?: RequestInit) => {
        const method = (init?.method ?? "GET").toUpperCase();
        if (method === "DELETE" && String(url).includes("/notes/")) {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: "delete failed" }), {
              status: 500,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        return fetchStub(url, init);
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const wrapper = mount(AppShell);
    await flushPromises();

    await wrapper.get('[aria-label="More"]').trigger("click");
    await wrapper
      .findAll('[role="menuitem"]')
      .find((item) => item.text().includes("Delete"))
      ?.trigger("click");
    await flushPromises();

    expect(wrapper.get(".doc-title").text()).toBe("Morning Pages");
    expect(wrapper.get(".action-error").text()).toBe("delete failed");
  });
});

describe("AppShell live refresh", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
    const { userInfo, loading, error } = useSettings();
    userInfo.value = null;
    loading.value = false;
    error.value = null;
    setAuthenticated(false);
    noteEventsMock.open.mockReset();
    noteEventsMock.open.mockReturnValue({ close: vi.fn() });
    vi.stubGlobal("fetch", fetchStub);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("starts the note-events stream after the initial fetch and stops it on unmount", async () => {
    setAuthenticated(true);
    const close = vi.fn();
    noteEventsMock.open.mockReturnValue({ close });
    const fetchMock = vi.fn(fetchStub);
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(AppShell);
    await flushPromises();

    expect(noteEventsMock.open).toHaveBeenCalledTimes(1);
    // The initial notes list was loaded (the stream starts only after it).
    expect(noteListGetCount(fetchMock)).toBeGreaterThanOrEqual(1);

    wrapper.unmount();
    expect(close).toHaveBeenCalledTimes(1);
  });

  it("does not start the stream when unauthenticated", async () => {
    mount(AppShell);
    await flushPromises();

    expect(noteEventsMock.open).not.toHaveBeenCalled();
  });

  it("stops the stream and cancels pending refetches when authentication is lost", async () => {
    setAuthenticated(true);
    const close = vi.fn();
    noteEventsMock.open.mockReturnValue({ close });
    mount(AppShell);
    await flushPromises();
    expect(noteEventsMock.open).toHaveBeenCalledTimes(1);

    setAuthenticated(false);
    await flushPromises();

    expect(close).toHaveBeenCalledTimes(1);
  });

  it("coalesces multiple quick note events into a single debounced refetch", async () => {
    setAuthenticated(true);
    const fetchMock = vi.fn(fetchStub);
    vi.stubGlobal("fetch", fetchMock);
    mount(AppShell);
    await flushPromises();
    const initialGets = noteListGetCount(fetchMock);

    vi.useFakeTimers();
    const handlers = lastStreamHandlers();
    handlers.onEvent({ kind: "updated", note_id: "n1" });
    handlers.onEvent({ kind: "created", note_id: "n2" });
    handlers.onEvent({ kind: "deleted", note_id: "n3" });
    await vi.advanceTimersByTimeAsync(250);
    vi.useRealTimers();
    await flushPromises();

    expect(noteListGetCount(fetchMock) - initialGets).toBe(1);
  });

  it("reselects a remaining note when the active note disappears from a refresh", async () => {
    setAuthenticated(true);
    const keptDto = {
      id: "kept",
      title: "Kept Note",
      content: "# Kept Note\n\nStill here.",
      tags: [],
      createdAt: "2026-06-20T10:00:00.000Z",
      updatedAt: "2026-06-20T10:00:00.000Z",
    };
    let getCount = 0;
    const fetchMock = vi.fn(
      (url: string | URL | Request, init?: RequestInit) => {
        const method = (init?.method ?? "GET").toUpperCase();
        if (method === "GET" && String(url).includes("/notes/")) {
          getCount += 1;
          const body = getCount === 1 ? noteDtos : [keptDto];
          return Promise.resolve(
            new Response(JSON.stringify(body), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        return fetchStub(url, init);
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(AppShell);
    await flushPromises();
    expect(wrapper.get(".doc-title").text()).toBe("Morning Pages");

    vi.useFakeTimers();
    lastStreamHandlers().onEvent({ kind: "deleted", note_id: "n1" });
    await vi.advanceTimersByTimeAsync(250);
    vi.useRealTimers();
    await flushPromises();

    expect(wrapper.get(".doc-title").text()).toBe("Kept Note");
  });

  it("clears the selection to the empty state when a refresh returns no notes", async () => {
    setAuthenticated(true);
    let getCount = 0;
    const fetchMock = vi.fn(
      (url: string | URL | Request, init?: RequestInit) => {
        const method = (init?.method ?? "GET").toUpperCase();
        if (method === "GET" && String(url).includes("/notes/")) {
          getCount += 1;
          return Promise.resolve(
            new Response(JSON.stringify(getCount === 1 ? noteDtos : []), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            }),
          );
        }
        return fetchStub(url, init);
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(AppShell);
    await flushPromises();
    expect(wrapper.find(".doc-title").exists()).toBe(true);

    vi.useFakeTimers();
    lastStreamHandlers().onEvent({ kind: "deleted", note_id: "n1" });
    await vi.advanceTimersByTimeAsync(250);
    vi.useRealTimers();
    await flushPromises();

    expect(wrapper.find(".empty-state").exists()).toBe(true);
    expect(wrapper.find(".doc-title").exists()).toBe(false);
  });

  it("keeps the notes list visible when the stream reports an error", async () => {
    setAuthenticated(true);
    const wrapper = mount(AppShell);
    await flushPromises();
    const before = wrapper.get(".doc-title").text();

    lastStreamHandlers().onError?.(new Error("stream down"));
    await flushPromises();

    expect(wrapper.get(".doc-title").text()).toBe(before);
  });
});
