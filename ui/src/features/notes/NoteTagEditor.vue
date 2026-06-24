<script setup lang="ts">
import { computed, ref } from "vue";

import { PlusIcon, XIcon } from "@/design-system/icons";

interface NoteTagEditorProps {
  tags: string[];
  disabled?: boolean;
  error?: string | null;
  /** Compatibility for the existing AppShell consumer until it moves to disabled. */
  saving?: boolean;
}

const props = withDefaults(defineProps<NoteTagEditorProps>(), {
  disabled: false,
  error: null,
  saving: false,
});

const emit = defineEmits<{
  "add-tag": [value: string];
  "remove-tag": [tag: string];
  addTag: [value: string];
  removeTag: [tag: string];
}>();

const tagDraft = ref("");
const canAddTag = computed(() => tagDraft.value.trim().length > 0);
const isDisabled = computed(() => props.disabled || props.saving);

function addTag() {
  if (!canAddTag.value) return;

  emit("add-tag", tagDraft.value);
  emit("addTag", tagDraft.value);
  tagDraft.value = "";
}

function removeTag(tag: string) {
  emit("remove-tag", tag);
  emit("removeTag", tag);
}
</script>

<template>
  <section class="note-tag-editor" aria-labelledby="note-tag-editor-title">
    <div class="note-tag-editor__head">
      <h2 id="note-tag-editor-title">Tags</h2>
      <span>{{ tags.length }} {{ tags.length === 1 ? "tag" : "tags" }}</span>
    </div>

    <div v-if="tags.length" class="note-tag-editor__chips">
      <button
        v-for="tag in tags"
        :key="tag"
        class="note-tag-editor__chip"
        type="button"
        :disabled="isDisabled"
        :aria-label="`Remove #${tag}`"
        @click="removeTag(tag)"
      >
        <span>#{{ tag }}</span>
        <XIcon :ariaHidden="true" />
      </button>
    </div>
    <p v-else class="note-tag-editor__empty">No tags yet.</p>
    <p v-if="error" class="note-tag-editor__error" role="alert">
      {{ error }}
    </p>

    <form class="note-tag-editor__form" @submit.prevent="addTag">
      <label class="sr-only" for="note-tag-editor-input">Add tag</label>
      <input
        id="note-tag-editor-input"
        v-model="tagDraft"
        type="text"
        autocomplete="off"
        placeholder="Add tag"
        :disabled="isDisabled"
      />
      <button type="submit" :disabled="isDisabled || !canAddTag">
        <PlusIcon :ariaHidden="true" />
        <span>Add</span>
      </button>
    </form>
  </section>
</template>

<style scoped>
.note-tag-editor {
  display: grid;
  gap: 10px;
  margin-bottom: 18px;
  padding: 14px;
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: var(--r);
  box-shadow: var(--shadow-sm);
}

.note-tag-editor__head {
  display: flex;
  gap: 10px;
  align-items: baseline;
  justify-content: space-between;
}

.note-tag-editor__head h2 {
  margin: 0;
  color: var(--text);
  font-size: 13px;
  font-weight: 700;
}

.note-tag-editor__head span,
.note-tag-editor__error,
.note-tag-editor__empty {
  color: var(--muted);
  font-size: 12px;
}

.note-tag-editor__error,
.note-tag-editor__empty {
  margin: 0;
}

.note-tag-editor__error {
  color: var(--danger);
}

.note-tag-editor__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.note-tag-editor__chip {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  min-height: 26px;
  padding: 0 9px;
  color: var(--accent-600);
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  background: var(--focus-ring);
  border: 1px solid transparent;
  border-radius: 999px;
}

.note-tag-editor__chip:not(:disabled),
.note-tag-editor__form button:not(:disabled) {
  cursor: pointer;
}

.note-tag-editor__chip:hover:not(:disabled),
.note-tag-editor__chip:focus-visible {
  color: var(--accent);
  outline: none;
  border-color: color-mix(in srgb, var(--accent) 22%, transparent);
}

.note-tag-editor__chip:disabled,
.note-tag-editor__form input:disabled,
.note-tag-editor__form button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.note-tag-editor__form {
  display: flex;
  gap: 8px;
}

.note-tag-editor__form input {
  min-width: 0;
  flex: 1;
  padding: 0 11px;
  color: var(--text);
  font: inherit;
  font-size: 13px;
  background: var(--canvas);
  border: 1px solid var(--line-2);
  border-radius: var(--segment-item-radius);
}

.note-tag-editor__form input:focus {
  outline: none;
  box-shadow: 0 0 0 3px var(--focus-ring);
}

.note-tag-editor__form input::placeholder {
  color: var(--muted);
}

.note-tag-editor__form button {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  justify-content: center;
  min-height: var(--tool-size);
  padding: 0 14px;
  color: var(--surface);
  font: inherit;
  font-size: 13px;
  font-weight: 650;
  background: var(--accent);
  border: 1px solid var(--accent);
  border-radius: var(--segment-item-radius);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
