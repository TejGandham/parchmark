<script setup lang="ts">
import { SearchIcon, XIcon } from "@/design-system/icons";

interface SearchBoxProps {
  modelValue: string;
  placeholder?: string;
}

withDefaults(defineProps<SearchBoxProps>(), {
  placeholder: "Search notes...",
});

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();
</script>

<template>
  <label class="search-box" :class="{ 'has-value': modelValue }">
    <SearchIcon class="search-box__icon" :aria-hidden="true" />
    <span class="visually-hidden">Search notes</span>
    <input
      :value="modelValue"
      :placeholder="placeholder"
      type="search"
      @input="
        emit('update:modelValue', ($event.target as HTMLInputElement).value)
      "
    />
    <button
      v-if="modelValue"
      class="search-box__clear"
      type="button"
      aria-label="Clear search"
      @click="emit('update:modelValue', '')"
    >
      <XIcon :aria-hidden="true" />
    </button>
  </label>
</template>

<style scoped>
.search-box {
  display: flex;
  gap: 9px;
  align-items: center;
  padding: 9px 12px;
  margin: 14px 20px 4px;
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: 10px;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.search-box:focus-within {
  border-color: var(--tool-hover-border);
  box-shadow: 0 0 0 3px var(--focus-ring);
}

.search-box__icon {
  flex: none;
  color: var(--muted);
}

.search-box input {
  width: 100%;
  min-width: 0;
  color: var(--text);
  font: inherit;
  font-size: 14px;
  background: transparent;
  border: none;
  outline: none;
}

.search-box input::placeholder {
  color: var(--muted);
}

.search-box__clear {
  display: grid;
  flex: none;
  padding: 0 2px;
  color: var(--muted);
  background: transparent;
  border: none;
  place-items: center;
}

.search-box__clear:hover,
.search-box__clear:focus-visible {
  color: var(--text);
  outline: none;
}
</style>
