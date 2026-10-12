<script setup lang="ts">
import DsToolButton from "@/design-system/components/DsToolButton.vue";
import { MoonIcon, SunIcon } from "@/design-system/icons";

interface ThemeToggleButtonProps {
  theme: "light" | "dark";
}

defineProps<ThemeToggleButtonProps>();
defineEmits<{
  toggle: [];
}>();
</script>

<template>
  <DsToolButton
    :label="theme === 'dark' ? 'Switch to Parchment' : 'Switch to Desk lamp'"
    @click="$emit('toggle')"
  >
    <SunIcon v-if="theme === 'dark'" :aria-hidden="true" />
    <MoonIcon v-else :aria-hidden="true" />
  </DsToolButton>
</template>
