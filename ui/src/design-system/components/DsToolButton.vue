<script setup lang="ts">
interface DsToolButtonProps {
  label: string;
  active?: boolean;
  disabled?: boolean;
  type?: "button" | "submit";
}

withDefaults(defineProps<DsToolButtonProps>(), {
  active: false,
  disabled: false,
  type: "button",
});
</script>

<template>
  <button
    class="ds-tool-button"
    :class="{ 'is-active': active }"
    :type="type"
    :aria-label="label"
    :aria-pressed="active || undefined"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>

<style scoped>
.ds-tool-button {
  position: relative;
  display: grid;
  width: var(--tool-size);
  height: var(--tool-size);
  padding: 0;
  color: var(--text-2);
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: var(--tool-radius);
  place-items: center;
  transition:
    border-color 0.14s ease,
    box-shadow 0.14s ease,
    color 0.14s ease,
    transform 0.14s ease;
}

.ds-tool-button:hover:not(:disabled),
.ds-tool-button.is-active {
  color: var(--accent);
  border-color: var(--tool-hover-border);
}

.ds-tool-button.is-active {
  box-shadow: var(--shadow-sm);
}

.ds-tool-button:active:not(:disabled) {
  transform: translateY(1px);
}

.ds-tool-button:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 3px var(--focus-ring),
    var(--shadow-sm);
}

.ds-tool-button:disabled {
  cursor: default;
  opacity: 0.5;
}
</style>
