<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import MarkdownProse from "@/features/notes/MarkdownProse.vue";
import NoteEditor from "@/features/notes/NoteEditor.vue";
import NoteTagEditor from "@/features/notes/NoteTagEditor.vue";
import {
  allTags,
  extractTitle,
  readingTime,
  relTime,
  wordCount,
} from "@/features/notes/noteMockHelpers";
import { useNotes } from "@/features/notes/useNotes";

import AppTopbar from "./AppTopbar.vue";
import type { NoteMenuAction, NoteMode } from "./headerTypes";
import SidebarDrawer from "./SidebarDrawer.vue";

const {
  notes,
  loading,
  error,
  creating,
  updating,
  deletingId,
  mutationError,
  clearMutationError,
  fetchNotes,
  createNote: persistNote,
  updateNote: persistNoteUpdate,
  deleteNote: persistDeleteNote,
} = useNotes();
const activeId = ref<string | null>(null);
const mode = ref<NoteMode>("read");
const search = ref("");
const activeTags = ref<string[]>([]);
const menuOpen = ref(false);
const navOpen = ref(false);
const settingsActive = ref(false);
const draftContent = ref("");
const storedTheme =
  typeof localStorage === "undefined" ? null : localStorage.getItem("pm_theme");
const theme = ref<"light" | "dark">(storedTheme === "dark" ? "dark" : "light");

watch(
  theme,
  (value) => {
    document.documentElement.dataset.theme = value;
    try {
      localStorage.setItem("pm_theme", value);
    } catch {
      // Storage is optional in embedded/test contexts.
    }
  },
  { immediate: true },
);

onMounted(async () => {
  await fetchNotes();
  const newest = notes.value
    .slice()
    .sort((left, right) => right.updatedAt - left.updatedAt)[0];
  activeId.value = newest?.id ?? null;
});

const tags = computed(() => allTags(notes.value));

const filteredNotes = computed(() => {
  const query = search.value.trim().toLowerCase();

  return notes.value
    .filter((note) => {
      if (
        activeTags.value.length > 0 &&
        !activeTags.value.some((tag) => note.tags.includes(tag))
      ) {
        return false;
      }

      if (!query) return true;

      const haystack =
        `${extractTitle(note.content)} ${note.content}`.toLowerCase();
      return haystack.includes(query);
    })
    .sort((left, right) => right.updatedAt - left.updatedAt);
});

const activeNote = computed(
  () => notes.value.find((note) => note.id === activeId.value) ?? null,
);

const activeTitle = computed(() =>
  activeNote.value ? extractTitle(activeNote.value.content) : "Untitled",
);

const draftDirty = computed(
  () =>
    activeNote.value !== null &&
    draftContent.value !== activeNote.value.content,
);
const draftValid = computed(() => draftContent.value.trim().length >= 4);
const canSaveDraft = computed(
  () => draftDirty.value && draftValid.value && !updating.value,
);

function selectNote(id: string) {
  activeId.value = id;
  mode.value = "read";
  draftContent.value = "";
  clearMutationError();
  menuOpen.value = false;
  navOpen.value = false;
  settingsActive.value = false;
}

async function createNote() {
  if (creating.value) return;

  try {
    const note = await persistNote({ content: "# Untitled\n\n", tags: [] });

    activeId.value = note.id;
    draftContent.value = note.content;
    mode.value = "edit";
    navOpen.value = false;
    settingsActive.value = false;
  } catch {
    // The notes store owns the visible mutation error and leaves state intact.
  }
}

function toggleTag(tag: string) {
  activeTags.value = activeTags.value.includes(tag)
    ? activeTags.value.filter((activeTag) => activeTag !== tag)
    : [...activeTags.value, tag];
}

function pruneUnavailableActiveTags() {
  const availableTags = new Set(tags.value.map(({ tag }) => tag));
  activeTags.value = activeTags.value.filter((tag) => availableTags.has(tag));
}

function openSettings() {
  settingsActive.value = true;
  draftContent.value = "";
  clearMutationError();
  navOpen.value = false;
  menuOpen.value = false;
}

function toggleTheme() {
  theme.value = theme.value === "dark" ? "light" : "dark";
}

function startEdit() {
  if (!activeNote.value) return;
  draftContent.value = activeNote.value.content;
  clearMutationError();
  mode.value = "edit";
}

function cancelEdit() {
  draftContent.value = activeNote.value?.content ?? "";
  clearMutationError();
  mode.value = "read";
}

function handleModeUpdate(nextMode: NoteMode) {
  if (nextMode === "edit") {
    startEdit();
  } else {
    cancelEdit();
  }
}

async function saveDraft() {
  if (!activeNote.value || !canSaveDraft.value) return;

  const noteId = activeNote.value.id;
  try {
    const updated = await persistNoteUpdate(noteId, {
      content: draftContent.value,
    });
    activeId.value = updated.id;
    draftContent.value = updated.content;
    mode.value = "read";
  } catch {
    // The notes store owns the visible mutation error and leaves state intact.
  }
}

async function addTagToActiveNote(rawTag: string) {
  if (!activeNote.value || updating.value || rawTag.trim().length === 0) return;

  const note = activeNote.value;
  try {
    const updated = await persistNoteUpdate(note.id, {
      tags: [...note.tags, rawTag],
    });
    activeId.value = updated.id;
    pruneUnavailableActiveTags();
  } catch {
    // The notes store owns the visible mutation error and leaves state intact.
  }
}

async function removeTagFromActiveNote(tag: string) {
  if (!activeNote.value || updating.value) return;

  const note = activeNote.value;
  try {
    const updated = await persistNoteUpdate(note.id, {
      tags: note.tags.filter((noteTag) => noteTag !== tag),
    });
    activeId.value = updated.id;
    pruneUnavailableActiveTags();
  } catch {
    // The notes store owns the visible mutation error and leaves state intact.
  }
}

async function copyActiveMarkdown() {
  if (!activeNote.value || !navigator.clipboard) return;
  await navigator.clipboard.writeText(activeNote.value.content);
}

function exportActiveMarkdown() {
  if (!activeNote.value || typeof URL.createObjectURL !== "function") return;

  const slug = activeTitle.value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
  const blob = new Blob([activeNote.value.content], {
    type: "text/markdown;charset=utf-8",
  });
  const href = URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = href;
  anchor.download = `${slug || "note"}.md`;
  anchor.click();
  URL.revokeObjectURL(href);
}

async function deleteActiveNote() {
  if (!activeNote.value || deletingId.value === activeNote.value.id) return;

  const deletedId = activeNote.value.id;
  const deletedIndex = notes.value.findIndex((note) => note.id === deletedId);

  try {
    await persistDeleteNote(deletedId);
    const nextIndex = Math.min(deletedIndex, notes.value.length - 1);
    activeId.value =
      nextIndex >= 0 ? (notes.value[nextIndex]?.id ?? null) : null;
    draftContent.value = "";
    mode.value = "read";
  } catch {
    // The notes store owns the visible mutation error and leaves state intact.
  }
}

function handleNoteMenuAction(id: NoteMenuAction) {
  if (id === "copy") {
    void copyActiveMarkdown();
  }
  if (id === "export") {
    exportActiveMarkdown();
  }
  if (id === "delete") {
    void deleteActiveNote();
  }
  menuOpen.value = false;
}
</script>

<template>
  <div class="app-shell" :class="{ 'is-nav-open': navOpen }">
    <SidebarDrawer
      v-model:search="search"
      :notes="filteredNotes"
      :activeId="activeId"
      :tags="tags"
      :activeTags="activeTags"
      :settingsActive="settingsActive"
      :open="navOpen"
      :loading="loading"
      :error="error"
      @select="selectNote"
      @newNote="createNote"
      @toggleTag="toggleTag"
      @openSettings="openSettings"
      @retry="fetchNotes"
    />

    <button
      v-if="navOpen"
      class="scrim"
      type="button"
      aria-label="Close navigation"
      @click="navOpen = false"
    />

    <main class="main-pane">
      <AppTopbar
        v-model:menuOpen="menuOpen"
        :mode="mode"
        :activeNote="settingsActive ? null : activeNote"
        :activeTags="activeTags"
        :title="activeTitle"
        :theme="theme"
        @openDrawer="navOpen = true"
        @update:mode="handleModeUpdate"
        @toggleTheme="toggleTheme"
        @noteAction="handleNoteMenuAction"
      />

      <div v-if="mutationError" class="action-error" role="alert">
        {{ mutationError }}
      </div>

      <section v-if="settingsActive" class="settings-placeholder">
        <h1>Settings</h1>
        <p>Profile and workspace controls are queued for a later slice.</p>
      </section>

      <section v-else-if="activeNote" class="read-pane" aria-live="polite">
        <div class="measure">
          <h1 class="doc-title">{{ activeTitle }}</h1>
          <div class="doc-meta">
            <span>{{ readingTime(activeNote.content) }} min read</span>
            <span aria-hidden="true" class="dot" />
            <span>{{ wordCount(activeNote.content) }} words</span>
            <span aria-hidden="true" class="dot" />
            <span>Edited {{ relTime(activeNote.updatedAt) }}</span>
            <span
              v-if="mode === 'read' && activeNote.tags.length"
              class="doc-tags"
            >
              <button
                v-for="tag in activeNote.tags"
                :key="tag"
                class="mini-tag-button"
                type="button"
                @click="toggleTag(tag)"
              >
                #{{ tag }}
              </button>
            </span>
          </div>
          <div class="rule" />
          <NoteTagEditor
            v-if="mode === 'edit'"
            :tags="activeNote.tags"
            :saving="updating"
            @addTag="addTagToActiveNote"
            @removeTag="removeTagFromActiveNote"
          />
          <NoteEditor
            v-if="mode === 'edit'"
            v-model="draftContent"
            :canSave="canSaveDraft"
            :saving="updating"
            :error="mutationError"
            @save="saveDraft"
            @cancel="cancelEdit"
          />
          <MarkdownProse v-else :markdown="activeNote.content" />
        </div>
      </section>

      <section v-else class="empty-state">
        <div>
          <div class="empty-state__mark">P</div>
          <h1>No notes match.</h1>
          <p>Adjust the search or clear the active tag filters.</p>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  --app-sidebar-width: var(--sidebar-width);

  position: relative;
  display: grid;
  grid-template-columns: var(--app-sidebar-width) minmax(0, 1fr);
  height: 100vh;
  overflow: hidden;
  background: var(--canvas);
}

.app-shell::before {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  content: "";
  background-image: radial-gradient(var(--paper-grain) 1px, transparent 1.3px);
  background-size: 24px 24px;
}

.main-pane {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.action-error {
  margin: 14px 28px 0;
  padding: 10px 12px;
  color: var(--danger);
  font-size: 13px;
  background: var(--danger-surface);
  border: 1px solid color-mix(in srgb, var(--danger) 24%, transparent);
  border-radius: var(--r);
}

.read-pane {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.measure {
  max-width: 780px;
  padding: 54px 56px 110px;
  margin: 0 auto;
}

.doc-title {
  margin: 0 0 10px;
  color: var(--text);
  font-family: var(--serif);
  font-size: 42px;
  font-weight: 700;
  line-height: 1.12;
}

.doc-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  color: var(--muted);
  font-size: 12.5px;
}

.dot {
  width: 4px;
  height: 4px;
  background: var(--line-2);
  border-radius: 50%;
}

.doc-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.mini-tag-button {
  padding: 1.5px 7px;
  color: var(--accent-600);
  font-size: 10.5px;
  font-weight: 500;
  background: var(--focus-ring);
  border: none;
  border-radius: 12px;
}

.mini-tag-button:hover,
.mini-tag-button:focus-visible {
  color: var(--accent);
  outline: none;
}

.rule {
  height: 1px;
  margin: 26px 0;
  background: var(--line-2);
}

.settings-placeholder,
.empty-state {
  display: grid;
  flex: 1;
  place-items: center;
  padding: 40px;
  text-align: center;
}

.settings-placeholder h1,
.empty-state h1 {
  margin: 0 0 8px;
  color: var(--text);
  font-family: var(--serif);
  font-size: 34px;
}

.settings-placeholder p,
.empty-state p {
  max-width: 340px;
  margin: 0;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.55;
}

.empty-state__mark {
  margin-bottom: 10px;
  color: var(--focus-ring);
  font-family: var(--serif);
  font-size: 46px;
}

.scrim {
  position: fixed;
  inset: 0;
  z-index: 15;
  background: var(--scrim);
  border: none;
}

@media (max-width: 53.75em) {
  .app-shell {
    grid-template-columns: minmax(0, 1fr);
  }
  .measure {
    padding: 40px 24px 100px;
  }

  .doc-title {
    font-size: 34px;
  }
}
</style>
