<script setup lang="ts">
import { computed, markRaw, ref } from "vue";

import DsMenu from "@/design-system/components/DsMenu.vue";
import DsSegment from "@/design-system/components/DsSegment.vue";
import DsToolButton from "@/design-system/components/DsToolButton.vue";
import {
  CopyIcon,
  DownloadIcon,
  EditIcon,
  EyeIcon,
  MoreIcon,
  PlusIcon,
  SearchIcon,
  TrashIcon,
} from "@/design-system/icons";

const mode = ref("read");
const menuOpen = ref(false);

const segmentOptions = [
  { value: "read", label: "Read", icon: markRaw(EyeIcon) },
  { value: "edit", label: "Edit", icon: markRaw(EditIcon) },
];

const menuItems = [
  { id: "copy", label: "Copy link", icon: markRaw(CopyIcon) },
  { id: "download", label: "Download", icon: markRaw(DownloadIcon) },
  {
    id: "delete",
    label: "Delete note",
    icon: markRaw(TrashIcon),
    danger: true,
    separatorBefore: true,
  },
];

const modeLabel = computed(() =>
  mode.value === "read" ? "Reading" : "Editing",
);
</script>

<template>
  <main class="v2-shell">
    <header class="v2-topbar" aria-label="Note toolbar">
      <button class="v2-brand" type="button" aria-label="ParchMark home">
        Parch<span>Mark</span>
      </button>

      <div class="v2-crumb" aria-live="polite">
        Notes
        <span aria-hidden="true">/</span>
        <strong>{{ modeLabel }}</strong>
      </div>

      <div class="v2-spacer" />

      <DsToolButton label="New note">
        <PlusIcon :aria-hidden="true" />
      </DsToolButton>

      <DsToolButton label="Search notes">
        <SearchIcon :aria-hidden="true" />
      </DsToolButton>

      <DsSegment
        v-model="mode"
        ariaLabel="Note view mode"
        :options="segmentOptions"
      />

      <div class="v2-menu-anchor">
        <DsToolButton
          id="v2-overflow-trigger"
          label="More actions"
          :active="menuOpen"
          @click="menuOpen = !menuOpen"
        >
          <MoreIcon :aria-hidden="true" />
        </DsToolButton>
        <DsMenu
          :open="menuOpen"
          :items="menuItems"
          labelledBy="v2-overflow-trigger"
          @close="menuOpen = false"
          @select="menuOpen = false"
        />
      </div>
    </header>
  </main>
</template>

<style scoped>
.v2-shell {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: var(--canvas);
}

.v2-shell::before {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  content: "";
  background-image: radial-gradient(var(--paper-grain) 1px, transparent 1.3px);
  background-size: 24px 24px;
}

.v2-topbar {
  position: relative;
  z-index: 1;
  display: flex;
  gap: var(--topbar-gap);
  align-items: center;
  padding: var(--topbar-padding-y) var(--topbar-padding-x);
  background: var(--topbar-bg);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(8px);
}

.v2-brand {
  padding: 0;
  color: var(--text);
  font-family: var(--serif);
  font-size: 25px;
  font-weight: 800;
  line-height: 1;
  background: transparent;
  border: none;
}

.v2-brand span {
  color: var(--accent);
}

.v2-brand:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px var(--focus-ring);
}

.v2-crumb {
  display: flex;
  gap: 7px;
  align-items: center;
  color: var(--muted);
  font-size: 13px;
}

.v2-crumb strong {
  color: var(--text-2);
  font-weight: 600;
}

.v2-spacer {
  flex: 1;
}

.v2-menu-anchor {
  position: relative;
}

.v2-menu-anchor :deep(.ds-menu) {
  top: calc(var(--tool-size) + 8px);
  right: 0;
}
</style>
