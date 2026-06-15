<script setup lang="ts">
import { EditIcon, EyeIcon } from "@/design-system/icons";

import type { NoteMode } from "./headerTypes";

interface ReadEditSegmentProps {
  mode: NoteMode;
}

const props = defineProps<ReadEditSegmentProps>();

const emit = defineEmits<{
  "update:mode": [mode: NoteMode];
  startEdit: [];
}>();

function toggleMode() {
  const nextMode = props.mode === "read" ? "edit" : "read";
  emit("update:mode", nextMode);
  if (nextMode === "edit") {
    emit("startEdit");
  }
}
</script>

<template>
  <div
    class="mode-switch"
    :class="{ 'is-editing': mode === 'edit' }"
    aria-label="Note mode"
  >
    <span class="mode-switch__status" role="status">
      <span class="mode-switch__dot" aria-hidden="true" />
      {{ mode === "edit" ? "Editing" : "Reading" }}
    </span>

    <button
      class="mode-switch__action"
      type="button"
      :aria-label="
        mode === 'edit' ? 'Return to read mode' : 'Switch to edit mode'
      "
      @click="toggleMode"
    >
      <EyeIcon v-if="mode === 'edit'" :aria-hidden="true" />
      <EditIcon v-else :aria-hidden="true" />
      <span>{{ mode === "edit" ? "Read" : "Edit" }}</span>
    </button>
  </div>
</template>

<style scoped>
.mode-switch {
  display: inline-flex;
  min-height: var(--tool-size);
  align-items: center;
  gap: 4px;
  padding: 3px 3px 3px 10px;
  color: var(--text-2);
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: var(--segment-radius);
}

.mode-switch__status {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  min-width: 72px;
  font-size: 13px;
  font-weight: 600;
}

.mode-switch__dot {
  width: var(--segment-item-radius);
  height: var(--segment-item-radius);
  background: var(--line-2);
  border-radius: 50%;
}

.mode-switch.is-editing .mode-switch__status {
  color: var(--accent);
}

.mode-switch.is-editing .mode-switch__dot {
  background: var(--accent);
}

.mode-switch__action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 13px;
  color: var(--accent);
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  background: var(--surface);
  border: none;
  border-radius: var(--segment-item-radius);
  box-shadow: var(--shadow-sm);
  transition:
    box-shadow 0.15s ease,
    color 0.15s ease,
    transform 0.15s ease;
}

.mode-switch__action:hover {
  color: var(--accent);
  box-shadow: var(--shadow-sm);
}

.mode-switch__action:active {
  transform: translateY(1px);
}

.mode-switch__action:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 3px var(--focus-ring),
    var(--shadow-sm);
}
</style>
