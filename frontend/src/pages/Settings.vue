<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const s = ref({})
onMounted(async () => { s.value = await getJSON('/api/settings') })
</script>
<template>
  <div class="page">
    <h1>参数</h1>
    <ul class="panel kv">
      <li v-for="(v, k) in s" :key="k"><span class="muted">{{ k }}</span> {{ v }}</li>
    </ul>
  </div>
</template>
<style scoped>
.kv { list-style: none; padding: 1rem; margin: 0; }
.kv li { padding: 0.35rem 0; border-bottom: 1px solid color-mix(in srgb, var(--muted) 25%, transparent); }
</style>
