<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getJSON, postJSON } from '../api'
const items = ref([])
const showVoided = ref(false)
const error = ref('')
const router = useRouter()
const load = async () => {
  const q = showVoided.value ? '?include_voided=1' : ''
  items.value = (await getJSON('/api/history' + q)).items
}
onMounted(load)
const resultOf = (h) => { try { return JSON.parse(h.result_json) } catch { return {} } }
const act = async (fn) => { error.value = ''; try { await fn() } catch (e) { error.value = String(e.message || e) } }
const voidRun = (id) => act(async () => { await postJSON(`/api/history/${id}/void`, {}); await load() })
const remeasure = (id) => act(async () => {
  const r = await postJSON(`/api/history/${id}/remeasure`, {})
  router.push(`/history/${r.run_id}`)
})
</script>
<template>
  <div class="page">
    <h1>估算记录</h1>
    <label><input type="checkbox" v-model="showVoided" @change="load" /> 显示已作废</label>
    <p v-if="error" class="error">{{ error }}</p>
    <table>
      <tr><th>编号</th><th>时间</th><th>房间</th><th>升数</th><th>净面积</th><th>涂布率</th><th>状态</th><th>操作</th></tr>
      <tr v-for="h in items" :key="h.id" :class="{ voided: h.voided }">
        <td><router-link :to="`/history/${h.id}`">#{{ h.id }}</router-link></td>
        <td>{{ h.created_at }}</td>
        <td>{{ h.room_id }}</td>
        <td>{{ resultOf(h).liters }}</td>
        <td>{{ resultOf(h).net_m2 }}</td>
        <td>{{ resultOf(h).coverage }}</td>
        <td><span v-if="h.voided" class="badge">已作废</span><span v-else>有效</span></td>
        <td>
          <button v-if="!h.voided" @click="voidRun(h.id)">作废</button>
          <button @click="remeasure(h.id)">再测</button>
        </td>
      </tr>
    </table>
  </div>
</template>
