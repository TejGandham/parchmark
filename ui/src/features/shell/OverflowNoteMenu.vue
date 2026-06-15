<script setup lang="ts">
import { markRaw, nextTick, onBeforeUnmount, ref, watch } from "vue";

import DsMenu from "@/design-system/components/DsMenu.vue";
import DsToolButton from "@/design-system/components/DsToolButton.vue";
import {
  CopyIcon,
  DownloadIcon,
  MoreIcon,
  TrashIcon,
} from "@/design-system/icons";
import type { NoteMock } from "@/features/notes/mockNotes";

import type { NoteMenuAction } from "./headerTypes";

interface OverflowNoteMenuProps {
  open: boolean;
  note: NoteMock;
}

const props = defineProps<OverflowNoteMenuProps>();
const emit = defineEmits<{
  "update:open": [open: boolean];
  select: [id: NoteMenuAction];
}>();

const menuRoot = ref<HTMLElement | null>(null);

const menuItems = [
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

function closeMenu() {
  emit("update:open", false);
}

function handlePointerDown(event: PointerEvent) {
  const target = event.target;
  if (target instanceof Node && !menuRoot.value?.contains(target)) {
    closeMenu();
  }
}

function addOutsideListener() {
  document.addEventListener("pointerdown", handlePointerDown);
}

function removeOutsideListener() {
  document.removeEventListener("pointerdown", handlePointerDown);
}

watch(
  () => props.open,
  async (open) => {
    removeOutsideListener();
    if (open) {
      await nextTick();
      addOutsideListener();
    }
  },
  { immediate: true },
);

onBeforeUnmount(removeOutsideListener);

function selectItem(id: string) {
  emit("select", id as NoteMenuAction);
}
</script>

<template>
  <div ref="menuRoot" class="overflow-note-menu">
    <DsToolButton
      id="overflow-trigger"
      label="More"
      :active="open"
      @click.stop="$emit('update:open', !open)"
    >
      <MoreIcon :aria-hidden="true" />
    </DsToolButton>
    <DsMenu
      :open="open"
      :items="menuItems"
      labelledBy="overflow-trigger"
      @close="closeMenu"
      @select="selectItem"
    />
  </div>
</template>

<style scoped>
.overflow-note-menu {
  position: relative;
}

.overflow-note-menu :deep(.ds-menu) {
  top: calc(var(--tool-size) + 8px);
  right: 0;
}
</style>
