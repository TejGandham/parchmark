<script setup lang="ts">
import { GearIcon } from "@/design-system/icons";

interface UserFooterProps {
  active?: boolean;
}

defineProps<UserFooterProps>();

const emit = defineEmits<{
  openSettings: [];
}>();
</script>

<template>
  <button
    class="user-footer"
    :class="{ 'is-active': active }"
    type="button"
    title="Settings"
    @click="emit('openSettings')"
  >
    <span class="user-footer__avatar">JD</span>
    <span class="user-footer__identity">
      Jamie Doe
      <small>jamie@parchmark.app</small>
    </span>
    <span class="user-footer__settings" aria-hidden="true">
      <GearIcon :aria-hidden="true" />
    </span>
  </button>
</template>

<style scoped>
.user-footer {
  display: flex;
  gap: 10px;
  align-items: center;
  width: 100%;
  padding: 12px 16px;
  color: inherit;
  text-align: left;
  background: transparent;
  border: none;
  border-top: 1px solid var(--line);
  transition: background-color 0.14s ease;
}

.user-footer:hover,
.user-footer.is-active {
  background: var(--menu-hover-surface);
}

.user-footer:focus-visible {
  outline: none;
  box-shadow: inset 0 0 0 3px var(--focus-ring);
}

.user-footer__avatar {
  display: grid;
  flex: none;
  width: 30px;
  height: 30px;
  color: var(--accent);
  font-size: 12.5px;
  font-weight: 700;
  background: var(--focus-ring);
  border-radius: 50%;
  place-items: center;
}

.user-footer__identity {
  color: var(--text);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.2;
}

.user-footer__identity small {
  display: block;
  color: var(--muted);
  font-size: 11px;
  font-weight: 400;
}

.user-footer__settings {
  display: grid;
  width: 32px;
  height: 32px;
  margin-left: auto;
  color: var(--muted);
  border: 1px solid transparent;
  border-radius: 9px;
  place-items: center;
}
</style>
