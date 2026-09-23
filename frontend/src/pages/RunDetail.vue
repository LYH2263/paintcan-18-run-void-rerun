<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getJSON, postJSON } from '../api'
const route = useRoute()
const router = useRouter()
const run = ref(null)
const error = ref('')
const load = async () => {
  error.value = ''
  try { run.value = await getJSON('/api/history/' + route.params.id) }
  catch { run.value = null; error.value = '记录不存在' }
}
onMounted(load)
watch(() => route.params.id, load)
const act = async (fn) => { error.value = ''; try { await fn() } catch (e) { error.value = String(e.message || e) } }
const voidRun = () => act(async () => { await postJSON(`/api/history/${run.value.id}/void`, {}); await load() })
const remeasure = () => act(async () => {
  const r = await postJSON(`/api/history/${run.value.id}/remeasure`, {})
  router.push(`/history/${r.run_id}`)
})
</script>
<template>
  <div class="page">
    <p v-if="error" class="error">{{ error }}</p>
    <template v-if="run">
      <h1>估算 #{{ run.id }} <span v-if="run.voided" class="badge">已作废</span></h1>
      <p>时间 {{ run.created_at }} · 房间 {{ run.room_id }}<span v-if="run.voided_at"> · 作废于 {{ run.voided_at }}</span></p>
      <p v-if="run.supersedes_id">再测自 <router-link :to="`/history/${run.supersedes_id}`">#{{ run.supersedes_id }}</router-link></p>
      <p><span class="hero-num">{{ run.result.liters }}</span> 升 · 净 {{ run.result.net_m2 }} m² · 涂布率 {{ run.result.coverage }} m²/L · {{ run.result.coats }} 遍</p>
      <p>毛面积 {{ run.result.gross_m2 }} m² · 洞口 {{ run.result.openings_m2 }} m²</p>
      <p>
        <button v-if="!run.voided" @click="voidRun">作废</button>
        <button @click="remeasure">再测</button>
        <router-link to="/history">返回记录</router-link>
      </p>
    </template>
  </div>
</template>
