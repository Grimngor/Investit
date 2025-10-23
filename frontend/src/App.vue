<template>
  <div id="app" :class="{ dark: isDark }">
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
import { useThemeStore } from './stores/theme'

const themeStore = useThemeStore()
const isDark = computed(() => themeStore.isDark)
const route = useRoute()
const showNavigation = computed(() => route.path !== '/')
</script>

<style scoped>
#app {
  min-height: 100vh;
  transition: background-color 0.3s ease;
}
</style>
