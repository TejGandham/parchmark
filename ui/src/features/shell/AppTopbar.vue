<script setup lang="ts">
import DsToolButton from "@/design-system/components/DsToolButton.vue";
import { MenuIcon } from "@/design-system/icons";
import type { NoteMock } from "@/features/notes/mockNotes";

import BreadcrumbTrail from "./BreadcrumbTrail.vue";
import EditingFlag from "./EditingFlag.vue";
import type { NoteMenuAction, NoteMode } from "./headerTypes";
import OverflowNoteMenu from "./OverflowNoteMenu.vue";
import ReadEditSegment from "./ReadEditSegment.vue";
import ThemeToggleButton from "./ThemeToggleButton.vue";

interface AppTopbarProps {
  activeNote: NoteMock | null;
  activeTags: string[];
  title: string;
  mode: NoteMode;
  dirty?: boolean;
  theme: "light" | "dark";
  menuOpen: boolean;
}

defineProps<AppTopbarProps>();
const emit = defineEmits<{
  openDrawer: [];
  startEdit: [];
  toggleTheme: [];
  "update:mode": [mode: NoteMode];
  "update:menuOpen": [open: boolean];
  noteAction: [id: NoteMenuAction];
}>();

function updateMode(mode: NoteMode) {
  emit("update:mode", mode);
}

function startEdit() {
  emit("startEdit");
}
</script>

<template>
  <header class="app-topbar" aria-label="Note toolbar">
    <DsToolButton
      class="app-topbar__menu-toggle"
      label="Menu"
      @click="emit('openDrawer')"
    >
      <MenuIcon :aria-hidden="true" />
    </DsToolButton>

    <BreadcrumbTrail
      :title="activeNote ? title : ''"
      :activeTags="activeTags"
    />

    <div class="app-topbar__spacer" />

    <ReadEditSegment
      v-if="activeNote && mode === 'read'"
      :mode="mode"
      @update:mode="updateMode"
      @startEdit="startEdit"
    />

    <EditingFlag v-if="activeNote && mode === 'edit'" />

    <ThemeToggleButton :theme="theme" @toggle="emit('toggleTheme')" />

    <OverflowNoteMenu
      v-if="activeNote && mode === 'read'"
      :open="menuOpen"
      :note="activeNote"
      @update:open="emit('update:menuOpen', $event)"
      @select="emit('noteAction', $event)"
    />
  </header>
</template>

<style scoped>
.app-topbar {
  display: flex;
  gap: var(--topbar-gap);
  align-items: center;
  padding: var(--topbar-padding-y) var(--topbar-padding-x);
  background: var(--topbar-bg);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(8px);
}

.app-topbar__menu-toggle {
  display: none;
}

.app-topbar__spacer {
  flex: 1;
}

@media (max-width: 53.75em) {
  .app-topbar__menu-toggle {
    display: grid;
  }
}
</style>
