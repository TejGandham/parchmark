<script setup lang="ts">
import { ref } from "vue";

import {
  AlertIcon,
  EyeIcon,
  EyeOffIcon,
  FeatherIcon,
  LockIcon,
} from "@/design-system/icons";

import { useAuth } from "./useAuth";

const { error, pending, login } = useAuth();

const username = ref("");
const password = ref("");
const showPw = ref(false);

async function onSubmit() {
  await login(username.value, password.value);
}
</script>

<template>
  <div class="auth-shell">
    <aside class="auth-aside">
      <div class="auth-aside-in">
        <div>
          <div class="auth-brand">Parch<span class="mk">Mark</span></div>
          <p class="auth-tag">A calm home for your markdown.</p>
        </div>
        <blockquote class="auth-quote">
          <p>"The page asks for nothing back. That's the whole trick."</p>
          <span>— from <em>Morning Pages</em></span>
        </blockquote>
        <div class="auth-feats">
          <div class="af">
            <span class="af-ic"><EyeIcon :aria-hidden="true" /></span>
            Read &amp; edit, one tap apart
          </div>
          <div class="af">
            <span class="af-ic"><FeatherIcon :aria-hidden="true" /></span>
            Markdown, GFM &amp; Mermaid, rendered
          </div>
          <div class="af">
            <span class="af-ic"><LockIcon :aria-hidden="true" /></span>
            Your notes, stored on your device
          </div>
        </div>
      </div>
      <div class="auth-aside-foot">Pages, not files. ❧</div>
    </aside>

    <main class="auth-main">
      <div class="auth-card">
        <h1 class="auth-h1">Welcome back</h1>
        <p class="auth-sub">Sign in to pick up where you left off.</p>
        <form class="auth-form" @submit.prevent="onSubmit">
          <label class="fld">
            <span>Username</span>
            <input
              v-model.trim="username"
              autocomplete="username"
              placeholder="jamie"
              :disabled="pending"
            />
          </label>

          <label class="fld">
            <span class="fld-top">Password</span>
            <div class="pw-wrap">
              <input
                v-model="password"
                :type="showPw ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="••••••••"
                :disabled="pending"
              />
              <button
                type="button"
                class="pw-toggle"
                aria-label="Toggle password"
                @click="showPw = !showPw"
              >
                <EyeIcon v-if="showPw" :aria-hidden="true" />
                <EyeOffIcon v-else :aria-hidden="true" />
              </button>
            </div>
          </label>

          <div v-if="error" class="auth-err">
            <AlertIcon :aria-hidden="true" /> {{ error }}
          </div>

          <button type="submit" class="auth-submit" :disabled="pending">
            <span v-if="pending" class="spin"></span> Sign in
          </button>
        </form>
      </div>
    </main>
  </div>
</template>

<style scoped>
.auth-shell {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  height: 100vh;
}

/* One-off burgundy brand gradient: no semantic token exists for this panel,
   so the literal p700/p900-family stops are inlined per the design mock. */
.auth-aside {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 52px 54px;
  overflow: hidden;
  color: #f7ecef;
  background:
    radial-gradient(
      120% 90% at 15% 0%,
      rgba(141, 69, 91, 0.45) 0%,
      transparent 55%
    ),
    linear-gradient(155deg, #5b172e 0%, #42061a 60%, #2e0512 100%);
}

.auth-aside::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: radial-gradient(
    rgba(255, 255, 255, 0.06) 1px,
    transparent 1.4px
  );
  background-size: 26px 26px;
  opacity: 0.5;
}

.auth-aside-in {
  position: relative;
  max-width: 420px;
}

.auth-brand {
  font-family: var(--serif);
  font-size: 40px;
  font-weight: 800;
  letter-spacing: -0.015em;
}

.auth-brand .mk {
  color: #e9b8c4;
}

.auth-tag {
  margin: 8px 0 0;
  color: #e3c3cd;
  font-family: var(--serif);
  font-size: 20px;
  font-style: italic;
  font-weight: 500;
}

.auth-quote {
  margin: 48px 0;
  padding-left: 20px;
  border-left: 3px solid rgba(233, 184, 196, 0.5);
}

.auth-quote p {
  margin: 0 0 10px;
  color: #fbf2f4;
  font-family: var(--serif);
  font-size: 23px;
  font-style: italic;
  line-height: 1.45;
}

.auth-quote span {
  color: #d3a6b2;
  font-size: 13.5px;
}

.auth-quote em {
  color: #ecc4cf;
}

.auth-feats {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.af {
  display: flex;
  gap: 11px;
  align-items: center;
  color: #eccfd6;
  font-size: 14px;
}

.af-ic {
  display: grid;
  flex: none;
  width: 30px;
  height: 30px;
  color: #f0d3da;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  place-items: center;
}

.auth-aside-foot {
  position: relative;
  color: #c79aa6;
  font-family: var(--serif);
  font-size: 15px;
  font-style: italic;
}

.auth-main {
  display: grid;
  padding: 40px;
  background: var(--canvas);
  place-items: center;
}

.auth-card {
  width: min(400px, 100%);
}

.auth-h1 {
  margin: 0 0 6px;
  color: var(--text);
  font-family: var(--serif);
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.auth-sub {
  margin: 0 0 26px;
  color: var(--muted);
  font-size: 14.5px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.fld {
  display: grid;
  gap: 7px;
}

.fld > span,
.fld-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--text-2);
  font-size: 13px;
  font-weight: 600;
}

.fld input {
  width: 100%;
  padding: 11px 13px;
  color: var(--text);
  font-family: inherit;
  font-size: 14.5px;
  background: var(--surface);
  border: 1px solid var(--line-2);
  border-radius: 10px;
  outline: none;
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}

/* mock used --p300 for the focus border; --accent-600 is the nearest token */
.fld input:focus {
  border-color: var(--accent-600);
  box-shadow: 0 0 0 3px var(--focus-ring);
}

.fld input::placeholder {
  color: var(--muted);
}

.pw-wrap {
  position: relative;
}

.pw-wrap input {
  padding-right: 42px;
}

.pw-toggle {
  position: absolute;
  top: 50%;
  right: 6px;
  display: grid;
  width: 30px;
  height: 30px;
  color: var(--muted);
  background: none;
  border: none;
  border-radius: 8px;
  transform: translateY(-50%);
  place-items: center;
}

.pw-toggle:hover {
  color: var(--text);
}

.auth-err {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 9px 12px;
  color: var(--danger);
  font-size: 13px;
  font-weight: 500;
  background: var(--danger-surface);
  border-radius: 9px;
}

.auth-submit {
  display: inline-flex;
  gap: 9px;
  align-items: center;
  justify-content: center;
  width: 100%;
  margin-top: 2px;
  padding: 12px;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  background: var(--accent);
  border: none;
  border-radius: 11px;
  box-shadow: var(--shadow-sm);
  transition: all 0.15s;
}

.auth-submit:hover:not(:disabled) {
  box-shadow: var(--shadow);
  transform: translateY(-1px);
}

.auth-submit:disabled {
  cursor: default;
  opacity: 0.7;
}

.spin {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 860px) {
  .auth-shell {
    grid-template-columns: 1fr;
  }

  .auth-aside {
    display: none;
  }
}
</style>
