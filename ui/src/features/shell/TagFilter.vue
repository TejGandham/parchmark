<script setup lang="ts">
import type { TagCount } from "@/features/notes/noteMockHelpers";

interface TagFilterProps {
  tags: TagCount[];
  activeTags: string[];
}

defineProps<TagFilterProps>();

const emit = defineEmits<{
  toggle: [tag: string];
}>();
</script>

<template>
  <section class="tag-filter" aria-label="Filter by tag">
    <span class="tag-filter__label">Filter by tag</span>
    <button
      v-for="{ tag, count } in tags"
      :key="tag"
      class="tag-filter__tag"
      :class="{ 'is-active': activeTags.includes(tag) }"
      type="button"
      :aria-pressed="activeTags.includes(tag)"
      :title="`${count} notes`"
      @click="emit('toggle', tag)"
    >
      <span aria-hidden="true">#</span>{{ tag }}
    </button>
  </section>
</template>

<style scoped>
.tag-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  align-items: center;
  padding: 12px 20px 6px;
}

.tag-filter__label {
  width: 100%;
  margin-bottom: 2px;
  color: var(--muted);
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}

.tag-filter__tag {
  padding: 3.5px 10px;
  color: var(--text-2);
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: 20px;
  transition:
    border-color 0.14s ease,
    color 0.14s ease,
    background-color 0.14s ease;
}

.tag-filter__tag span {
  opacity: 0.55;
}

.tag-filter__tag:hover {
  color: var(--accent);
  border-color: var(--tool-hover-border);
}

.tag-filter__tag.is-active {
  color: var(--surface);
  background: var(--accent);
  border-color: var(--accent);
}

.tag-filter__tag.is-active span {
  opacity: 0.8;
}

.tag-filter__tag:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px var(--focus-ring);
}
</style>
