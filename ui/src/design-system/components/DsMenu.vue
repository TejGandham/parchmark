<script setup lang="ts">
import { nextTick, ref, watch, type Component } from "vue";

interface DsMenuItem {
  id: string;
  label: string;
  icon?: Component;
  danger?: boolean;
  separatorBefore?: boolean;
}

interface DsMenuProps {
  open: boolean;
  items: DsMenuItem[];
  labelledBy: string;
}

const props = defineProps<DsMenuProps>();
const emit = defineEmits<{
  close: [];
  select: [id: string];
}>();

const menuItems = ref<HTMLButtonElement[]>([]);

watch(
  () => props.open,
  async (open) => {
    if (open) {
      await nextTick();
      menuItems.value[0]?.focus();
    }
  },
);

function focusItem(index: number) {
  if (menuItems.value.length === 0) return;
  const normalizedIndex =
    (index + menuItems.value.length) % menuItems.value.length;
  menuItems.value[normalizedIndex]?.focus();
}

function handleKeydown(event: KeyboardEvent, index: number) {
  if (event.key === "Escape") {
    event.preventDefault();
    emit("close");
  }

  if (event.key === "ArrowDown") {
    event.preventDefault();
    focusItem(index + 1);
  }

  if (event.key === "ArrowUp") {
    event.preventDefault();
    focusItem(index - 1);
  }

  if (event.key === "Home") {
    event.preventDefault();
    focusItem(0);
  }

  if (event.key === "End") {
    event.preventDefault();
    focusItem(menuItems.value.length - 1);
  }
}
</script>

<template>
  <div v-if="open" class="ds-menu" role="menu" :aria-labelledby="labelledBy">
    <template v-for="(item, index) in items" :key="item.id">
      <div
        v-if="item.separatorBefore"
        class="ds-menu__separator"
        role="separator"
      />
      <button
        ref="menuItems"
        class="ds-menu__item"
        :class="{ 'is-danger': item.danger }"
        type="button"
        role="menuitem"
        @click="emit('select', item.id)"
        @keydown="handleKeydown($event, index)"
      >
        <component :is="item.icon" v-if="item.icon" :aria-hidden="true" />
        <span>{{ item.label }}</span>
      </button>
    </template>
  </div>
</template>

<style scoped>
.ds-menu {
  position: absolute;
  z-index: 30;
  min-width: 184px;
  padding: 6px;
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: var(--menu-radius);
  box-shadow: var(--shadow-lg);
}

.ds-menu__item {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;
  padding: 9px 11px;
  color: var(--text);
  font: inherit;
  font-size: 13.5px;
  font-weight: 500;
  text-align: left;
  background: transparent;
  border: none;
  border-radius: calc(var(--menu-radius) - 4px);
  transition:
    background-color 0.12s ease,
    color 0.12s ease;
}

.ds-menu__item:hover,
.ds-menu__item:focus-visible {
  color: var(--text);
  background: var(--surface-2);
  outline: none;
}

.ds-menu__item:focus-visible {
  box-shadow: 0 0 0 3px var(--focus-ring);
}

.ds-menu__item.is-danger {
  color: var(--danger);
}

.ds-menu__item.is-danger:hover,
.ds-menu__item.is-danger:focus-visible {
  background: var(--danger-surface);
}

.ds-menu__separator {
  height: 1px;
  margin: 5px 4px;
  background: var(--line);
}
</style>
