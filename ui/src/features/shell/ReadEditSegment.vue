<script setup lang="ts">
import { markRaw } from "vue";

import DsSegment from "@/design-system/components/DsSegment.vue";
import { EditIcon, EyeIcon } from "@/design-system/icons";

import type { NoteMode } from "./headerTypes";

interface ReadEditSegmentProps {
  mode: NoteMode;
  disabled?: boolean;
}

withDefaults(defineProps<ReadEditSegmentProps>(), {
  disabled: false,
});

const emit = defineEmits<{
  "update:mode": [mode: NoteMode];
  startEdit: [];
}>();

const segmentOptions = [
  { value: "read", label: "Read", icon: markRaw(EyeIcon) },
  { value: "edit", label: "Edit", icon: markRaw(EditIcon) },
];

function updateMode(value: string) {
  const nextMode = value as NoteMode;
  emit("update:mode", nextMode);
  if (nextMode === "edit") {
    emit("startEdit");
  }
}
</script>

<template>
  <DsSegment
    :modelValue="mode"
    :options="
      segmentOptions.map((option) => ({
        ...option,
        disabled: disabled && option.value === 'edit',
      }))
    "
    ariaLabel="Note view mode"
    @update:modelValue="updateMode"
  />
</template>
