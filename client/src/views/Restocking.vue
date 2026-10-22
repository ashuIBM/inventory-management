<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="budget-row">
          <label for="budget-slider" class="budget-label">{{ t('restocking.budget') }}</label>
          <span class="budget-value">{{ money(budget) }}</span>
        </div>
        <input
          id="budget-slider"
          v-model.number="budget"
          type="range"
          class="budget-slider"
          min="0"
          :max="sliderMax"
          :step="BUDGET_STEP"
        />
        <div class="budget-scale">
          <span>{{ money(0) }}</span>
          <span>{{ money(sliderMax) }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.plannedSpend') }}</div>
          <div class="stat-value">{{ money(plan.total_cost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ money(plan.remaining) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.itemsToRestock') }}</div>
          <div class="stat-value">{{ plan.items.length }}</div>
          <div class="stat-sub">{{ t('restocking.ofItems', { count: forecastCount }) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
          <button
            class="place-order-btn"
            :disabled="plan.items.length === 0 || placing || refreshing"
            @click="placeOrder"
          >
            {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="placedOrder" class="notice success">
          {{ t('restocking.orderPlaced', { id: placedOrder.id, days: placedOrder.lead_time_days }) }}
          <router-link to="/orders">{{ t('restocking.viewOrders') }}</router-link>
        </div>
        <div v-if="placeError" class="notice danger">{{ placeError }}</div>

        <div v-if="plan.items.length === 0" class="empty-state">{{ t('restocking.noItems') }}</div>
        <div v-else class="table-container" :class="{ refreshing }">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in plan.items" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ translateProductName(item.item_name) }}</td>
                <td><span :class="['badge', item.trend]">{{ t('trends.' + item.trend) }}</span></td>
                <td class="num">
                  {{ item.quantity.toLocaleString() }}
                  <span v-if="item.partial" class="partial-tag">
                    {{ t('restocking.partial') }} · {{ t('restocking.ofTarget', { count: item.target_quantity.toLocaleString() }) }}
                  </span>
                </td>
                <td class="num">{{ formatCurrencyWithDecimals(item.unit_cost, currentCurrency, 2) }}</td>
                <td class="num">{{ money(item.line_total) }}</td>
                <td class="num">{{ t('restocking.days', { count: item.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const BUDGET_STEP = 500
const DEFAULT_BUDGET = 20000
const DEBOUNCE_MS = 250

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const refreshing = ref(false)
    const placing = ref(false)
    const placeError = ref(null)
    const placedOrder = ref(null)

    const budget = ref(DEFAULT_BUDGET)
    const plan = ref({ budget: 0, max_budget: 0, total_cost: 0, remaining: 0, items: [] })
    const forecastCount = ref(0)

    // Round the max up to a whole step so the slider can always reach "everything fits"
    const sliderMax = computed(() => Math.ceil(plan.value.max_budget / BUDGET_STEP) * BUDGET_STEP)

    const money = (amount) => formatCurrency(amount, currentCurrency.value)

    // Slider drags fire many changes; only the latest response may win, so stale
    // responses that arrive out of order are dropped via a request counter
    let requestId = 0
    const loadPlan = async () => {
      const thisRequest = ++requestId
      try {
        refreshing.value = true
        const result = await api.getRestockRecommendations(budget.value)
        if (thisRequest !== requestId) return
        plan.value = result
        error.value = null
      } catch (err) {
        if (thisRequest !== requestId) return
        error.value = 'Failed to load restock recommendations: ' + err.message
        console.error('Restock load error:', err)
      } finally {
        if (thisRequest === requestId) refreshing.value = false
      }
    }

    let debounceTimer = null
    watch(budget, () => {
      placedOrder.value = null
      placeError.value = null
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadPlan, DEBOUNCE_MS)
    })

    const placeOrder = async () => {
      try {
        placing.value = true
        placeError.value = null
        placedOrder.value = await api.createRestockOrder(budget.value)
      } catch (err) {
        placeError.value = t('restocking.orderFailed') + ': ' + (err.response?.data?.detail || err.message)
        console.error('Restock order error:', err)
      } finally {
        placing.value = false
      }
    }

    onMounted(async () => {
      try {
        const forecasts = await api.getDemandForecasts()
        forecastCount.value = forecasts.length
        await loadPlan()
        // Clamp the default if the data's full-restock cost is below it
        if (budget.value > sliderMax.value) budget.value = sliderMax.value
      } catch (err) {
        error.value = 'Failed to load restock recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    })

    onBeforeUnmount(() => clearTimeout(debounceTimer))

    return {
      t,
      BUDGET_STEP,
      currentCurrency,
      translateProductName,
      formatCurrencyWithDecimals,
      loading,
      error,
      refreshing,
      placing,
      placeError,
      placedOrder,
      budget,
      plan,
      forecastCount,
      sliderMax,
      money,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  padding: 1.5rem;
}

.budget-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.875rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.budget-slider {
  width: 100%;
  accent-color: #3b82f6;
  cursor: pointer;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.375rem;
}

.stat-sub {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.place-order-btn {
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

.place-order-btn:hover:not(:disabled) {
  background: #1e293b;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.notice {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.notice.success {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.notice.success a {
  color: #166534;
  font-weight: 600;
  margin-left: 0.5rem;
}

.notice.danger {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.table-container {
  transition: opacity 0.15s;
}

.table-container.refreshing {
  opacity: 0.6;
}

.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.partial-tag {
  display: block;
  font-size: 0.7rem;
  color: #b45309;
}
</style>
