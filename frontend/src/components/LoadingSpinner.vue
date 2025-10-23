<template>
  <div class="loading-spinner" :class="{ 'loading-spinner--small': size === 'small' }">
    <div class="spinner">
      <div class="spinner-circle"></div>
      <div class="spinner-circle"></div>
      <div class="spinner-circle"></div>
      <div class="spinner-circle"></div>
    </div>
    <p v-if="message" class="loading-message">{{ message }}</p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  message?: string
  size?: 'default' | 'small'
}

withDefaults(defineProps<Props>(), {
  message: '',
  size: 'default',
})
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  min-height: 200px;
}

.loading-spinner--small {
  min-height: 100px;
  padding: 1rem;
}

.spinner {
  position: relative;
  width: 40px;
  height: 40px;
}

.loading-spinner--small .spinner {
  width: 24px;
  height: 24px;
}

.spinner-circle {
  position: absolute;
  width: 100%;
  height: 100%;
  opacity: 0;
  animation: spinner-fade 1.2s linear infinite;
}

.spinner-circle:nth-child(1) {
  animation-delay: 0s;
  transform: rotate(0deg);
}

.spinner-circle:nth-child(2) {
  animation-delay: 0.3s;
  transform: rotate(90deg);
}

.spinner-circle:nth-child(3) {
  animation-delay: 0.6s;
  transform: rotate(180deg);
}

.spinner-circle:nth-child(4) {
  animation-delay: 0.9s;
  transform: rotate(270deg);
}

.spinner-circle::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  width: 8px;
  height: 8px;
  background-color: var(--color-primary, #3b82f6);
  border-radius: 50%;
  transform: translateX(-50%);
}

.loading-spinner--small .spinner-circle::before {
  width: 5px;
  height: 5px;
}

@keyframes spinner-fade {
  0%,
  39%,
  100% {
    opacity: 0;
  }
  40% {
    opacity: 1;
  }
}

.loading-message {
  margin-top: 1rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary, #64748b);
  text-align: center;
}

.loading-spinner--small .loading-message {
  margin-top: 0.5rem;
  font-size: 0.75rem;
}
</style>
