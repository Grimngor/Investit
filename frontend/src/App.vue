<template>
  <div id="app">
    <Navigation v-if="showNavigation" />
    <RouterView />
    <ToastContainer />
  </div>
</template>

<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import { computed } from 'vue'
import Navigation from './components/Navigation.vue'
import ToastContainer from './components/ToastContainer.vue'
// Theme store is imported to ensure reactive updates if other components depend on it
import { useThemeStore } from './stores/theme'
useThemeStore() // initialization side-effects handled internally
const route = useRoute()
const showNavigation = computed(() => route.path !== '/')
</script>

<style scoped>
#app { min-height: 100vh; }
</style>
