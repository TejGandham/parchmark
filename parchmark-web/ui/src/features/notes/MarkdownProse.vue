<script setup lang="ts">
import { computed } from "vue";

import { renderMarkdownBody } from "./markdownRender";

const props = defineProps<{
  markdown: string;
}>();

const renderedMarkdown = computed(() => renderMarkdownBody(props.markdown));
</script>

<template>
  <div class="prose" v-html="renderedMarkdown" />
</template>

<style scoped>
.prose {
  --prose-accent-soft: var(--tool-hover-border);

  color: var(--text);
  font-size: 1.0625rem;
  line-height: 1.72;
}

.prose :deep(:first-child) {
  margin-top: 0;
}

.prose :deep(h1),
.prose :deep(h2),
.prose :deep(h3),
.prose :deep(h4) {
  margin: 1.7em 0 0.55em;
  color: var(--text);
  font-family: var(--serif);
  font-weight: 700;
  line-height: 1.2;
}

.prose :deep(h1) {
  font-size: 1.9em;
}

.prose :deep(h2) {
  padding-bottom: 0.25em;
  font-size: 1.5em;
  border-bottom: 1px solid var(--line-2);
}

.prose :deep(h3) {
  font-size: 1.22em;
}

.prose :deep(h4) {
  font-size: 1.05em;
}

.prose :deep(p) {
  margin: 0 0 1.1em;
}

.prose :deep(a) {
  color: var(--accent);
  text-decoration: none;
  border-bottom: 1px solid var(--focus-ring);
  transition: border-color 0.14s ease;
}

.prose :deep(a:hover) {
  border-bottom-color: var(--accent);
}

.prose :deep(strong) {
  color: var(--text);
  font-weight: 700;
}

.prose :deep(em) {
  font-style: italic;
}

.prose :deep(ul),
.prose :deep(ol) {
  padding-left: 1.5em;
  margin: 0 0 1.1em;
}

.prose :deep(li) {
  margin: 0.3em 0;
}

.prose :deep(li::marker) {
  color: var(--prose-accent-soft);
}

.prose :deep(blockquote) {
  padding: 0.25em 0 0.25em 1.2em;
  margin: 1.3em 0;
  color: var(--text-2);
  font-style: italic;
  border-left: 0.18em solid var(--prose-accent-soft);
}

.prose :deep(blockquote p) {
  margin: 0.3em 0;
}

.prose :deep(code) {
  padding: 0.15em 0.45em;
  color: var(--accent);
  font-family: var(--mono);
  font-size: 0.85em;
  background: var(--surface-2);
  border-radius: calc(var(--r) / 2);
}

.prose :deep(pre) {
  padding: 1.1em 1.2em;
  margin: 1.3em 0;
  overflow-x: auto;
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: var(--r);
  box-shadow: var(--shadow-sm);
}

.prose :deep(pre code) {
  padding: 0;
  color: var(--text);
  font-size: 0.86em;
  line-height: 1.6;
  background: none;
  border-radius: 0;
}

.prose :deep(hr) {
  height: 1px;
  margin: 2em 0;
  background: var(--line-2);
  border: 0;
}

.prose :deep(img) {
  max-width: 100%;
  border-radius: var(--r);
}

.prose :deep(table) {
  width: 100%;
  margin: 1.3em 0;
  overflow: hidden;
  font-size: 0.92em;
  border-collapse: collapse;
}

.prose :deep(th),
.prose :deep(td) {
  padding: 0.58em 0.82em;
  text-align: left;
  border: 1px solid var(--line-2);
}

.prose :deep(th) {
  font-weight: 600;
  background: var(--surface-2);
}

.prose :deep(tr:nth-child(2n) td) {
  background: var(--surface-2);
}

.prose :deep(input[type="checkbox"]) {
  width: 1em;
  height: 1em;
  margin: 0 0.5em 0 0;
  accent-color: var(--accent);
  vertical-align: -0.12em;
}

.prose :deep(li:has(> input[type="checkbox"])) {
  margin-left: -1.4em;
  list-style: none;
}

.prose :deep(.mermaid) {
  padding: 1.1em;
  margin: 1.3em 0;
  overflow-x: auto;
  text-align: center;
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: var(--r);
}
</style>
