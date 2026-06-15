<script setup lang="ts">
interface EditingFlagProps {
  label?: string;
}

withDefaults(defineProps<EditingFlagProps>(), {
  label: "Editing",
});
</script>

<template>
  <span class="editing-flag" role="status">
    <span class="editing-flag__pulse" aria-hidden="true" />
    {{ label }}
  </span>
</template>

<style scoped>
.editing-flag {
  display: inline-flex;
  gap: var(--segment-item-radius);
  align-items: center;
  color: var(--accent);
  font-size: 13px;
  font-weight: 600;
}

.editing-flag__pulse {
  width: var(--segment-item-radius);
  height: var(--segment-item-radius);
  background: var(--accent);
  border-radius: 50%;
  animation: editing-pulse 1.6s ease-in-out infinite;
}

@keyframes editing-pulse {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.3;
  }
}
</style>
