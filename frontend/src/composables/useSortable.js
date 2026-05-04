import { computed, ref } from 'vue'

/**
 * Provides sortBy/sortDir state and a sorted computed property.
 *
 * comparators: { [field]: (a, b) => number }
 * If a field has no comparator, falls back to a.localeCompare(b) on string or a - b on number.
 */
export function useSortable(source, comparators = {}) {
  const sortBy = ref(null)
  const sortDir = ref('asc')

  const toggleSort = (field) => {
    if (sortBy.value === field) {
      sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortBy.value = field
      sortDir.value = 'asc'
    }
  }

  const sorted = computed(() => {
    const list = [...source.value]
    if (!sortBy.value) return list
    const dir = sortDir.value === 'asc' ? 1 : -1
    const field = sortBy.value
    const cmp = comparators[field]
    return list.sort((a, b) => {
      if (cmp) return dir * cmp(a, b)
      const av = a[field]
      const bv = b[field]
      if (typeof av === 'string') return dir * av.localeCompare(bv)
      return dir * (Number(av) - Number(bv))
    })
  })

  return { sortBy, sortDir, sorted, toggleSort }
}
