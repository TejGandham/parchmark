<script setup lang="ts">
import { onMounted, ref } from "vue";

import { useAuth } from "@/features/auth/useAuth";
import LoginView from "@/features/auth/LoginView.vue";
import AppShell from "@/features/shell/AppShell.vue";

const { isAuthenticated, restoreSession } = useAuth();

// Gate rendering until the stored session has been validated, so an
// authenticated reload does not flash the LoginView before `restoreSession`
// resolves.
const ready = ref(false);

onMounted(async () => {
  await restoreSession();
  ready.value = true;
});
</script>

<template>
  <div v-if="!ready" class="app-loading" aria-busy="true" />
  <LoginView v-else-if="!isAuthenticated" />
  <AppShell v-else />
</template>

<style scoped>
.app-loading {
  width: 100%;
  height: 100vh;
  background: var(--canvas);
}
</style>
