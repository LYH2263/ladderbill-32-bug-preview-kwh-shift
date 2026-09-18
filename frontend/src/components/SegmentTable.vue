<script setup>
defineProps({ rows: { type: Array, default: () => [] } })
</script>
<template>
  <table v-if="rows.length">
    <thead><tr><th>区间(kWh)</th><th>电量</th><th>单价</th><th>金额</th></tr></thead>
    <tbody>
      <tr v-for="(s, i) in rows" :key="i">
        <td>{{ s.from_kwh }} – {{ s.to_kwh }}</td>
        <td>{{ s.qty }}</td>
        <td>{{ s.price }}</td>
        <td>¥{{ s.amount }}</td>
      </tr>
    </tbody>
  </table>
  <p v-else class="muted">无明细</p>
</template>
