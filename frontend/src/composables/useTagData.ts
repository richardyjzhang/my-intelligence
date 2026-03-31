import { ref } from 'vue'
import { getTags } from '@/api/tag'
import type { TagInfo } from '@/api/tag'
import type { SelectOption } from 'naive-ui'

const allTags = ref<TagInfo[]>([])
const tagOptions = ref<SelectOption[]>([])
const loaded = ref(false)

async function fetchTags() {
  try {
    const res = await getTags()
    if (res.code === 200) {
      allTags.value = res.data
      tagOptions.value = res.data.map((tag) => ({
        label: tag.name,
        value: tag.id,
      }))
      loaded.value = true
    }
  } catch {
    /* ignore */
  }
}

export function useTagData() {
  if (!loaded.value) {
    fetchTags()
  }
  return { allTags, tagOptions, fetchTags }
}
