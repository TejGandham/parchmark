<script setup lang="ts">
import { computed } from "vue";

import { GearIcon, LogOutIcon } from "@/design-system/icons";
import { useAuth } from "@/features/auth/useAuth";

interface UserFooterProps {
  active?: boolean;
}

defineProps<UserFooterProps>();

const emit = defineEmits<{
  openSettings: [];
}>();

const { user, logout } = useAuth();

const username = computed(() => user.value?.username ?? "Account");

const initials = computed(
  () => username.value.slice(0, 2).toUpperCase() || "?",
);
</script>

<template>
  <div class="user-footer" :class="{ 'is-active': active }">
    <button
      class="user-footer__main"
      type="button"
      title="Settings"
      @click="emit('openSettings')"
    >
      <span class="user-footer__avatar">{{ initials }}</span>
      <span class="user-footer__identity">
        {{ username }}
      </span>
      <span class="user-footer__settings" aria-hidden="true">
        <GearIcon :aria-hidden="true" />
      </span>
    </button>
    <button
      class="user-footer__logout"
      type="button"
      aria-label="Sign out"
      title="Sign out"
      @click="logout"
    >
      <LogOutIcon :aria-hidden="true" />
    </button>
  </div>
</template>

<style scoped>
.user-footer {
  display: flex;
  align-items: center;
  width: 100%;
  border-top: 1px solid var(--line);
}

.user-footer__main {
  display: flex;
  flex: 1;
  gap: 10px;
  align-items: center;
  min-width: 0;
  padding: 12px 16px;
  color: inherit;
  text-align: left;
  background: transparent;
  border: none;
  transition: background-color 0.14s ease;
}

.user-footer__main:hover,
.user-footer.is-active .user-footer__main {
  background: var(--menu-hover-surface);
}

.user-footer__main:focus-visible {
  outline: none;
  box-shadow: inset 0 0 0 3px var(--focus-ring);
}

.user-footer__logout {
  display: grid;
  flex: none;
  width: 34px;
  height: 34px;
  margin-right: 12px;
  color: var(--muted);
  background: transparent;
  border: 1px solid transparent;
  border-radius: 9px;
  transition:
    color 0.14s ease,
    background-color 0.14s ease;
  place-items: center;
}

.user-footer__logout:hover {
  color: var(--text);
  background: var(--menu-hover-surface);
}

.user-footer__logout:focus-visible {
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
  overflow: hidden;
  color: var(--text);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
  text-overflow: ellipsis;
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
