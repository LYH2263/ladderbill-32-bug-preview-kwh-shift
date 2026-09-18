<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const tiers = ref([])
onMounted(async () => { tiers.value = (await getJSON('/api/tiers')).items })
</script>
<template>
  <div class="page">
    <h1>阶梯单价</h1>
    <table>
      <thead><tr><th>顺序</th><th>上限(kWh)</th><th>单价(元)</th></tr></thead>
      <tbody>
        <tr v-for="t in tiers" :key="t.id">
          <td>{{ t.sort_order }}</td>
          <td>{{ t.up_to ?? '以上' }}</td>
          <td>{{ t.price }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
