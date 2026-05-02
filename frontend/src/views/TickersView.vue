<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold tracking-tight">Mapeamento de Tickers</h1>
      <p class="text-muted-foreground text-sm mt-1">
        Confirme ou corrija tickers não reconhecidos. Use também para mapear renomeações (ex: EMBR3 → EMBJ3).
      </p>
    </div>

    <!-- Add manual alias -->
    <Card class="p-4">
      <p class="text-sm font-medium mb-3">Adicionar mapeamento manual</p>
      <div class="flex gap-2 items-end">
        <div class="flex-1">
          <label class="text-xs text-muted-foreground block mb-1">Nome / ticker antigo</label>
          <input
            v-model="newRaw"
            type="text"
            placeholder="Ex: EMBR3 ou AMBEV S/A ON"
            class="h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
        <div class="w-32">
          <label class="text-xs text-muted-foreground block mb-1">Ticker atual</label>
          <input
            v-model="newTicker"
            type="text"
            placeholder="Ex: EMBJ3"
            class="h-9 w-full rounded-md border border-input bg-background px-3 text-sm font-mono uppercase shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
            @input="newTicker = newTicker.toUpperCase()"
          />
        </div>
        <Button :disabled="!newRaw.trim() || !newTicker.trim() || saving" @click="createAlias" class="shrink-0">
          Adicionar
        </Button>
      </div>
      <p v-if="createError" class="text-xs text-red-500 mt-1">{{ createError }}</p>
    </Card>

    <!-- Pending confirmation -->
    <div v-if="pending.length">
      <div class="flex items-center gap-2 mb-3">
        <AlertTriangle class="h-4 w-4 text-amber-500" />
        <h2 class="font-semibold text-sm">Aguardando confirmação ({{ pending.length }})</h2>
      </div>
      <div class="space-y-2">
        <Card
          v-for="alias in pending"
          :key="alias.raw_name"
          class="flex items-center gap-3 px-4 py-3"
        >
          <div class="flex-1 min-w-0">
            <p class="text-xs text-muted-foreground">Nome extraído da nota</p>
            <p class="font-mono text-sm font-medium truncate">{{ alias.raw_name }}</p>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <input
              v-model="editValues[alias.raw_name]"
              type="text"
              placeholder="Ticker B3"
              class="h-8 w-28 rounded-md border border-input bg-background px-2 text-sm font-mono uppercase shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
              @input="editValues[alias.raw_name] = editValues[alias.raw_name].toUpperCase()"
              @keyup.enter="confirmAlias(alias.raw_name)"
            />
            <Button
              size="sm"
              :disabled="!editValues[alias.raw_name]?.trim() || confirming[alias.raw_name]"
              @click="confirmAlias(alias.raw_name)"
            >
              <Check class="h-3.5 w-3.5 mr-1" />
              Confirmar
            </Button>
            <button
              type="button"
              class="p-1 rounded text-muted-foreground hover:text-destructive transition-colors"
              @click="remove(alias.raw_name)"
            >
              <Trash2 class="h-4 w-4" />
            </button>
          </div>
        </Card>
      </div>
    </div>

    <!-- Confirmed aliases -->
    <div>
      <div class="flex items-center gap-2 mb-3">
        <CheckCircle class="h-4 w-4 text-emerald-500" />
        <h2 class="font-semibold text-sm">Mapeamentos confirmados ({{ confirmed.length }})</h2>
      </div>
      <Card class="overflow-hidden">
        <div v-if="!confirmed.length" class="px-4 py-8 text-center text-sm text-muted-foreground">
          Nenhum mapeamento confirmado ainda.
        </div>
        <table v-else class="w-full text-sm">
          <thead>
            <tr class="border-b bg-muted/40">
              <th class="px-4 py-2 text-left font-medium text-muted-foreground">Nome / ticker antigo</th>
              <th class="px-4 py-2 text-left font-medium text-muted-foreground">Ticker atual</th>
              <th class="px-4 py-2 text-left font-medium text-muted-foreground">Atualizado</th>
              <th class="px-4 py-2 w-24"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="alias in confirmed"
              :key="alias.raw_name"
              class="border-b last:border-0 hover:bg-muted/20"
            >
              <td class="px-4 py-2 font-mono text-xs text-muted-foreground">{{ alias.raw_name }}</td>
              <td class="px-4 py-2">
                <template v-if="editing === alias.raw_name">
                  <input
                    v-model="editValues[alias.raw_name]"
                    type="text"
                    class="h-7 w-24 rounded-md border border-input bg-background px-2 text-sm font-mono uppercase shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                    @input="editValues[alias.raw_name] = editValues[alias.raw_name].toUpperCase()"
                    @keyup.enter="confirmAlias(alias.raw_name)"
                    @keyup.escape="editing = null"
                    autofocus
                  />
                </template>
                <span v-else class="font-mono font-semibold">{{ alias.ticker }}</span>
              </td>
              <td class="px-4 py-2 text-xs text-muted-foreground tabular-nums">{{ formatDate(alias.updated_at) }}</td>
              <td class="px-4 py-2">
                <div class="flex items-center gap-1 justify-end">
                  <template v-if="editing === alias.raw_name">
                    <Button size="sm" variant="ghost" @click="confirmAlias(alias.raw_name)">
                      <Check class="h-3.5 w-3.5" />
                    </Button>
                    <button type="button" class="p-1 text-muted-foreground hover:text-foreground" @click="editing = null">
                      <X class="h-3.5 w-3.5" />
                    </button>
                  </template>
                  <template v-else>
                    <button
                      type="button"
                      class="p-1 rounded text-muted-foreground hover:text-foreground transition-colors"
                      @click="startEdit(alias)"
                    >
                      <Pencil class="h-3.5 w-3.5" />
                    </button>
                    <button
                      type="button"
                      class="p-1 rounded text-muted-foreground hover:text-destructive transition-colors"
                      @click="remove(alias.raw_name)"
                    >
                      <Trash2 class="h-3.5 w-3.5" />
                    </button>
                  </template>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { formatDate } from '@/utils/format.js'
import { createTickerAlias, deleteTickerAlias, getTickerAliases, updateTickerAlias } from '@/services/api.js'
import { AlertTriangle, Check, CheckCircle, Pencil, Trash2, X } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'

const aliases = ref([])
const editValues = reactive({})
const confirming = reactive({})
const editing = ref(null)
const saving = ref(false)
const createError = ref('')
const newRaw = ref('')
const newTicker = ref('')

const pending = computed(() => aliases.value.filter(a => !a.confirmed))
const confirmed = computed(() => aliases.value.filter(a => a.confirmed))

const load = async () => {
  aliases.value = await getTickerAliases()
  for (const a of aliases.value) {
    if (!a.confirmed) {
      editValues[a.raw_name] = editValues[a.raw_name] ?? (a.ticker ?? '')
    }
  }
}

const confirmAlias = async (rawName) => {
  const ticker = (editValues[rawName] ?? '').trim().toUpperCase()
  if (!ticker) return
  confirming[rawName] = true
  try {
    await updateTickerAlias(rawName, { ticker })
    editing.value = null
    await load()
  } catch (e) {
    alert(e.message)
  } finally {
    confirming[rawName] = false
  }
}

const remove = async (rawName) => {
  if (!window.confirm(`Remover mapeamento "${rawName}"?`)) return
  await deleteTickerAlias(rawName)
  await load()
}

const startEdit = (alias) => {
  editing.value = alias.raw_name
  editValues[alias.raw_name] = alias.ticker ?? ''
}

const createAlias = async () => {
  createError.value = ''
  saving.value = true
  try {
    await createTickerAlias({ raw_name: newRaw.value.trim(), ticker: newTicker.value.trim() })
    newRaw.value = ''
    newTicker.value = ''
    await load()
  } catch (e) {
    createError.value = e.message
  } finally {
    saving.value = false
  }
}


onMounted(load)
</script>
