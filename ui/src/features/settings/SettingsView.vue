<script setup lang="ts">
import { computed, onMounted } from "vue";

import { GearIcon } from "@/design-system/icons";

import { useSettings } from "./useSettings";

const { userInfo, loading, error, fetchUserInfo } = useSettings();

onMounted(() => {
  void fetchUserInfo();
});

const createdAtLabel = computed(() => {
  if (!userInfo.value) return "";

  const createdAt = new Date(userInfo.value.created_at);
  if (Number.isNaN(createdAt.getTime())) {
    return userInfo.value.created_at;
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(createdAt);
});

const authProviderLabel = computed(() => {
  const provider = userInfo.value?.auth_provider;
  if (provider === "local") return "Local password";
  if (provider === "oidc") return "OIDC";
  return provider ?? "";
});

const accountRows = computed(() => {
  if (!userInfo.value) return [];

  const rows = [
    { label: "Username", value: userInfo.value.username },
    { label: "Notes", value: String(userInfo.value.notes_count) },
    { label: "Sign-in", value: authProviderLabel.value },
    { label: "Created", value: createdAtLabel.value },
  ];

  if (userInfo.value.email) {
    rows.splice(1, 0, { label: "Email", value: userInfo.value.email });
  }

  return rows;
});
</script>

<template>
  <section class="settings-view" aria-labelledby="settings-title">
    <div class="settings-view__inner">
      <header class="settings-view__header">
        <div class="settings-view__icon" aria-hidden="true">
          <GearIcon />
        </div>
        <div>
          <h1 id="settings-title">Settings</h1>
          <p>Account details for this ParchMark session.</p>
        </div>
      </header>

      <div v-if="loading" class="settings-view__state" role="status">
        Loading account details...
      </div>

      <div v-else-if="error" class="settings-view__state is-error" role="alert">
        <p>{{ error }}</p>
        <button type="button" @click="fetchUserInfo">Retry</button>
      </div>

      <dl v-else-if="userInfo" class="settings-view__facts">
        <div
          v-for="row in accountRows"
          :key="row.label"
          class="settings-view__row"
        >
          <dt>{{ row.label }}</dt>
          <dd>{{ row.value }}</dd>
        </div>
      </dl>
    </div>
  </section>
</template>

<style scoped>
.settings-view {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.settings-view__inner {
  max-width: 720px;
  padding: 54px 56px 110px;
  margin: 0 auto;
}

.settings-view__header {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 28px;
}

.settings-view__icon {
  display: grid;
  flex: 0 0 auto;
  width: 38px;
  height: 38px;
  place-items: center;
  color: var(--accent);
  background: var(--focus-ring);
  border-radius: var(--r);
}

.settings-view__icon :deep(svg) {
  width: 20px;
  height: 20px;
}

.settings-view h1 {
  margin: 0 0 8px;
  color: var(--text);
  font-family: var(--serif);
  font-size: 34px;
  line-height: 1.14;
}

.settings-view p {
  margin: 0;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.55;
}

.settings-view__facts {
  display: grid;
  margin: 0;
  border-top: 1px solid var(--line-2);
}

.settings-view__row {
  display: grid;
  grid-template-columns: minmax(120px, 0.34fr) minmax(0, 1fr);
  gap: 24px;
  padding: 18px 0;
  border-bottom: 1px solid var(--line-2);
}

.settings-view__row dt {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.settings-view__row dd {
  min-width: 0;
  margin: 0;
  color: var(--text);
  font-size: 15px;
  line-height: 1.45;
  overflow-wrap: anywhere;
}

.settings-view__state {
  padding: 14px 16px;
  color: var(--muted);
  font-size: 14px;
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: var(--r);
}

.settings-view__state.is-error {
  color: var(--danger);
  background: var(--danger-surface);
  border-color: color-mix(in srgb, var(--danger) 24%, transparent);
}

.settings-view__state button {
  margin-top: 12px;
  padding: 7px 12px;
  color: var(--button-primary-text);
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  background: var(--accent);
  border: none;
  border-radius: var(--r-sm);
}

.settings-view__state button:hover,
.settings-view__state button:focus-visible {
  background: var(--accent-600);
  outline: none;
}

@media (max-width: 53.75em) {
  .settings-view__inner {
    padding: 40px 24px 100px;
  }

  .settings-view__row {
    grid-template-columns: minmax(0, 1fr);
    gap: 6px;
  }
}
</style>
