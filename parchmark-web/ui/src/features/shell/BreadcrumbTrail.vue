<script setup lang="ts">
interface BreadcrumbTrailProps {
  title: string;
  activeTags: string[];
}

defineProps<BreadcrumbTrailProps>();
</script>

<template>
  <nav class="breadcrumb-trail" aria-label="Current note">
    <template v-if="activeTags.length">
      <span>Filtered</span>
      <strong v-for="tag in activeTags" :key="tag">#{{ tag }}</strong>
    </template>
    <span v-else>All notes</span>
    <template v-if="title">
      <span class="breadcrumb-trail__slash" aria-hidden="true">/</span>
      <strong>{{ title }}</strong>
    </template>
  </nav>
</template>

<style scoped>
.breadcrumb-trail {
  display: flex;
  gap: var(--segment-item-radius);
  align-items: center;
  min-width: 0;
  overflow: hidden;
  color: var(--muted);
  font-size: 13px;
  white-space: nowrap;
}

.breadcrumb-trail strong {
  overflow: hidden;
  color: var(--text-2);
  font-weight: 600;
  text-overflow: ellipsis;
}

.breadcrumb-trail__slash {
  color: var(--line-2);
}
</style>
