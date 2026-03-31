<script setup lang="ts">
import { h, ref, reactive, onMounted, computed } from 'vue'
import {
  NCard,
  NDataTable,
  NButton,
  NIcon,
  NInput,
  NSpace,
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
  DownloadOutline,
  EyeOutline,
  RefreshOutline,
} from '@vicons/ionicons5'
import {
  getDocuments,
  deleteDocument,
  reparseDocument,
  getPreviewUrl,
  getDownloadUrl,
  STATUS_MAP,
} from '@/api/document'
import type { DocumentInfo } from '@/api/document'
import type { TagInfo } from '@/api/tag'
import { useAuthStore } from '@/stores/auth'
import { useTagData } from '@/composables/useTagData'
import TagSelect from '../components/TagSelect.vue'
import DocumentFormModal from './DocumentFormModal.vue'
import DocumentPreviewModal from './DocumentPreviewModal.vue'

const message = useMessage()
const dialog = useDialog()
const authStore = useAuthStore()
const { allTags } = useTagData()

const isAdmin = computed(() => authStore.isAdmin)

const keyword = ref('')
const filterTagIds = ref<number[]>([])
const loading = ref(false)
const data = ref<DocumentInfo[]>([])
const pagination = reactive({
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  prefix: ({ itemCount }: { itemCount: number | undefined }) => `共 ${itemCount ?? 0} 条`,
})

const showFormModal = ref(false)
const editData = ref<DocumentInfo | null>(null)

const showPreviewModal = ref(false)
const previewUrl = ref('')
const previewTitle = ref('')

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

function renderStatus(status: number) {
  const info = STATUS_MAP[status]
  if (!info) return h('span', {}, String(status))
  return h(NTag, { size: 'small', type: info.type, round: true }, { default: () => info.label })
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const columns = computed<DataTableColumns<DocumentInfo>>(() => {
  const cols: DataTableColumns<DocumentInfo> = [
    {
      title: '名称',
      key: 'title',
      minWidth: 200,
      ellipsis: { tooltip: true },
    },
    {
      title: '编号',
      key: 'code',
      width: 160,
      ellipsis: { tooltip: true },
      render(row) {
        return row.code || '—'
      },
    },
    {
      title: '发布时间',
      key: 'publishDate',
      width: 120,
      render(row) {
        return row.publishDate || '—'
      },
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render(row) {
        return renderStatus(row.status)
      },
    },
    {
      title: '标签',
      key: 'tags',
      width: 200,
      render(row) {
        return renderTags(row.tags)
      },
    },
    {
      title: '文件',
      key: 'fileName',
      width: 160,
      ellipsis: { tooltip: true },
      render(row) {
        return h('span', {}, [
          row.fileName,
          h(
            'span',
            { style: { color: '#86909c', marginLeft: '4px', fontSize: '12px' } },
            `(${formatFileSize(row.fileSize)})`,
          ),
        ])
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
      width: isAdmin.value ? 400 : 160,
      render(row) {
        const buttons: ReturnType<typeof h>[] = [
          h(
            NButton,
            {
              size: 'small',
              text: true,
              type: 'primary',
              onClick: () => handlePreview(row),
            },
            { default: () => '预览', icon: () => h(NIcon, { component: EyeOutline }) },
          ),
          h(
            NButton,
            {
              size: 'small',
              text: true,
              type: 'default',
              tag: 'a',
              href: getDownloadUrl(row.id),
              target: '_blank',
              style: { marginLeft: '12px' },
            } as any,
            { default: () => '下载', icon: () => h(NIcon, { component: DownloadOutline }) },
          ),
        ]

        if (isAdmin.value) {
          buttons.push(
            h(
              NButton,
              {
                size: 'small',
                text: true,
                type: 'warning',
                disabled: row.status !== -1,
                onClick: () => handleReparse(row),
                style: { marginLeft: '12px' },
              },
              { default: () => '重识别', icon: () => h(NIcon, { component: RefreshOutline }) },
            ),
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
    const res = await getDocuments(
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

function handlePreview(row: DocumentInfo) {
  previewTitle.value = row.title
  previewUrl.value = getPreviewUrl(row.id)
  showPreviewModal.value = true
}

function handleCreate() {
  editData.value = null
  showFormModal.value = true
}

function handleEdit(row: DocumentInfo) {
  editData.value = row
  showFormModal.value = true
}

function handleReparse(row: DocumentInfo) {
  dialog.warning({
    title: '确认重识别',
    content: `确定要重新识别文档「${row.title}」吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const res = await reparseDocument(row.id)
        if (res.code === 200) {
          message.success('已重新提交识别任务')
          fetchData()
        }
      } catch {
        message.error('操作失败')
      }
    },
  })
}

function handleDelete(row: DocumentInfo) {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除文档「${row.title}」吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const res = await deleteDocument(row.id)
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
          placeholder="搜索名称、编号或备注"
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
      :row-key="(row: DocumentInfo) => row.id"
    />

    <DocumentFormModal
      v-model:show="showFormModal"
      :edit-data="editData"
      @saved="fetchData"
    />

    <DocumentPreviewModal
      v-model:show="showPreviewModal"
      :title="previewTitle"
      :url="previewUrl"
    />
  </NCard>
</template>
