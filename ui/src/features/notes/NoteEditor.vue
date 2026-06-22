<script setup lang="ts">
interface NoteEditorProps {
  modelValue: string;
  canSave: boolean;
  saving?: boolean;
  error?: string | null;
}

withDefaults(defineProps<NoteEditorProps>(), {
  saving: false,
  error: null,
});

const emit = defineEmits<{
  "update:modelValue": [value: string];
  save: [];
  cancel: [];
}>();

function updateValue(event: Event) {
  emit("update:modelValue", (event.target as HTMLTextAreaElement).value);
}
</script>

<template>
  <form class="note-editor" @submit.prevent="emit('save')">
    <textarea
      class="note-editor__textarea"
      :value="modelValue"
      aria-label="Markdown content"
      spellcheck="true"
      @input="updateValue"
    />

    <div class="note-editor__bar">
      <p v-if="error" class="note-editor__error" role="alert">{{ error }}</p>
      <div class="note-editor__actions">
        <button
          class="note-editor__button note-editor__button--secondary"
          type="button"
          :disabled="saving"
          @click="emit('cancel')"
        >
          Cancel
        </button>
        <button
          class="note-editor__button note-editor__button--primary"
          type="submit"
          :disabled="saving || !canSave"
        >
          {{ saving ? "Saving..." : "Save" }}
        </button>
      </div>
    </div>
  </form>
</template>

<style scoped>
.note-editor {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.note-editor__textarea {
  min-height: 54vh;
  padding: 18px 20px;
  color: var(--text);
  font: 15px/1.65 var(--mono);
  resize: vertical;
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: var(--r);
  box-shadow: var(--shadow-sm);
}

.note-editor__textarea:focus {
  outline: none;
  box-shadow:
    0 0 0 3px var(--focus-ring),
    var(--shadow-sm);
}

.note-editor__bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.note-editor__error {
  margin: 0;
  color: var(--danger);
  font-size: 13px;
}

.note-editor__actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.note-editor__button {
  min-height: var(--tool-size);
  padding: 0 14px;
  color: var(--text);
  font: inherit;
  font-size: 13px;
  font-weight: 650;
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: var(--segment-item-radius);
}

.note-editor__button:not(:disabled) {
  cursor: pointer;
}

.note-editor__button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.note-editor__button--primary {
  color: var(--surface);
  background: var(--accent);
  border-color: var(--accent);
}

.note-editor__button--secondary:hover:not(:disabled) {
  background: var(--menu-hover-surface);
}
</style>
