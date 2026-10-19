<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import MarkdownProse from "@/features/notes/MarkdownProse.vue";
import {
  createViewLink,
  deleteArtifact,
  getArtifactContent,
  setArtifactVisibility,
  type ArtifactDTO,
  type ArtifactVisibility,
} from "@/services/artifacts";

import { errorDetail } from "./errorDetail";

const props = defineProps<{
  artifact: ArtifactDTO;
}>();

const emit = defineEmits<{
  back: [];
  updated: [artifact: ArtifactDTO];
  deleted: [id: number];
}>();

const visibilityOptions: ArtifactVisibility[] = ["private", "unlisted"];

// Local copy: visibility changes replace it with the server's response
// instead of mutating the prop.
const current = ref<ArtifactDTO>(props.artifact);
const viewUrl = ref<string | null>(null);
const markdown = ref<string | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const busy = ref(false);
const confirmingDelete = ref(false);
const copied = ref(false);

// HTML and SVG run untrusted markup, so they are only ever shown inside a
// sandboxed frame on the content origin; Markdown is sanitized in-page.
const framed = computed(
  () => current.value.current_version.content_type !== "markdown",
);
const canCopy = computed(() => current.value.visibility === "unlisted");

// The viewer mounts afresh for every open, so each open mints a new link.
onMounted(async () => {
  try {
    if (framed.value) {
      const link = await createViewLink(current.value.id);
      viewUrl.value = link.url;
    } else {
      const body = await getArtifactContent(current.value.id);
      markdown.value = body.content;
    }
  } catch (caught) {
    error.value = errorDetail(caught);
  } finally {
    loading.value = false;
  }
});

async function chooseVisibility(visibility: ArtifactVisibility) {
  if (busy.value || visibility === current.value.visibility) return;

  busy.value = true;
  error.value = null;
  copied.value = false;
  try {
    current.value = await setArtifactVisibility(current.value.id, visibility);
    emit("updated", current.value);
  } catch (caught) {
    error.value = errorDetail(caught);
  } finally {
    busy.value = false;
  }
}

async function copyLink() {
  if (!canCopy.value) return;

  try {
    await navigator.clipboard.writeText(current.value.share_url);
    copied.value = true;
  } catch {
    error.value = "Could not copy the link.";
  }
}

async function confirmDelete() {
  busy.value = true;
  error.value = null;
  try {
    await deleteArtifact(current.value.id);
    emit("deleted", current.value.id);
  } catch (caught) {
    error.value = errorDetail(caught);
    confirmingDelete.value = false;
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <article class="artifact-viewer">
    <header class="artifact-viewer__bar">
      <button class="artifact-back" type="button" @click="emit('back')">
        ← All artifacts
      </button>
      <h1 class="artifact-viewer__title">{{ current.title }}</h1>
      <span class="artifact-viewer__meta">
        {{ current.current_version.content_type }} · v{{
          current.current_version.version
        }}
      </span>
    </header>

    <div class="artifact-viewer__controls">
      <div class="artifact-visibility" role="group" aria-label="Visibility">
        <button
          v-for="option in visibilityOptions"
          :key="option"
          type="button"
          :data-visibility="option"
          :aria-pressed="current.visibility === option ? 'true' : 'false'"
          :class="{ 'is-active': current.visibility === option }"
          :disabled="busy"
          @click="chooseVisibility(option)"
        >
          {{ option }}
        </button>
      </div>

      <button
        class="artifact-copy"
        type="button"
        :disabled="!canCopy"
        :title="
          canCopy ? 'Copy share link' : 'Make the artifact unlisted to share it'
        "
        @click="copyLink"
      >
        {{ copied ? "Link copied" : "Copy link" }}
      </button>

      <template v-if="confirmingDelete">
        <span class="artifact-viewer__confirm-text">Delete for good?</span>
        <button
          class="artifact-delete-confirm"
          type="button"
          :disabled="busy"
          @click="confirmDelete"
        >
          Delete
        </button>
        <button
          class="artifact-delete-cancel"
          type="button"
          @click="confirmingDelete = false"
        >
          Cancel
        </button>
      </template>
      <button
        v-else
        class="artifact-delete"
        type="button"
        @click="confirmingDelete = true"
      >
        Delete…
      </button>
    </div>

    <p v-if="error" class="artifact-viewer__error" role="alert">{{ error }}</p>

    <div v-if="loading" class="artifact-viewer__state" role="status">
      Loading…
    </div>
    <iframe
      v-else-if="framed && viewUrl"
      class="artifact-frame"
      :src="viewUrl"
      :title="current.title"
      sandbox="allow-scripts"
      referrerpolicy="no-referrer"
    />
    <div v-else-if="!framed && markdown !== null" class="artifact-markdown">
      <MarkdownProse :markdown="markdown" keep-title />
    </div>
  </article>
</template>

<style scoped>
.artifact-viewer {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 14px;
  min-height: 0;
  padding: 28px 32px;
}

.artifact-viewer__bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: baseline;
}

.artifact-viewer__title {
  margin: 0;
  color: var(--text);
  font-family: var(--serif);
  font-size: 28px;
}

.artifact-viewer__meta {
  color: var(--muted);
  font-size: 12.5px;
}

.artifact-viewer__controls {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.artifact-viewer button {
  padding: 6px 12px;
  color: var(--text);
  font-size: 13px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: var(--r);
}

.artifact-viewer button:disabled {
  color: var(--muted);
  cursor: not-allowed;
  opacity: 0.6;
}

.artifact-viewer button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px var(--focus-ring);
}

.artifact-visibility {
  display: inline-flex;
  gap: 4px;
}

.artifact-visibility button.is-active {
  color: var(--accent);
  border-color: var(--accent);
}

.artifact-viewer .artifact-delete-confirm {
  color: var(--danger);
  border-color: var(--danger);
}

.artifact-viewer__confirm-text {
  color: var(--muted);
  font-size: 13px;
}

.artifact-viewer__error {
  margin: 0;
  padding: 10px 12px;
  color: var(--danger);
  font-size: 13px;
  background: var(--danger-surface);
  border-radius: var(--r);
}

.artifact-viewer__state {
  color: var(--muted);
  font-size: 14px;
}

.artifact-frame {
  flex: 1;
  width: 100%;
  min-height: 420px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r);
}

.artifact-markdown {
  flex: 1;
  max-width: 780px;
  min-height: 0;
  overflow-y: auto;
}
</style>
