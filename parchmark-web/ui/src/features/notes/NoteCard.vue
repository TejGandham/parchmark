<script setup lang="ts">
import type { NoteMock } from "./mockNotes";
import { extractTitle, plainPreview, relTime } from "./noteMockHelpers";

interface NoteCardProps {
  note: NoteMock;
  active?: boolean;
}

defineProps<NoteCardProps>();
</script>

<template>
  <button class="note-card" :class="{ 'is-active': active }" type="button">
    <span class="note-card__title">{{ extractTitle(note.content) }}</span>
    <span v-if="plainPreview(note.content)" class="note-card__preview">
      {{ plainPreview(note.content) }}
    </span>
    <span class="note-card__meta">
      <span class="note-card__time">{{ relTime(note.updatedAt) }}</span>
      <span v-if="note.tags.length" class="note-card__tags">
        <span v-for="tag in note.tags.slice(0, 2)" :key="tag" class="mini-tag">
          #{{ tag }}
        </span>
      </span>
    </span>
  </button>
</template>

<style scoped>
.note-card {
  position: relative;
  display: block;
  width: 100%;
  padding: 11px 12px;
  color: inherit;
  text-align: left;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 10px;
  transition:
    background-color 0.13s ease,
    border-color 0.13s ease,
    box-shadow 0.13s ease;
}

.note-card + .note-card {
  margin-top: 2px;
}

.note-card:hover {
  background: var(--menu-hover-surface);
}

.note-card.is-active {
  background: var(--surface);
  border-color: var(--line-2);
  box-shadow: var(--shadow-sm);
}

.note-card.is-active::before {
  position: absolute;
  top: 12px;
  bottom: 12px;
  left: 0;
  width: 3px;
  content: "";
  background: var(--accent);
  border-radius: 3px;
}

.note-card:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 3px var(--focus-ring),
    var(--shadow-sm);
}

.note-card__title,
.note-card__preview,
.note-card__meta {
  display: block;
}

.note-card__title {
  display: -webkit-box;
  margin-bottom: 3px;
  overflow: hidden;
  color: var(--text);
  font-family: var(--serif);
  font-size: 15.5px;
  font-weight: 600;
  line-height: 1.25;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
}

.note-card__preview {
  display: -webkit-box;
  overflow: hidden;
  color: var(--text-2);
  font-size: 12.5px;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.note-card__meta {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 7px;
}

.note-card__time {
  color: var(--muted);
  font-size: 11px;
}

.note-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.mini-tag {
  padding: 1.5px 7px;
  color: var(--accent-600);
  font-size: 10.5px;
  font-weight: 500;
  background: var(--focus-ring);
  border-radius: 12px;
}
</style>
