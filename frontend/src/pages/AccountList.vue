<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => { items.value = (await getJSON('/api/accounts')).items })
</script>
<template>
  <div class="page">
    <h1>户号列表</h1>
    <table>
      <thead><tr><th>名称</th><th>表号</th><th>备注</th><th></th></tr></thead>
      <tbody>
        <tr v-for="a in items" :key="a.id">
          <td>{{ a.name }}</td><td>{{ a.meter_no }}</td><td class="muted">{{ a.note }}</td>
          <td><router-link :to="`/accounts/${a.id}`">详情</router-link></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
