<script setup lang="ts">
import { computed, markRaw, ref, watch } from "vue";

import DsMenu from "@/design-system/components/DsMenu.vue";
import DsSegment from "@/design-system/components/DsSegment.vue";
import DsToolButton from "@/design-system/components/DsToolButton.vue";
import {
  CopyIcon,
  DownloadIcon,
  EditIcon,
  EyeIcon,
  MenuIcon,
  MoonIcon,
  MoreIcon,
  SunIcon,
  TrashIcon,
} from "@/design-system/icons";
import { mockNotes, type NoteMock } from "@/features/notes/mockNotes";
import {
  allTags,
  extractTitle,
  plainPreview,
  readingTime,
  relTime,
  wordCount,
} from "@/features/notes/noteMockHelpers";

import SidebarDrawer from "./SidebarDrawer.vue";

const notes = ref<NoteMock[]>(mockNotes.slice());
const activeId = ref(
  notes.value.slice().sort((left, right) => right.updatedAt - left.updatedAt)[0]
    ?.id ?? null,
);
const mode = ref("read");
const search = ref("");
const activeTags = ref<string[]>([]);
const menuOpen = ref(false);
const navOpen = ref(false);
const settingsActive = ref(false);
const theme = ref(
  typeof localStorage === "undefined"
    ? "light"
    : localStorage.getItem("pm_theme") || "light",
);

const segmentOptions = [
  { value: "read", label: "Read", icon: markRaw(EyeIcon) },
  { value: "edit", label: "Edit", icon: markRaw(EditIcon) },
];

const menuItems = [
  { id: "edit", label: "Edit note", icon: markRaw(EditIcon) },
  { id: "copy", label: "Copy markdown", icon: markRaw(CopyIcon) },
  { id: "export", label: "Export .md", icon: markRaw(DownloadIcon) },
  {
    id: "delete",
    label: "Delete note",
    icon: markRaw(TrashIcon),
    danger: true,
    separatorBefore: true,
  },
];

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

const bodyPreview = computed(() =>
  activeNote.value ? plainPreview(activeNote.value.content) : "",
);

function selectNote(id: string) {
  activeId.value = id;
  mode.value = "read";
  menuOpen.value = false;
  navOpen.value = false;
  settingsActive.value = false;
}

function createNote() {
  const timestamp = Date.now();
  const note: NoteMock = {
    id: `n${timestamp.toString(36)}`,
    tags: [],
    createdAt: timestamp,
    updatedAt: timestamp,
    content: "# Untitled\n\n",
  };

  notes.value = [note, ...notes.value];
  activeId.value = note.id;
  mode.value = "edit";
  navOpen.value = false;
  settingsActive.value = false;
}

function toggleTag(tag: string) {
  activeTags.value = activeTags.value.includes(tag)
    ? activeTags.value.filter((activeTag) => activeTag !== tag)
    : [...activeTags.value, tag];
}

function openSettings() {
  settingsActive.value = true;
  navOpen.value = false;
  menuOpen.value = false;
}

function toggleTheme() {
  theme.value = theme.value === "dark" ? "light" : "dark";
}

function handleMenuSelect(id: string) {
  if (id === "edit") {
    mode.value = "edit";
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
      @select="selectNote"
      @newNote="createNote"
      @toggleTag="toggleTag"
      @openSettings="openSettings"
    />

    <button
      v-if="navOpen"
      class="scrim"
      type="button"
      aria-label="Close navigation"
      @click="navOpen = false"
    />

    <main class="main-pane">
      <header class="topbar" aria-label="Note toolbar">
        <DsToolButton class="menu-toggle" label="Menu" @click="navOpen = true">
          <MenuIcon :aria-hidden="true" />
        </DsToolButton>

        <div class="crumb">
          <template v-if="activeTags.length">
            <span>Filtered</span>
            <strong v-for="tag in activeTags" :key="tag">#{{ tag }}</strong>
          </template>
          <span v-else>All notes</span>
          <template v-if="activeNote">
            <span class="crumb__slash" aria-hidden="true">/</span>
            <strong>{{ activeTitle }}</strong>
          </template>
        </div>

        <div class="spacer" />

        <DsSegment
          v-if="activeNote && !settingsActive"
          v-model="mode"
          ariaLabel="Note view mode"
          :options="segmentOptions"
        />

        <DsToolButton
          :label="
            theme === 'dark' ? 'Switch to Parchment' : 'Switch to Desk lamp'
          "
          @click="toggleTheme"
        >
          <SunIcon v-if="theme === 'dark'" :aria-hidden="true" />
          <MoonIcon v-else :aria-hidden="true" />
        </DsToolButton>

        <div v-if="activeNote && !settingsActive" class="menu-anchor">
          <DsToolButton
            id="overflow-trigger"
            label="More"
            :active="menuOpen"
            @click.stop="menuOpen = !menuOpen"
          >
            <MoreIcon :aria-hidden="true" />
          </DsToolButton>
          <DsMenu
            :open="menuOpen"
            :items="menuItems"
            labelledBy="overflow-trigger"
            @close="menuOpen = false"
            @select="handleMenuSelect"
          />
        </div>
      </header>

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
            <span v-if="activeNote.tags.length" class="doc-tags">
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
          <p class="note-body">{{ bodyPreview }}</p>
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

.topbar {
  display: flex;
  gap: var(--topbar-gap);
  align-items: center;
  padding: var(--topbar-padding-y) var(--topbar-padding-x);
  background: var(--topbar-bg);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(8px);
}

.menu-toggle {
  display: none;
}

.crumb {
  display: flex;
  gap: 7px;
  align-items: center;
  min-width: 0;
  color: var(--muted);
  font-size: 13px;
}

.crumb strong {
  color: var(--text-2);
  font-weight: 600;
}

.crumb__slash {
  color: var(--muted);
}

.spacer {
  flex: 1;
}

.menu-anchor {
  position: relative;
}

.menu-anchor :deep(.ds-menu) {
  top: calc(var(--tool-size) + 8px);
  right: 0;
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

.note-body {
  margin: 0;
  color: var(--text);
  font-size: 17px;
  line-height: 1.72;
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

  .menu-toggle {
    display: grid;
  }

  .measure {
    padding: 40px 24px 100px;
  }

  .doc-title {
    font-size: 34px;
  }
}
</style>
