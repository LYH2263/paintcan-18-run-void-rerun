<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getJSON, postJSON } from '../api'

const route = useRoute()
const router = useRouter()
const run = ref(null)
const notFound = ref(false)
const error = ref('')

const resultOf = (r) => {
  try { return JSON.parse(r.result_json) } catch { return {} }
}
const inputOf = (r) => {
  try { return JSON.parse(r.input_json) } catch { return {} }
}
const load = async () => {
  notFound.value = false; error.value = ''
  try { run.value = await getJSON(`/api/history/${route.params.id}`) }
  catch { run.value = null; notFound.value = true }
}
const voidRun = async () => {
  if (!confirm(`确认将 #${run.value.id} 标记作废？数值不会被改写。`)) return
  try { await postJSON(`/api/runs/${run.value.id}/void`, {}); await load() }
  catch (e) { error.value = `作废失败：${e.message}` }
}
const remeasure = async () => {
  const roomId = inputOf(run.value).room_id
  if (roomId == null) { error.value = '该记录缺少房间参数，无法再测'; return }
  const r = await postJSON('/api/estimate', { room_id: roomId, persist: true, supersedes_id: run.value.id })
  router.push(`/history/${r.run_id}?fresh=1`)
}
onMounted(load)
watch(() => route.params.id, load)
</script>
<template><div class="page">
  <h1>记录 #{{ route.params.id }} <span v-if="run?.voided" class="tag">已作废</span><span v-else-if="run" class="tag tag-ok">有效</span></h1>
  <p v-if="notFound" class="error">找不到该编号的记录。</p>
  <p v-if="error" class="error">{{ error }}</p>
  <template v-if="run">
    <p>时间 {{ run.created_at }}<span v-if="run.voided_at"> · 作废于 {{ run.voided_at }}</span></p>
    <p>房间 ID {{ inputOf(run).room_id }}<template v-if="inputOf(run).coats != null"> · {{ inputOf(run).coats }} 遍</template></p>
    <ul class="pinned">
      <li>钉选升数 <span class="hero-num">{{ resultOf(run).liters }}</span> L</li>
      <li>钉选净面积 <span class="hero-num">{{ resultOf(run).net_m2 }}</span> m²</li>
      <li>钉选涂布率 <span class="hero-num">{{ resultOf(run).coverage }}</span> m²/L</li>
    </ul>
    <p v-if="run.supersedes_id">前序编号 <router-link :to="`/history/${run.supersedes_id}`">#{{ run.supersedes_id }}</router-link></p>
    <div class="actions">
      <button v-if="!run.voided" @click="voidRun">作废</button>
      <button @click="remeasure">再测（按现行房间参数写新条）</button>
      <router-link to="/history">返回列表</router-link>
    </div>
  </template>
</div></template>
