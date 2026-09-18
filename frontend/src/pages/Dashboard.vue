<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const stats = ref(null)
onMounted(async () => { stats.value = await getJSON('/api/dashboard') })
</script>
<template>
  <div class="page dash">
    <header><h1>用电总览</h1><p class="muted">阶梯累进 + 尖峰系数对照</p></header>
    <div class="tiles" v-if="stats">
      <div class="tile"><div class="hero-num">{{ stats.account_count }}</div><div class="muted">户号</div></div>
      <div class="tile"><div class="hero-num">{{ stats.reading_count }}</div><div class="muted">抄表</div></div>
      <div class="tile ok"><div class="hero-num">{{ stats.clean_accounts }}</div><div class="muted">正常对照</div></div>
      <div class="tile warn"><div class="hero-num">{{ stats.dirty_accounts }}</div><div class="muted">偏高种子</div></div>
    </div>
    <router-link to="/compare">去看尖峰对比 →</router-link>
  </div>
</template>
<style scoped>
.dash header { margin-bottom: 1rem; }
.tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1rem; }
.tile { background: var(--panel); padding: 1rem; border-radius: 12px; }
.tile.warn { border: 1px solid #e6a817; }
.tile.ok { border: 1px solid var(--accent); }
</style>
