<script setup lang="ts">
import { h, ref, reactive, onMounted, computed } from 'vue'
import {
  NCard,
  NDataTable,
  NButton,
  NIcon,
  NInput,
  NSpace,
  NModal,
  NTag,
  useMessage,
  useDialog,
  type DataTableColumns,
} from 'naive-ui'
import {
  SearchOutline,
  AddOutline,
  CreateOutline,
  TrashOutline,
  EyeOutline,
} from '@vicons/ionicons5'
import { getFragments, deleteFragment } from '@/api/fragment'
import type { FragmentInfo } from '@/api/fragment'
import type { TagInfo } from '@/api/tag'
import { useAuthStore } from '@/stores/auth'
import { useTagData } from '@/composables/useTagData'
import TagSelect from '../components/TagSelect.vue'
import FragmentFormModal from './FragmentFormModal.vue'

const message = useMessage()
const dialog = useDialog()
const authStore = useAuthStore()
useTagData()

const isAdmin = computed(() => authStore.isAdmin)

const keyword = ref('')
const filterTagIds = ref<number[]>([])
const loading = ref(false)
const data = ref<FragmentInfo[]>([])
const pagination = reactive({
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  prefix: ({ itemCount }: { itemCount: number | undefined }) => `共 ${itemCount ?? 0} 条`,
})

const showFormModal = ref(false)
const editData = ref<FragmentInfo | null>(null)

const showDetailModal = ref(false)
const detailData = ref<FragmentInfo | null>(null)

function renderTags(tags: TagInfo[]) {
  if (!tags || tags.length === 0) return h('span', { style: { color: '#c9cdd4' } }, '—')
  return h(NSpace, { size: 4 }, () =>
    tags.map((tag) =>
      h(
        NTag,
        {
          size: 'small',
          round: true,
          color: { color: tag.color + '1A', textColor: tag.color, borderColor: tag.color },
        },
        { default: () => tag.name },
      ),
    ),
  )
}

const columns = computed<DataTableColumns<FragmentInfo>>(() => {
  const cols: DataTableColumns<FragmentInfo> = [
    {
      title: '标题',
      key: 'title',
      minWidth: 200,
      ellipsis: { tooltip: true },
    },
    {
      title: '内容',
      key: 'content',
      minWidth: 300,
      ellipsis: { tooltip: true },
    },
    {
      title: '标签',
      key: 'tags',
      width: 240,
      render(row) {
        return renderTags(row.tags)
      },
    },
    {
      title: '创建人',
      key: 'creator',
      width: 100,
      render(row) {
        return row.creator?.nickname || '—'
      },
    },
    {
      title: '创建时间',
      key: 'createTime',
      width: 180,
      render(row) {
        return row.createTime ? row.createTime.replace('T', ' ') : ''
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: isAdmin.value ? 260 : 100,
      render(row) {
        const buttons = [
          h(
            NButton,
            { size: 'small', text: true, type: 'primary', onClick: () => handleDetail(row) },
            { default: () => '查看', icon: () => h(NIcon, { component: EyeOutline }) },
          ),
        ]

        if (isAdmin.value) {
          buttons.push(
            h(
              NButton,
              {
                size: 'small',
                text: true,
                type: 'info',
                onClick: () => handleEdit(row),
                style: { marginLeft: '12px' },
              },
              { default: () => '编辑', icon: () => h(NIcon, { component: CreateOutline }) },
            ),
            h(
              NButton,
              {
                size: 'small',
                text: true,
                type: 'error',
                onClick: () => handleDelete(row),
                style: { marginLeft: '12px' },
              },
              { default: () => '删除', icon: () => h(NIcon, { component: TrashOutline }) },
            ),
          )
        }

        return h(NSpace, { size: 0 }, () => buttons)
      },
    },
  ]

  return cols
})

async function fetchData() {
  loading.value = true
  try {
    const res = await getFragments(
      keyword.value || undefined,
      filterTagIds.value.length > 0 ? filterTagIds.value : undefined,
    )
    if (res.code === 200) {
      data.value = res.data
    }
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  fetchData()
}

function handleCreate() {
  editData.value = null
  showFormModal.value = true
}

function handleEdit(row: FragmentInfo) {
  editData.value = row
  showFormModal.value = true
}

function handleDetail(row: FragmentInfo) {
  detailData.value = row
  showDetailModal.value = true
}

function handleDelete(row: FragmentInfo) {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除碎片知识「${row.title}」吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const res = await deleteFragment(row.id)
        if (res.code === 200) {
          message.success('删除成功')
          fetchData()
        }
      } catch {
        message.error('删除失败')
      }
    },
  })
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <NCard class="page-card">
    <NSpace justify="space-between" align="center" class="mb-4">
      <NSpace>
        <NInput
          v-model:value="keyword"
          placeholder="搜索标题或内容"
          clearable
          style="width: 240px"
          @clear="handleSearch"
          @keydown.enter="handleSearch"
        />
        <TagSelect
          v-model="filterTagIds"
          placeholder="按标签筛选"
          style="min-width: 180px; max-width: 600px"
          @update:value="handleSearch"
        />
        <NButton type="primary" @click="handleSearch">
          <template #icon><NIcon :component="SearchOutline" /></template>
          搜索
        </NButton>
      </NSpace>
      <NButton type="primary" @click="handleCreate">
        <template #icon><NIcon :component="AddOutline" /></template>
        新增
      </NButton>
    </NSpace>

    <NDataTable
      :columns="columns"
      :data="data"
      :loading="loading"
      :pagination="pagination"
      :row-key="(row: FragmentInfo) => row.id"
    />

    <FragmentFormModal
      v-model:show="showFormModal"
      :edit-data="editData"
      @saved="fetchData"
    />

    <!-- 详情弹窗 -->
    <NModal
      v-model:show="showDetailModal"
      preset="card"
      title="碎片知识详情"
      style="width: 640px"
    >
      <template v-if="detailData">
        <div style="margin-bottom: 16px">
          <div style="font-size: 18px; font-weight: 600; margin-bottom: 12px">
            {{ detailData.title }}
          </div>
          <NSpace size="small" style="margin-bottom: 12px">
            <NTag
              v-for="tag in detailData.tags"
              :key="tag.id"
              size="small"
              round
              :color="{
                color: tag.color + '1A',
                textColor: tag.color,
                borderColor: tag.color,
              }"
            >
              {{ tag.name }}
            </NTag>
          </NSpace>
          <div
            style="
              white-space: pre-wrap;
              line-height: 1.8;
              color: #4e5969;
              background: #f7f8fa;
              padding: 16px;
              border-radius: 8px;
            "
          >
            {{ detailData.content }}
          </div>
          <div style="margin-top: 16px; font-size: 13px; color: #86909c">
            <span>创建人：{{ detailData.creator?.nickname }}</span>
            <span style="margin-left: 24px">
              创建时间：{{ detailData.createTime?.replace('T', ' ') }}
            </span>
          </div>
        </div>
      </template>
    </NModal>
  </NCard>
</template>
