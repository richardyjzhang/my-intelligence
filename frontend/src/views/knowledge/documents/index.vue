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
  NForm,
  NFormItem,
  NTag,
  NDatePicker,
  NSelect,
  NUpload,
  useMessage,
  useDialog,
  type DataTableColumns,
  type FormInst,
  type FormRules,
  type SelectOption,
  type UploadFileInfo,
} from 'naive-ui'
import {
  SearchOutline,
  AddOutline,
  CreateOutline,
  TrashOutline,
  DownloadOutline,
  EyeOutline,
} from '@vicons/ionicons5'
import {
  getDocuments,
  createDocument,
  updateDocument,
  deleteDocument,
  getPreviewUrl,
  getDownloadUrl,
  STATUS_MAP,
} from '@/api/document'
import type { DocumentInfo } from '@/api/document'
import { getTags } from '@/api/tag'
import type { TagInfo } from '@/api/tag'
import { useAuthStore } from '@/stores/auth'

const message = useMessage()
const dialog = useDialog()
const authStore = useAuthStore()

const isAdmin = computed(() => authStore.isAdmin)

const keyword = ref('')
const filterTagId = ref<number | null>(null)
const loading = ref(false)
const data = ref<DocumentInfo[]>([])
const tagOptions = ref<SelectOption[]>([])
const allTags = ref<TagInfo[]>([])
const pagination = reactive({
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  prefix: ({ itemCount }: { itemCount: number | undefined }) => `共 ${itemCount ?? 0} 条`,
})

const showModal = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInst | null>(null)
const formModel = reactive({
  title: '',
  code: '',
  publishDate: null as number | null,
  url: '',
  remark: '',
  tagIds: [] as number[],
})
const fileList = ref<UploadFileInfo[]>([])
const formSaving = ref(false)

const showPreviewModal = ref(false)
const previewUrl = ref('')
const previewTitle = ref('')

const formRules: FormRules = {
  title: [{ required: true, message: '请输入名称', trigger: 'blur' }],
}

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
      width: isAdmin.value ? 320 : 160,
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

async function fetchTags() {
  try {
    const res = await getTags()
    if (res.code === 200) {
      allTags.value = res.data
      tagOptions.value = res.data.map((tag) => ({
        label: tag.name,
        value: tag.id,
      }))
    }
  } catch {
    /* ignore */
  }
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getDocuments(keyword.value || undefined, filterTagId.value || undefined)
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

function resetForm() {
  formModel.title = ''
  formModel.code = ''
  formModel.publishDate = null
  formModel.url = ''
  formModel.remark = ''
  formModel.tagIds = []
  fileList.value = []
}

function handleFileChange(files: UploadFileInfo[]) {
  const first = files[0]
  if (first && !formModel.title) {
    formModel.title = first.name.replace(/\.[^.]+$/, '')
  }
}

function handlePreview(row: DocumentInfo) {
  previewTitle.value = row.title
  previewUrl.value = getPreviewUrl(row.id)
  showPreviewModal.value = true
}

function handleCreate() {
  resetForm()
  isEdit.value = false
  editingId.value = null
  showModal.value = true
}

function handleEdit(row: DocumentInfo) {
  isEdit.value = true
  editingId.value = row.id
  formModel.title = row.title
  formModel.code = row.code || ''
  formModel.publishDate = row.publishDate ? new Date(row.publishDate).getTime() : null
  formModel.url = row.url || ''
  formModel.remark = row.remark || ''
  formModel.tagIds = row.tags?.map((t) => t.id) || []
  showModal.value = true
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

function buildFormData(includeFile: boolean): FormData {
  const fd = new FormData()
  fd.append('title', formModel.title)
  if (formModel.code) fd.append('code', formModel.code)
  if (formModel.publishDate) {
    const d = new Date(formModel.publishDate)
    const dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    fd.append('publishDate', dateStr)
  }
  if (formModel.url) fd.append('url', formModel.url)
  if (formModel.remark) fd.append('remark', formModel.remark)
  formModel.tagIds.forEach((id) => fd.append('tagIds', String(id)))

  if (includeFile) {
    const firstFile = fileList.value[0]
    if (firstFile?.file) {
      fd.append('file', firstFile.file)
    }
  }

  return fd
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  if (!isEdit.value && fileList.value.length === 0) {
    message.warning('请选择PDF文件')
    return
  }

  formSaving.value = true
  try {
    if (isEdit.value && editingId.value !== null) {
      const fd = buildFormData(false)
      const res = await updateDocument(editingId.value, fd)
      if (res.code === 200) {
        message.success('修改成功')
        showModal.value = false
        fetchData()
      }
    } else {
      const fd = buildFormData(true)
      const res = await createDocument(fd)
      if (res.code === 200) {
        message.success('创建成功')
        showModal.value = false
        fetchData()
      }
    }
  } catch {
    message.error(isEdit.value ? '修改失败' : '创建失败')
  } finally {
    formSaving.value = false
  }
}

onMounted(() => {
  fetchTags()
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
        <NSelect
          v-model:value="filterTagId"
          :options="tagOptions"
          placeholder="按标签筛选"
          clearable
          style="width: 180px"
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

    <!-- 新增 / 编辑弹窗 -->
    <NModal
      v-model:show="showModal"
      preset="card"
      :title="isEdit ? '编辑文档' : '新增文档'"
      style="width: 680px"
      :mask-closable="false"
    >
      <NForm
        ref="formRef"
        :model="formModel"
        :rules="formRules"
        label-placement="left"
        label-width="80"
      >
        <NFormItem label="名称" path="title">
          <NInput v-model:value="formModel.title" placeholder="请输入名称" />
        </NFormItem>
        <NFormItem label="编号" path="code">
          <NInput v-model:value="formModel.code" placeholder="请输入编号（可选）" />
        </NFormItem>
        <NFormItem label="发布时间" path="publishDate">
          <NDatePicker
            v-model:value="formModel.publishDate"
            type="date"
            placeholder="选择发布时间"
            clearable
            style="width: 100%"
          />
        </NFormItem>
        <NFormItem label="在线地址" path="url">
          <NInput v-model:value="formModel.url" placeholder="请输入在线文档地址（可选）" />
        </NFormItem>
        <NFormItem label="标签" path="tagIds">
          <NSelect
            v-model:value="formModel.tagIds"
            :options="tagOptions"
            multiple
            placeholder="选择标签（可选）"
            :render-tag="({ option, handleClose }: any) => {
              const tag = allTags.find((t) => t.id === option.value)
              return h(
                NTag,
                {
                  closable: true,
                  onClose: handleClose,
                  size: 'tiny',
                  round: true,
                  color: tag
                    ? { color: tag.color + '1A', textColor: tag.color, borderColor: tag.color }
                    : undefined,
                },
                { default: () => option.label },
              )
            }"
            :render-label="(option: any) => {
              const tag = allTags.find((t) => t.id === option.value)
              return h(
                NTag,
                {
                  size: 'small',
                  round: true,
                  color: tag
                    ? { color: tag.color + '1A', textColor: tag.color, borderColor: tag.color }
                    : undefined,
                },
                { default: () => option.label },
              )
            }"
          />
        </NFormItem>
        <NFormItem label="备注" path="remark">
          <NInput
            v-model:value="formModel.remark"
            type="textarea"
            placeholder="请输入备注（可选）"
            :autosize="{ minRows: 2, maxRows: 6 }"
          />
        </NFormItem>
        <NFormItem v-if="!isEdit" label="PDF文件" path="file">
          <NUpload
            v-model:file-list="fileList"
            accept=".pdf"
            :max="1"
            :default-upload="false"
            @update:file-list="handleFileChange"
          >
            <NButton>选择PDF文件</NButton>
          </NUpload>
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="showModal = false">取消</NButton>
          <NButton type="primary" :loading="formSaving" @click="handleSubmit">确定</NButton>
        </NSpace>
      </template>
    </NModal>

    <!-- PDF 预览弹窗 -->
    <NModal
      v-model:show="showPreviewModal"
      preset="card"
      :title="previewTitle"
      style="width: 90vw; height: 90vh"
    >
      <iframe
        :src="previewUrl"
        style="width: 100%; height: calc(90vh - 120px); border: none; border-radius: 4px"
      />
    </NModal>
  </NCard>
</template>
