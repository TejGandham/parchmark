<script setup lang="ts">
import { ref, type Component } from "vue";

interface SegmentOption {
  value: string;
  label: string;
  icon?: Component;
  disabled?: boolean;
}

interface DsSegmentProps {
  modelValue: string;
  options: SegmentOption[];
  ariaLabel: string;
}

const props = defineProps<DsSegmentProps>();
const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const optionButtons = ref<HTMLButtonElement[]>([]);

function selectOption(option: SegmentOption) {
  if (!option.disabled) {
    emit("update:modelValue", option.value);
  }
}

function focusOption(index: number) {
  const available = props.options
    .map((option, optionIndex) => ({ option, optionIndex }))
    .filter(({ option }) => !option.disabled);

  if (available.length === 0) return;

  const normalizedIndex = (index + available.length) % available.length;
  const nextIndex = available[normalizedIndex]?.optionIndex;

  if (nextIndex !== undefined) {
    optionButtons.value[nextIndex]?.focus();
  }
}

function handleKeydown(event: KeyboardEvent, index: number) {
  const enabledIndex = props.options.filter(
    (option, optionIndex) => !option.disabled && optionIndex < index,
  ).length;

  if (event.key === "ArrowRight" || event.key === "ArrowDown") {
    event.preventDefault();
    focusOption(enabledIndex + 1);
  }

  if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
    event.preventDefault();
    focusOption(enabledIndex - 1);
  }

  if (event.key === "Home") {
    event.preventDefault();
    focusOption(0);
  }

  if (event.key === "End") {
    event.preventDefault();
    focusOption(props.options.filter((option) => !option.disabled).length - 1);
  }
}
</script>

<template>
  <div class="ds-segment" role="radiogroup" :aria-label="ariaLabel">
    <button
      v-for="(option, index) in options"
      :key="option.value"
      ref="optionButtons"
      class="ds-segment__item"
      :class="{ 'is-active': option.value === modelValue }"
      type="button"
      role="radio"
      :aria-checked="option.value === modelValue"
      :disabled="option.disabled"
      :tabindex="option.value === modelValue ? 0 : -1"
      @click="selectOption(option)"
      @keydown="handleKeydown($event, index)"
    >
      <component :is="option.icon" v-if="option.icon" :aria-hidden="true" />
      <span>{{ option.label }}</span>
    </button>
  </div>
</template>

<style scoped>
.ds-segment {
  display: inline-flex;
  gap: 2px;
  padding: 3px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: var(--segment-radius);
}

.ds-segment__item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 15px;
  color: var(--text-2);
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  background: transparent;
  border: none;
  border-radius: var(--segment-item-radius);
  transition:
    background-color 0.15s ease,
    box-shadow 0.15s ease,
    color 0.15s ease;
}

.ds-segment__item:not(.is-active):hover:not(:disabled) {
  color: var(--text);
}

.ds-segment__item.is-active {
  color: var(--accent);
  background: var(--surface);
  box-shadow: var(--shadow-sm);
}

.ds-segment__item:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 3px var(--focus-ring),
    var(--shadow-sm);
}

.ds-segment__item:disabled {
  cursor: default;
  opacity: 0.5;
}
</style>
