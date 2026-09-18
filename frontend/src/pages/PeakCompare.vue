<script setup>
import { ref } from 'vue'
import { postJSON } from '../api'
const kwh = ref(400)
const cmp = ref(null)
const run = async () => { cmp.value = await postJSON('/api/compare', { kwh: kwh.value, persist: true }) }
</script>
<template>
  <div class="page">
    <h1>平段 vs 尖峰</h1>
    <div class="panel">
      <label>电量 <input type="number" v-model.number="kwh" /></label>
      <button @click="run">对比</button>
    </div>
    <div v-if="cmp" class="compare-grid">
      <div class="panel"><h3>平段</h3><div class="hero-num">¥{{ cmp.plain_total }}</div></div>
      <div class="panel"><h3>尖峰 ×{{ cmp.peak_factor }}</h3><div class="hero-num">¥{{ cmp.peak_total }}</div></div>
      <div class="panel"><h3>差额</h3><div class="hero-num">¥{{ cmp.delta }}</div></div>
    </div>
  </div>
</template>
<style scoped>
.compare-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
</style>
