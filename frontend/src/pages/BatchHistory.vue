<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'

const items = ref([])
const includeVoided = ref(false)
const highlightId = ref(null)
const error = ref('')

const resultOf = (h) => {
  try { return JSON.parse(h.result_json) } catch { return {} }
}
const load = async () => {
  error.value = ''
  const q = includeVoided.value ? '?include_voided=true' : ''
  items.value = (await getJSON('/api/history' + q)).items
}
const voidRun = async (h) => {
  if (!confirm(`确认将 #${h.id} 标记作废？作废后默认列表不再展示，数值不会被改写。`)) return
  try {
    await postJSON(`/api/runs/${h.id}/void`, {})
    await load()
  } catch (e) { error.value = `#${h.id} 作废失败：${e.message}` }
}
const remeasure = async (h) => {
  if (h.room_id == null) { error.value = `#${h.id} 缺少房间参数，无法再测`; return }
  try {
    const r = await postJSON('/api/estimate', { room_id: h.room_id, persist: true, supersedes_id: h.id })
    highlightId.value = r.run_id
    await load()
  } catch (e) { error.value = `#${h.id} 再测失败：${e.message}` }
}

onMounted(load)
</script>
<template><div class="page">
  <h1>估算记录</h1>
  <label class="filter"><input type="checkbox" v-model="includeVoided" @change="load" /> 显示已作废</label>
  <p v-if="error" class="error">{{ error }}</p>
  <table>
    <thead><tr><th>编号</th><th>时间</th><th>升数</th><th>净面积 m²</th><th>涂布率</th><th>状态</th><th>挂接</th><th>操作</th></tr></thead>
    <tbody>
      <tr v-for="h in items" :key="h.id" :class="{ voided: h.voided, fresh: h.id === highlightId }">
        <td><router-link :to="`/history/${h.id}`">#{{ h.id }}</router-link></td>
        <td>{{ h.created_at }}</td>
        <td>{{ resultOf(h).liters }}</td>
        <td>{{ resultOf(h).net_m2 }}</td>
        <td>{{ resultOf(h).coverage }}</td>
        <td><span v-if="h.voided" class="tag">已作废</span><span v-else class="tag tag-ok">有效</span></td>
        <td><router-link v-if="h.supersedes_id" :to="`/history/${h.supersedes_id}`">#{{ h.supersedes_id }}</router-link></td>
        <td>
          <button v-if="!h.voided" @click="voidRun(h)">作废</button>
          <button @click="remeasure(h)">再测</button>
        </td>
      </tr>
    </tbody>
  </table>
  <p v-if="highlightId" class="hint">再测已写入 <router-link :to="`/history/${highlightId}`">#{{ highlightId }}</router-link>（现行房间参数）</p>
</div></template>
