<template>
  <div class="card-base p-8 w-full" :class="customClass">
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{ customClass?: string }>()
</script>

<style scoped></style>
