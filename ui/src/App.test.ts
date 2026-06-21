import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

import { mockNotes } from "@/features/notes/mockNotes";
import { extractTitle } from "@/features/notes/noteMockHelpers";

import App from "./App.vue";

// NoteResponse[] shape — ISO timestamps plus normalized backend tags.
const noteDtos = mockNotes.map((note) => ({
  id: note.id,
  title: extractTitle(note.content),
  content: note.content,
  tags: note.tags,
  createdAt: new Date(note.createdAt).toISOString(),
  updatedAt: new Date(note.updatedAt).toISOString(),
}));

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
  return Promise.resolve(new Response("{}", { status: 200 }));
}

// Controllable auth state shared with the mocked `useAuth` composable. App
// renders AppShell only once the session is restored AND the user is
// authenticated; otherwise it shows LoginView.
const isAuthenticated = ref(false);
const user = ref<{ username: string } | null>(null);
const error = ref<string | null>(null);
const pending = ref(false);
const restoreSession = vi.fn().mockResolvedValue(undefined);
const login = vi.fn().mockResolvedValue(true);
const logout = vi.fn().mockResolvedValue(undefined);

vi.mock("@/features/auth/useAuth", () => ({
  useAuth: () => ({
    isAuthenticated,
    user,
    error,
    pending,
    restoreSession,
    login,
    logout,
  }),
}));

beforeEach(() => {
  localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
  isAuthenticated.value = false;
  user.value = null;
  error.value = null;
  pending.value = false;
  restoreSession.mockClear();
  vi.stubGlobal("fetch", fetchStub);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("restores the session on mount", async () => {
    mount(App);
    await flushPromises();

    expect(restoreSession).toHaveBeenCalledTimes(1);
  });

  it("renders LoginView, not the app shell, when unauthenticated", async () => {
    const wrapper = mount(App);
    await flushPromises();

    expect(wrapper.find(".auth-shell").exists()).toBe(true);
    expect(wrapper.find(".app-shell").exists()).toBe(false);
    expect(wrapper.find(".wordmark").exists()).toBe(false);
  });

  it("renders the V2 app shell with notes and topbar controls when authenticated", async () => {
    isAuthenticated.value = true;
    user.value = { username: "jamie" };

    const wrapper = mount(App);
    await flushPromises();

    expect(wrapper.find(".auth-shell").exists()).toBe(false);
    expect(wrapper.get(".wordmark").text()).toBe("ParchMark");
    expect(wrapper.get(".doc-title").text()).toBe("Morning Pages");
    expect(wrapper.get(".mode-switch__status").text()).toContain("Reading");
    expect(wrapper.find('[aria-label="Switch to edit mode"]').exists()).toBe(
      true,
    );
    expect(wrapper.get(".prose").text()).toContain("Today");
    expect(wrapper.find(".prose blockquote").exists()).toBe(true);
  });
});
