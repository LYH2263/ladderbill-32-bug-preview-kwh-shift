<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { getJSON, postJSON } from '../api'

const accounts = ref([])
const readings = ref([])
const rows = ref([blank(), blank()])
const preview = ref(null)
const overwrite = ref(false)
const failures = ref([])
const notice = ref('')
const errorMsg = ref('')
const busy = ref(false)

function blank() {
  return { account_id: null, period: '', kwh: null, peak: false }
}

const load = async () => {
  accounts.value = (await getJSON('/api/accounts')).items
  readings.value = (await getJSON('/api/readings')).items
}
onMounted(load)

// 编辑内容变化后，旧预览（及令牌）作废，需重新预览
watch(rows, () => { preview.value = null; failures.value = [] }, { deep: true })

const addRow = () => rows.value.push(blank())
const removeRow = (i) => rows.value.splice(i, 1)

const payload = () => rows.value.map((r) => ({
  account_id: r.account_id === null || r.account_id === '' ? null : Number(r.account_id),
  period: r.period || null,
  kwh: r.kwh === null || r.kwh === '' ? null : Number(r.kwh),
  peak: !!r.peak,
}))

const doPreview = async () => {
  notice.value = ''; errorMsg.value = ''; failures.value = []
  try {
    preview.value = await postJSON('/api/readings/preview', { rows: payload() })
  } catch (e) {
    errorMsg.value = '预览失败：' + e.message
  }
}

const parseDetail = (e) => {
  try { return JSON.parse(e.message)?.detail } catch { return null }
}

const doConfirm = async () => {
  if (!preview.value?.token) return
  notice.value = ''; errorMsg.value = ''; failures.value = []
  busy.value = true
  try {
    const r = await postJSON('/api/readings/confirm', { token: preview.value.token, overwrite: overwrite.value })
    notice.value = `已写入 ${r.total} 条（新增 ${r.inserted}，替换 ${r.replaced}）`
    rows.value = [blank()]
    preview.value = null
    overwrite.value = false
    await load()
  } catch (e) {
    const d = parseDetail(e)
    if (d?.failures) {
      failures.value = d.failures
      errorMsg.value = d.message || '批次未写入'
    } else if (d?.message) {
      errorMsg.value = d.message
      preview.value = null  // 令牌失效，需重新预览
    } else {
      errorMsg.value = '确认失败：' + e.message
    }
  } finally {
    busy.value = false
  }
}

const rowResult = (line) => preview.value?.rows.find((r) => r.line === line)
const hasConflict = computed(() => (preview.value?.conflict_count || 0) > 0)
const statusText = (r) => (r.status === 'ok' ? '✓ 通过' : r.status === 'conflict' ? '⚠ 撞期' : '✗ ' + r.error_code)
</script>

<template>
  <div class="page">
    <h1>抄表录入</h1>

    <div class="panel">
      <h3>批量录入</h3>
      <table>
        <thead>
          <tr>
            <th>#</th><th>户号</th><th>账期</th><th>电量(kWh)</th><th>尖峰</th>
            <th v-if="preview">校验</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, i) in rows" :key="i">
            <td>{{ i + 1 }}</td>
            <td>
              <select v-model="r.account_id">
                <option :value="null" disabled>选择户号</option>
                <option v-for="a in accounts" :key="a.id" :value="a.id">{{ a.name }}（{{ a.meter_no }}）</option>
              </select>
            </td>
            <td><input type="month" v-model="r.period" /></td>
            <td><input type="number" v-model.number="r.kwh" min="0" step="0.01" placeholder="0" /></td>
            <td><input type="checkbox" v-model="r.peak" /></td>
            <td v-if="preview">
              <span v-if="rowResult(i + 1)" class="tag" :class="rowResult(i + 1).status" :title="rowResult(i + 1).message">
                {{ statusText(rowResult(i + 1)) }}
              </span>
            </td>
            <td><button class="ghost" @click="removeRow(i)" :disabled="rows.length <= 1">删</button></td>
          </tr>
        </tbody>
      </table>
      <div class="actions">
        <button class="ghost" @click="addRow">+ 添加行</button>
        <button @click="doPreview" :disabled="!rows.length">预览</button>
      </div>
    </div>

    <div v-if="preview" class="panel">
      <h3>预览结果</h3>
      <template v-if="preview.all_valid">
        <p>
          全部 {{ preview.rows.length }} 行通过校验，电量合计
          <strong class="hero-num" style="font-size:1.4rem">{{ preview.total_kwh }}</strong> kWh
        </p>
        <p v-if="hasConflict" class="warn">{{ preview.conflict_count }} 行与已有抄表撞期，确认将替换旧记录</p>
      </template>
      <p v-else class="err">{{ preview.error_count }} 行校验失败，请修正后重新预览</p>
      <ul v-if="preview.error_count || preview.conflict_count" class="issues">
        <li v-for="r in preview.rows.filter((x) => x.status !== 'ok')" :key="r.line">
          第 {{ r.line }} 行 <code>{{ r.error_code }}</code>：{{ r.message }}
        </li>
      </ul>
      <template v-if="preview.token">
        <label v-if="hasConflict" class="overwrite">
          <input type="checkbox" v-model="overwrite" /> 覆盖同户同账期已有抄表
        </label>
        <button @click="doConfirm" :disabled="busy">确认写入</button>
      </template>
      <p v-if="failures.length" class="err">
        <span v-for="f in failures" :key="f.line">第 {{ f.line }} 行：{{ f.message }}<br /></span>
      </p>
    </div>

    <p v-if="notice" class="ok-msg">{{ notice }}</p>
    <p v-if="errorMsg" class="err">{{ errorMsg }}</p>

    <div class="panel">
      <h3>抄表记录（共 {{ readings.length }} 条）</h3>
      <table>
        <thead><tr><th>ID</th><th>户号</th><th>表号</th><th>账期</th><th>电量(kWh)</th><th>尖峰</th></tr></thead>
        <tbody>
          <tr v-for="r in readings" :key="r.id">
            <td>{{ r.id }}</td>
            <td>{{ r.account_name || r.account_id }}</td>
            <td class="muted">{{ r.meter_no }}</td>
            <td>{{ r.period || '—' }}</td>
            <td>{{ r.kwh }}</td>
            <td>{{ r.peak ? '是' : '否' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
select { background: #0d1612; border: 1px solid var(--muted); color: var(--text); padding: 0.35rem 0.5rem; border-radius: 6px; }
input[type='number'] { width: 7rem; }
.actions { display: flex; gap: 0.6rem; margin-top: 0.8rem; }
button.ghost { background: transparent; border: 1px solid var(--muted); color: var(--text); }
button:disabled { opacity: 0.5; cursor: not-allowed; }
.tag { padding: 0.1rem 0.45rem; border-radius: 6px; font-size: 0.85rem; white-space: nowrap; }
.tag.ok { color: var(--accent); }
.tag.conflict { color: #f0b429; }
.tag.error { color: #ff6b6b; }
.err { color: #ff6b6b; }
.warn { color: #f0b429; }
.ok-msg { color: var(--accent); font-weight: 600; }
.issues { margin: 0.5rem 0; padding-left: 1.2rem; }
.overwrite { display: block; margin-bottom: 0.7rem; }
</style>
