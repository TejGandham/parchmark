<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { listArtifacts, type ArtifactDTO } from "@/services/artifacts";

import ArtifactViewer from "./ArtifactViewer.vue";
import { errorDetail } from "./errorDetail";
import { useArtifactRoute } from "./useArtifactRoute";

const emit = defineEmits<{
  selectedTitle: [title: string | null];
}>();

// The open artifact lives in the address bar (/artifacts/<id>), so a reload,
// Back and Forward all land on the same artifact.
const { location, go } = useArtifactRoute();

const artifacts = ref<ArtifactDTO[]>([]);
const loading = ref(false);
const loaded = ref(false);
const error = ref<string | null>(null);

const selectedId = computed(() => location.value?.artifactId ?? null);

const selected = computed(
  () => artifacts.value.find((item) => item.id === selectedId.value) ?? null,
);

function openArtifact(id: number) {
  go({ artifactId: id });
}

function showList({ replace = false } = {}) {
  go({ artifactId: null }, { replace });
}

async function fetchArtifacts() {
  loading.value = true;
  error.value = null;
  try {
    artifacts.value = await listArtifacts();
    loaded.value = true;
  } catch (caught) {
    error.value = errorDetail(caught);
  } finally {
    loading.value = false;
  }
}

function replaceArtifact(updated: ArtifactDTO) {
  artifacts.value = artifacts.value.map((item) =>
    item.id === updated.id ? updated : item,
  );
}

function removeArtifact(id: number) {
  artifacts.value = artifacts.value.filter((item) => item.id !== id);
  showList({ replace: true });
}

// An id the owner's list does not contain (unknown, deleted or another
// user's) falls back to the list, replacing the dead address.
watch([selectedId, loaded], ([id, isLoaded]) => {
  if (isLoaded && id !== null && selected.value === null) {
    showList({ replace: true });
  }
});

watch(
  () => selected.value?.title ?? null,
  (title) => emit("selectedTitle", title),
  { immediate: true },
);

onMounted(fetchArtifacts);
</script>

<template>
  <section class="artifacts-view" aria-label="Artifacts">
    <ArtifactViewer
      v-if="selected"
      :key="selected.id"
      :artifact="selected"
      @back="showList()"
      @updated="replaceArtifact"
      @deleted="removeArtifact"
    />

    <div v-else class="artifacts-view__inner">
      <header class="artifacts-view__header">
        <h1>Artifacts</h1>
        <p>HTML, SVG and Markdown documents you have published.</p>
      </header>

      <div v-if="loading" class="artifacts-view__state" role="status">
        Loading artifacts…
      </div>
      <div
        v-else-if="error"
        class="artifacts-view__state is-error"
        role="alert"
      >
        <p>{{ error }}</p>
        <button class="artifacts-retry" type="button" @click="fetchArtifacts">
          Retry
        </button>
      </div>
      <p v-else-if="artifacts.length === 0" class="artifacts-view__state">
        No artifacts yet.
      </p>
      <ul v-else class="artifact-gallery">
        <li v-for="item in artifacts" :key="item.id">
          <button
            class="artifact-card"
            type="button"
            @click="openArtifact(item.id)"
          >
            <span class="artifact-card__title">{{ item.title }}</span>
            <span class="artifact-card__meta">
              <span>{{ item.current_version.content_type }}</span>
              <span>{{ item.visibility }}</span>
              <span>v{{ item.current_version.version }}</span>
            </span>
          </button>
        </li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.artifacts-view {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
  overflow-y: auto;
}

.artifacts-view__inner {
  width: 100%;
  max-width: 780px;
  padding: 54px 56px 110px;
  margin: 0 auto;
}

.artifacts-view h1 {
  margin: 0 0 8px;
  color: var(--text);
  font-family: var(--serif);
  font-size: 34px;
}

.artifacts-view__header p,
.artifacts-view__state {
  margin: 0 0 24px;
  color: var(--muted);
  font-size: 14px;
}

.artifacts-view__state.is-error {
  color: var(--danger);
}

.artifact-gallery {
  display: grid;
  gap: 10px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.artifact-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  padding: 14px 16px;
  color: inherit;
  text-align: left;
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: var(--r);
}

.artifact-card:hover,
.artifact-card:focus-visible {
  border-color: var(--accent);
  outline: none;
}

.artifact-card__title {
  color: var(--text);
  font-size: 15px;
  font-weight: 600;
}

.artifact-card__meta {
  display: flex;
  gap: 10px;
  color: var(--muted);
  font-size: 12px;
}

@media (max-width: 53.75em) {
  .artifacts-view__inner {
    padding: 40px 24px 100px;
  }
}
</style>
