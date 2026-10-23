<template>
  <div v-if="lowStockItems.length" class="low-stock-alert" role="alert">
    <div class="alert-body">
      <strong>{{ t('lowStock.title', { count: lowStockItems.length }) }}</strong>
      <span class="alert-items">
        <span v-for="item in preview" :key="item.id" class="alert-chip">
          {{ item.sku }} · {{ t('lowStock.short', { count: item.reorder_point - item.quantity_on_hand }) }}
        </span>
        <span v-if="lowStockItems.length > preview.length" class="alert-more">
          {{ t('lowStock.more', { count: lowStockItems.length - preview.length }) }}
        </span>
      </span>
    </div>
    <router-link v-if="showLink" :to="{ path: '/inventory', query: { lowStock: '1' } }" class="alert-link">
      {{ t('lowStock.viewAll') }}
    </router-link>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n'

const PREVIEW_COUNT = 4

export default {
  name: 'LowStockAlert',
  props: {
    items: {
      type: Array,
      required: true
    },
    showLink: {
      type: Boolean,
      default: true
    }
  },
  setup(props) {
    const { t } = useI18n()

    // Same threshold as the Inventory "Low Stock" badge and dashboard summary
    const lowStockItems = computed(() =>
      props.items
        .filter(item => item.quantity_on_hand <= item.reorder_point)
        .sort((a, b) => (b.reorder_point - b.quantity_on_hand) - (a.reorder_point - a.quantity_on_hand))
    )

    const preview = computed(() => lowStockItems.value.slice(0, PREVIEW_COUNT))

    return { t, lowStockItems, preview }
  }
}
</script>

<style scoped>
.low-stock-alert {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.875rem 1.125rem;
  margin-bottom: 1.25rem;
  background: var(--danger-soft);
  border: 1px solid var(--danger-border);
  border-left: 4px solid #ef4444;
  border-radius: 8px;
  color: var(--danger-text);
  font-size: 0.875rem;
}

.alert-body {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 0.75rem;
}

.alert-items {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.alert-chip {
  background: var(--surface);
  border: 1px solid var(--danger-border);
  border-radius: 999px;
  padding: 0.125rem 0.625rem;
  font-size: 0.8rem;
  font-variant-numeric: tabular-nums;
}

.alert-more {
  font-size: 0.8rem;
  color: var(--danger-text);
}

.alert-link {
  flex-shrink: 0;
  font-weight: 600;
  color: var(--danger-text);
  text-decoration: underline;
}
</style>
