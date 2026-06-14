<script setup lang="ts">
import NoteCard from "@/features/notes/NoteCard.vue";
import type { NoteMock } from "@/features/notes/mockNotes";
import { groupByTime, type TagCount } from "@/features/notes/noteMockHelpers";
import { PlusIcon } from "@/design-system/icons";

import SearchBox from "./SearchBox.vue";
import TagFilter from "./TagFilter.vue";
import UserFooter from "./UserFooter.vue";

interface SidebarDrawerProps {
  notes: NoteMock[];
  activeId: string | null;
  search: string;
  tags: TagCount[];
  activeTags: string[];
  settingsActive?: boolean;
  open?: boolean;
}

const props = withDefaults(defineProps<SidebarDrawerProps>(), {
  settingsActive: false,
  open: false,
});

const emit = defineEmits<{
  select: [id: string];
  newNote: [];
  "update:search": [value: string];
  clearSearch: [];
  toggleTag: [tag: string];
  openSettings: [];
}>();
</script>

<template>
  <aside class="sidebar-drawer" :class="{ 'is-open': open }" aria-label="Notes">
    <div class="sidebar-drawer__head">
      <div class="brand-row">
        <div class="wordmark">Parch<span>Mark</span></div>
        <button
          class="new-note-button"
          type="button"
          title="New note"
          @click="emit('newNote')"
        >
          <span class="new-note-button__icon" aria-hidden="true">
            <PlusIcon :aria-hidden="true" />
          </span>
          New
        </button>
      </div>
    </div>

    <SearchBox
      :modelValue="search"
      @update:modelValue="emit('update:search', $event)"
    />

    <TagFilter
      :tags="tags"
      :activeTags="activeTags"
      @toggle="emit('toggleTag', $event)"
    />

    <div class="note-list" aria-live="polite">
      <div v-if="notes.length === 0" class="note-list__empty">
        No notes match.
      </div>
      <template v-for="group in groupByTime(notes)" :key="group.key">
        <div class="group-label">
          {{ group.label }}
          <span>{{ group.notes.length }}</span>
        </div>
        <NoteCard
          v-for="note in group.notes"
          :key="note.id"
          :note="note"
          :active="note.id === activeId"
          @click="emit('select', note.id)"
        />
      </template>
    </div>

    <UserFooter :active="settingsActive" @openSettings="emit('openSettings')" />
  </aside>
</template>

<style scoped>
.sidebar-drawer {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--surface-2);
  border-right: 1px solid var(--line-2);
}

.sidebar-drawer__head {
  padding: 20px 20px 14px;
}

.brand-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.wordmark {
  color: var(--text);
  font-family: var(--serif);
  font-size: 25px;
  font-weight: 800;
  line-height: 1;
}

.wordmark span {
  color: var(--accent);
}

.new-note-button {
  display: inline-flex;
  gap: 7px;
  align-items: center;
  padding: 9px 14px;
  color: var(--surface);
  font-size: 13.5px;
  font-weight: 600;
  background: var(--accent);
  border: none;
  border-radius: 10px;
  box-shadow: var(--shadow-sm);
  transition:
    background-color 0.15s ease,
    box-shadow 0.15s ease,
    transform 0.1s ease;
}

.new-note-button:hover {
  background: var(--accent);
  box-shadow: var(--shadow);
  transform: translateY(-1px);
}

.new-note-button:active {
  transform: translateY(0);
}

.new-note-button:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 3px var(--focus-ring),
    var(--shadow-sm);
}

.new-note-button__icon {
  display: grid;
  margin-top: -1px;
  place-items: center;
}

.note-list {
  flex: 1;
  min-height: 0;
  padding: 10px 12px 24px;
  overflow-y: auto;
}

.note-list__empty {
  padding: 28px 12px;
  color: var(--muted);
  font-size: 13.5px;
  text-align: center;
}

.group-label {
  display: flex;
  gap: 7px;
  align-items: baseline;
  padding: 14px 10px 7px;
  color: var(--muted);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}

.group-label span {
  color: var(--muted);
  font-weight: 600;
}

@media (max-width: 53.75em) {
  .sidebar-drawer {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 20;
    width: var(--drawer-width);
    box-shadow: var(--shadow-lg);
    transform: translateX(-100%);
    transition: transform 0.22s ease;
  }

  .sidebar-drawer.is-open {
    transform: none;
  }
}
</style>
