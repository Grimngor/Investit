<template>
	<div class="logs-view">
		<LogViewer />
	</div>
</template>

<script setup lang="ts">
import LogViewer from '@/components/debug/LogViewer.vue'
</script>

<style scoped>
.logs-view {
	height: calc(100vh - 120px);
	padding: 1rem;
}
</style>
