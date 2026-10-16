<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import {
  AlertIcon,
  CopyIcon,
  DownloadIcon,
  GearIcon,
  LockIcon,
  TrashIcon,
} from "@/design-system/icons";
import type { ApiTokenCreatedDTO } from "@/services/auth";

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
  deletingAccount,
  deleteError,
  apiTokens,
  apiTokensLoading,
  apiTokensError,
  creatingApiToken,
  revokingApiTokenId,
  apiTokenActionError,
  fetchUserInfo,
  fetchApiTokens,
  createApiToken,
  revokeApiToken,
  exportNotes,
  changePassword,
  deleteAccount,
  clearPasswordStatus,
  clearExportStatus,
  clearDeleteStatus,
} = useSettings();

const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const clientPasswordError = ref<string | null>(null);

const DELETE_CONFIRMATION = "DELETE";
const deletePassword = ref("");
const deleteConfirmation = ref("");

const tokenName = ref("");
// The plaintext of a just-created token lives only in this view: it is gone once
// dismissed or when Settings closes, and the API never returns it again.
const createdToken = ref<ApiTokenCreatedDTO | null>(null);
const copyStatus = ref<string | null>(null);

onMounted(() => {
  void fetchUserInfo();
  void fetchApiTokens();
});

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

const createdAtLabel = computed(() =>
  userInfo.value ? formatDateTime(userInfo.value.created_at) : "",
);

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

// Local accounts confirm with their password plus the typed phrase; accounts
// without a local password (OIDC and other providers) confirm with the phrase
// alone, which is what the backend accepts as their confirmation.
const canDeleteAccount = computed(() => {
  if (deleteConfirmation.value !== DELETE_CONFIRMATION) return false;
  if (canChangePassword.value) return deletePassword.value.length > 0;
  return true;
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

async function submitDeleteAccount() {
  if (!canDeleteAccount.value) return;
  clearDeleteStatus();

  // Send the password for local accounts, or the typed confirmation for accounts
  // without a local password — exactly as entered for the selected account type.
  const password = canChangePassword.value
    ? deletePassword.value
    : deleteConfirmation.value;

  try {
    await deleteAccount(password);
    // On success the auth session is cleared and App.vue returns to LoginView.
  } catch {
    // The settings store owns the visible delete error; the session is preserved.
  }
}

async function submitCreateToken() {
  const name = tokenName.value.trim();
  if (!name) return;

  try {
    createdToken.value = await createApiToken(name);
    copyStatus.value = null;
    tokenName.value = "";
  } catch {
    // The settings store owns the visible token error.
  }
}

async function copyCreatedToken() {
  if (!createdToken.value) return;

  try {
    await navigator.clipboard.writeText(createdToken.value.token);
    copyStatus.value = "Copied to the clipboard.";
  } catch {
    copyStatus.value = "Couldn't copy. Select the token and copy it by hand.";
  }
}

function dismissCreatedToken() {
  createdToken.value = null;
  copyStatus.value = null;
}

async function submitRevokeToken(id: number) {
  try {
    await revokeApiToken(id);
    if (createdToken.value?.id === id) dismissCreatedToken();
  } catch {
    // The settings store owns the visible token error.
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

      <section
        v-if="userInfo"
        class="settings-view__tokens"
        aria-labelledby="settings-tokens-title"
      >
        <div class="settings-view__section-heading">
          <div class="settings-view__section-icon" aria-hidden="true">
            <LockIcon />
          </div>
          <div>
            <h2 id="settings-tokens-title">API tokens</h2>
            <p>
              Tokens let tools such as the ParchMark MCP server use your account
              without your password. Revoke a token to cut off its access.
            </p>
          </div>
        </div>

        <div
          v-if="createdToken"
          class="settings-view__new-token"
          aria-label="New API token"
          role="region"
        >
          <p>
            Copy <strong>{{ createdToken.name }}</strong> now. You won't be able
            to see it again.
          </p>
          <code class="settings-view__token-value">{{
            createdToken.token
          }}</code>
          <div class="settings-view__token-actions">
            <button
              class="settings-view__action-button"
              type="button"
              @click="copyCreatedToken"
            >
              <CopyIcon />
              Copy token
            </button>
            <button
              class="settings-view__secondary-button"
              type="button"
              @click="dismissCreatedToken"
            >
              Done
            </button>
          </div>
          <p v-if="copyStatus" role="status">{{ copyStatus }}</p>
        </div>

        <form
          class="settings-view__token-form"
          @submit.prevent="submitCreateToken"
        >
          <label>
            Token name
            <input
              v-model="tokenName"
              autocomplete="off"
              maxlength="100"
              name="token-name"
              placeholder="Laptop MCP server"
              required
              type="text"
            />
          </label>

          <button
            type="submit"
            :disabled="!tokenName.trim() || creatingApiToken"
          >
            {{ creatingApiToken ? "Creating..." : "Create token" }}
          </button>
        </form>

        <p
          v-if="apiTokenActionError"
          class="settings-view__inline-message is-error"
          role="alert"
        >
          {{ apiTokenActionError }}
        </p>

        <div v-if="apiTokensLoading" class="settings-view__state" role="status">
          Loading tokens...
        </div>

        <div
          v-else-if="apiTokensError"
          class="settings-view__state is-error"
          role="alert"
        >
          <p>{{ apiTokensError }}</p>
          <button type="button" @click="fetchApiTokens">Retry</button>
        </div>

        <p v-else-if="apiTokens.length === 0">No API tokens yet.</p>

        <ul v-else class="settings-view__token-list" aria-label="API tokens">
          <li
            v-for="token in apiTokens"
            :key="token.id"
            class="settings-view__token-row"
          >
            <div>
              <span class="settings-view__token-name">{{ token.name }}</span>
              <span class="settings-view__token-date">
                Created {{ formatDateTime(token.created_at) }}
              </span>
            </div>
            <button
              class="settings-view__secondary-button"
              type="button"
              :aria-label="`Revoke ${token.name}`"
              :disabled="revokingApiTokenId === token.id"
              @click="submitRevokeToken(token.id)"
            >
              {{ revokingApiTokenId === token.id ? "Revoking..." : "Revoke" }}
            </button>
          </li>
        </ul>
      </section>

      <section
        v-if="userInfo"
        class="settings-view__danger"
        aria-labelledby="settings-danger-title"
      >
        <div class="settings-view__section-heading">
          <div class="settings-view__section-icon is-danger" aria-hidden="true">
            <TrashIcon />
          </div>
          <div>
            <h2 id="settings-danger-title">Delete account</h2>
            <p>
              Permanently delete your account and every note it owns. This
              cannot be undone.
            </p>
          </div>
        </div>

        <p class="settings-view__danger-warning" role="note">
          <span class="settings-view__danger-warning-icon" aria-hidden="true">
            <AlertIcon />
          </span>
          Deleting your account removes all of your notes and signs you out
          immediately.
        </p>

        <form
          class="settings-view__danger-form"
          @submit.prevent="submitDeleteAccount"
        >
          <label v-if="canChangePassword">
            Current password
            <input
              v-model="deletePassword"
              autocomplete="current-password"
              name="delete-password"
              required
              type="password"
            />
          </label>

          <label>
            Type {{ DELETE_CONFIRMATION }} to confirm
            <input
              v-model="deleteConfirmation"
              autocomplete="off"
              name="delete-confirm"
              required
              type="text"
            />
          </label>

          <p
            v-if="deleteError"
            class="settings-view__inline-message is-error"
            role="alert"
          >
            {{ deleteError }}
          </p>

          <button
            class="settings-view__danger-button"
            type="submit"
            :disabled="!canDeleteAccount || deletingAccount"
          >
            {{ deletingAccount ? "Deleting account..." : "Delete account" }}
          </button>
        </form>
      </section>
    </div>
  </section>
</template>

<style scoped>
.settings-view {
  --settings-primary-button-text: var(--button-primary-text, var(--n50));
  --settings-primary-button-radius: var(--button-primary-radius, 10px);
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
.settings-view__security,
.settings-view__tokens,
.settings-view__danger {
  padding-top: 30px;
  margin-top: 30px;
  border-top: 1px solid var(--line-2);
}

.settings-view__section-icon.is-danger {
  color: var(--danger);
  background: var(--danger-surface);
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

.settings-view__password-form,
.settings-view__token-form,
.settings-view__danger-form {
  display: grid;
  gap: 14px;
  max-width: 420px;
}

.settings-view__password-form label,
.settings-view__token-form label,
.settings-view__danger-form label {
  display: grid;
  gap: 6px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.settings-view__password-form input,
.settings-view__token-form input,
.settings-view__danger-form input {
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

.settings-view__password-form input:focus,
.settings-view__token-form input:focus,
.settings-view__danger-form input:focus {
  border-color: var(--accent);
  outline: 2px solid var(--focus-ring);
  outline-offset: 0;
}

.settings-view__danger-warning {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  max-width: 520px;
  margin-bottom: 18px;
  padding: 12px 14px;
  color: var(--danger);
  font-size: 14px;
  background: var(--danger-surface);
  border: 1px solid color-mix(in srgb, var(--danger) 24%, transparent);
  border-radius: var(--r);
}

.settings-view__danger-warning-icon {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
}

.settings-view__danger-warning-icon :deep(svg) {
  width: 18px;
  height: 18px;
}

.settings-view__danger-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  justify-self: start;
  padding: 9px 14px;
  color: var(--settings-primary-button-text);
  font: inherit;
  font-size: 13.5px;
  font-weight: 600;
  background: var(--danger);
  border: none;
  border-radius: var(--settings-primary-button-radius);
  box-shadow: var(--shadow-sm);
  transition:
    background-color 0.15s ease,
    box-shadow 0.15s ease,
    transform 0.1s ease;
}

.settings-view__danger-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.settings-view__danger-button:not(:disabled):hover {
  box-shadow: var(--shadow);
  transform: translateY(-1px);
}

.settings-view__danger-button:not(:disabled):active {
  transform: translateY(0);
}

.settings-view__danger-button:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 3px color-mix(in srgb, var(--danger) 40%, transparent),
    var(--shadow-sm);
}

.settings-view__password-form button,
.settings-view__token-form button,
.settings-view__action-button,
.settings-view__state button {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  justify-content: center;
  padding: 9px 14px;
  color: var(--settings-primary-button-text);
  font: inherit;
  font-size: 13.5px;
  font-weight: 600;
  background: var(--accent);
  border: none;
  border-radius: var(--settings-primary-button-radius);
  box-shadow: var(--shadow-sm);
  transition:
    background-color 0.15s ease,
    box-shadow 0.15s ease,
    transform 0.1s ease;
}

.settings-view__password-form button,
.settings-view__token-form button {
  justify-self: start;
}

.settings-view__action-button {
  justify-self: start;
}

.settings-view__state button {
  margin-top: 12px;
}

.settings-view__password-form button:disabled,
.settings-view__token-form button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.settings-view__action-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.settings-view__password-form button:not(:disabled):hover,
.settings-view__token-form button:not(:disabled):hover,
.settings-view__action-button:not(:disabled):hover,
.settings-view__state button:hover {
  background: var(--accent);
  box-shadow: var(--shadow);
  transform: translateY(-1px);
}

.settings-view__password-form button:not(:disabled):active,
.settings-view__token-form button:not(:disabled):active,
.settings-view__action-button:not(:disabled):active,
.settings-view__state button:active {
  transform: translateY(0);
}

.settings-view__password-form button:focus-visible,
.settings-view__token-form button:focus-visible,
.settings-view__action-button:focus-visible,
.settings-view__state button:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 3px var(--focus-ring),
    var(--shadow-sm);
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

.settings-view__tokens {
  display: grid;
  gap: 16px;
}

.settings-view__tokens .settings-view__section-heading {
  margin-bottom: 4px;
}

.settings-view__new-token {
  display: grid;
  gap: 12px;
  max-width: 520px;
  padding: 14px 16px;
  background: var(--surface);
  border: 1px solid color-mix(in srgb, var(--accent) 24%, transparent);
  border-radius: var(--r);
}

.settings-view__new-token p {
  color: var(--text);
}

.settings-view__token-value {
  display: block;
  padding: 10px 11px;
  color: var(--text);
  font: 13px/1.5 var(--mono);
  overflow-wrap: anywhere;
  user-select: all;
  background: var(--canvas);
  border: 1px solid var(--line-2);
  border-radius: var(--settings-control-radius);
}

.settings-view__token-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.settings-view__action-button :deep(svg) {
  width: 16px;
  height: 16px;
}

.settings-view__token-list {
  padding: 0;
  margin: 0;
  list-style: none;
  border-top: 1px solid var(--line-2);
}

.settings-view__token-row {
  display: flex;
  gap: 16px;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid var(--line-2);
}

.settings-view__token-row > div {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.settings-view__token-name {
  color: var(--text);
  font-size: 15px;
  overflow-wrap: anywhere;
}

.settings-view__token-date {
  color: var(--muted);
  font-size: 13px;
}

.settings-view__secondary-button {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  padding: 8px 13px;
  color: var(--text);
  font: inherit;
  font-size: 13.5px;
  font-weight: 600;
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: var(--settings-primary-button-radius);
  transition: border-color 0.15s ease;
}

.settings-view__token-row .settings-view__secondary-button {
  color: var(--danger);
}

.settings-view__secondary-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.settings-view__secondary-button:not(:disabled):hover {
  border-color: currentColor;
}

.settings-view__secondary-button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px var(--focus-ring);
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
