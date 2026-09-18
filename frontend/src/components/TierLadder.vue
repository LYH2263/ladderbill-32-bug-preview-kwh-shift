<script setup>
defineProps({ segments: { type: Array, default: () => [] }, maxKwh: { type: Number, default: 400 } })
</script>
<template>
  <div class="ladder">
    <div
      v-for="(s, i) in segments"
      :key="i"
      class="rung"
      :style="{ flex: s.qty, background: `color-mix(in srgb, var(--accent) ${40 + i * 15}%, var(--panel))` }"
    >
      <span>{{ s.from_kwh }}–{{ s.to_kwh }} kWh</span>
      <strong>¥{{ s.amount }}</strong>
    </div>
    <div v-if="!segments.length" class="muted">暂无分段</div>
  </div>
</template>
<style scoped>
.ladder { display: flex; gap: 4px; min-height: 72px; align-items: stretch; }
.rung { border-radius: 8px; padding: 0.5rem; display: flex; flex-direction: column; justify-content: space-between; font-size: 0.85rem; }
</style>
