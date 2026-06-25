<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { DownloadIcon, GearIcon, LockIcon } from "@/design-system/icons";

import { useSettings } from "./useSettings";

const {
  userInfo,
  loading,
  error,
  changingPassword,
  passwordError,
  passwordSuccess,
  exportingNotes,
  exportError,
  fetchUserInfo,
  exportNotes,
  changePassword,
  clearPasswordStatus,
  clearExportStatus,
} = useSettings();

const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const clientPasswordError = ref<string | null>(null);

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

const canChangePassword = computed(
  () => userInfo.value?.auth_provider === "local",
);

const passwordProviderLabel = computed(() => {
  if (userInfo.value?.auth_provider === "oidc") return "OIDC";
  return authProviderLabel.value || "your identity provider";
});

async function submitPasswordChange() {
  clientPasswordError.value = null;
  clearPasswordStatus();

  if (newPassword.value.length < 4) {
    clientPasswordError.value = "New password must be at least 4 characters.";
    return;
  }

  if (newPassword.value !== confirmPassword.value) {
    clientPasswordError.value = "New password and confirmation must match.";
    return;
  }

  try {
    await changePassword(currentPassword.value, newPassword.value);
    currentPassword.value = "";
    newPassword.value = "";
    confirmPassword.value = "";
  } catch {
    // The settings store owns the visible password error.
  }
}

async function submitExportNotes() {
  clearExportStatus();

  try {
    const download = await exportNotes();
    const objectUrl = URL.createObjectURL(download.blob);
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = download.filename;
    anchor.style.display = "none";
    document.body.appendChild(anchor);

    try {
      anchor.click();
    } finally {
      anchor.remove();
      URL.revokeObjectURL(objectUrl);
    }
  } catch {
    // The settings store owns the visible export error.
  }
}
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

      <section
        v-if="userInfo"
        class="settings-view__export"
        aria-labelledby="settings-export-title"
      >
        <div class="settings-view__section-heading">
          <div class="settings-view__section-icon" aria-hidden="true">
            <DownloadIcon />
          </div>
          <div>
            <h2 id="settings-export-title">Export notes</h2>
            <p>Download all of your notes and note metadata as a ZIP backup.</p>
          </div>
        </div>

        <button
          class="settings-view__action-button"
          type="button"
          :disabled="exportingNotes"
          @click="submitExportNotes"
        >
          {{ exportingNotes ? "Preparing download..." : "Download all notes" }}
        </button>

        <p
          v-if="exportError"
          class="settings-view__inline-message is-error"
          role="alert"
        >
          {{ exportError }}
        </p>
      </section>

      <section
        v-if="userInfo"
        class="settings-view__security"
        aria-labelledby="settings-security-title"
      >
        <div class="settings-view__section-heading">
          <div class="settings-view__section-icon" aria-hidden="true">
            <LockIcon />
          </div>
          <div>
            <h2 id="settings-security-title">Password</h2>
            <p>
              Update the password used to sign in with this ParchMark account.
            </p>
          </div>
        </div>

        <form
          v-if="canChangePassword"
          class="settings-view__password-form"
          @submit.prevent="submitPasswordChange"
        >
          <label>
            Current password
            <input
              v-model="currentPassword"
              autocomplete="current-password"
              name="current-password"
              required
              type="password"
            />
          </label>

          <label>
            New password
            <input
              v-model="newPassword"
              autocomplete="new-password"
              minlength="4"
              name="new-password"
              required
              type="password"
            />
          </label>

          <label>
            Confirm new password
            <input
              v-model="confirmPassword"
              autocomplete="new-password"
              minlength="4"
              name="confirm-new-password"
              required
              type="password"
            />
          </label>

          <p
            v-if="clientPasswordError || passwordError"
            class="settings-view__inline-message is-error"
            role="alert"
          >
            {{ clientPasswordError || passwordError }}
          </p>

          <p
            v-if="passwordSuccess"
            class="settings-view__inline-message is-success"
            role="status"
          >
            {{ passwordSuccess }}
          </p>

          <button type="submit" :disabled="changingPassword">
            {{ changingPassword ? "Changing..." : "Change password" }}
          </button>
        </form>

        <p v-else class="settings-view__provider-note">
          This account signs in through {{ passwordProviderLabel }}. Manage your
          password with that identity provider.
        </p>
      </section>
    </div>
  </section>
</template>

<style scoped>
.settings-view {
  --settings-primary-button-text: var(--button-primary-text, var(--n50));
  --settings-control-radius: var(--r-sm, 8px);

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

.settings-view__export,
.settings-view__security {
  padding-top: 30px;
  margin-top: 30px;
  border-top: 1px solid var(--line-2);
}

.settings-view__section-heading {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  margin-bottom: 20px;
}

.settings-view__section-icon {
  display: grid;
  flex: 0 0 auto;
  width: 32px;
  height: 32px;
  place-items: center;
  color: var(--accent);
  background: var(--focus-ring);
  border-radius: var(--settings-control-radius);
}

.settings-view__section-icon :deep(svg) {
  width: 18px;
  height: 18px;
}

.settings-view h2 {
  margin: 0 0 6px;
  color: var(--text);
  font-family: var(--serif);
  font-size: 24px;
  line-height: 1.2;
}

.settings-view__password-form {
  display: grid;
  gap: 14px;
  max-width: 420px;
}

.settings-view__password-form label {
  display: grid;
  gap: 6px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.settings-view__password-form input {
  width: 100%;
  min-width: 0;
  padding: 10px 11px;
  color: var(--text);
  font: inherit;
  font-size: 14px;
  letter-spacing: 0;
  text-transform: none;
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: var(--settings-control-radius);
}

.settings-view__password-form input:focus {
  border-color: var(--accent);
  outline: 2px solid var(--focus-ring);
  outline-offset: 0;
}

.settings-view__password-form button {
  justify-self: start;
  padding: 9px 13px;
  color: var(--settings-primary-button-text);
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  background: var(--accent);
  border: none;
  border-radius: var(--settings-control-radius);
}

.settings-view__action-button {
  justify-self: start;
  padding: 9px 13px;
  color: var(--settings-primary-button-text);
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  background: var(--accent);
  border: none;
  border-radius: var(--settings-control-radius);
}

.settings-view__password-form button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.settings-view__action-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.settings-view__password-form button:not(:disabled):hover,
.settings-view__password-form button:not(:disabled):focus-visible,
.settings-view__action-button:not(:disabled):hover,
.settings-view__action-button:not(:disabled):focus-visible {
  background: var(--accent-600);
  outline: none;
}

.settings-view__inline-message {
  max-width: 420px;
  padding: 10px 12px;
  font-size: 13px;
  border-radius: var(--settings-control-radius);
}

.settings-view__inline-message.is-error {
  color: var(--danger);
  background: var(--danger-surface);
  border: 1px solid color-mix(in srgb, var(--danger) 24%, transparent);
}

.settings-view__inline-message.is-success {
  color: var(--accent);
  background: var(--focus-ring);
  border: 1px solid color-mix(in srgb, var(--accent) 24%, transparent);
}

.settings-view__provider-note {
  max-width: 520px;
  padding: 12px 14px;
  color: var(--muted);
  font-size: 14px;
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: var(--r);
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
  color: var(--settings-primary-button-text);
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  background: var(--accent);
  border: none;
  border-radius: var(--settings-control-radius);
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
