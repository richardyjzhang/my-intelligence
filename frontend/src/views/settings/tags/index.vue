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
  NColorPicker,
  useMessage,
  useDialog,
  type DataTableColumns,
  type FormInst,
  type FormRules,
} from 'naive-ui'
import { SearchOutline, AddOutline, CreateOutline, TrashOutline } from '@vicons/ionicons5'
import { getTags, createTag, updateTag, deleteTag } from '@/api/tag'
import type { TagInfo } from '@/api/tag'
import { useAuthStore } from '@/stores/auth'

const message = useMessage()
const dialog = useDialog()
const authStore = useAuthStore()

const isAdmin = computed(() => authStore.isAdmin)

const keyword = ref('')
const loading = ref(false)
const data = ref<TagInfo[]>([])
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
  name: '',
  color: '#409EFF',
})
const formSaving = ref(false)

const formRules: FormRules = {
  name: [{ required: true, message: '请输入标签名称', trigger: 'blur' }],
  color: [
    { required: true, message: '请选择颜色', trigger: 'blur' },
    {
      pattern: /^#[0-9A-Fa-f]{6}$/,
      message: '请输入有效的十六进制颜色代码',
      trigger: 'blur',
    },
  ],
}

const columns = computed<DataTableColumns<TagInfo>>(() => {
  const cols: DataTableColumns<TagInfo> = [
    {
      title: '标签名称',
      key: 'name',
      width: 200,
      render(row) {
        return h(
          NTag,
          {
            color: { color: row.color + '1A', textColor: row.color, borderColor: row.color },
            size: 'medium',
            round: true,
          },
          { default: () => row.name },
        )
      },
    },
    {
      title: '颜色',
      key: 'color',
      width: 160,
      render(row) {
        return h('span', { style: { display: 'inline-flex', alignItems: 'center', gap: '8px' } }, [
          h('span', {
            style: {
              display: 'block',
              width: '16px',
              height: '16px',
              borderRadius: '3px',
              backgroundColor: row.color,
              flexShrink: '0',
            },
          }),
          h('span', {}, row.color),
        ])
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
  ]

  if (isAdmin.value) {
    cols.push({
      title: '操作',
      key: 'actions',
      width: 160,
      render(row) {
        return h(NSpace, { size: 'small' }, () => [
          h(
            NButton,
            { size: 'small', text: true, type: 'info', onClick: () => handleEdit(row) },
            { default: () => '编辑', icon: () => h(NIcon, { component: CreateOutline }) },
          ),
          h(
            NButton,
            { size: 'small', text: true, type: 'error', onClick: () => handleDelete(row) },
            { default: () => '删除', icon: () => h(NIcon, { component: TrashOutline }) },
          ),
        ])
      },
    })
  }

  return cols
})

async function fetchData() {
  loading.value = true
  try {
    const res = await getTags(keyword.value || undefined)
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
  formModel.name = ''
  formModel.color = '#409EFF'
}

function handleCreate() {
  resetForm()
  isEdit.value = false
  editingId.value = null
  showModal.value = true
}

function handleEdit(row: TagInfo) {
  isEdit.value = true
  editingId.value = row.id
  formModel.name = row.name
  formModel.color = row.color
  showModal.value = true
}

function handleDelete(row: TagInfo) {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除标签「${row.name}」吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const res = await deleteTag(row.id)
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

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  formSaving.value = true
  try {
    const params = { name: formModel.name, color: formModel.color }
    if (isEdit.value && editingId.value !== null) {
      const res = await updateTag(editingId.value, params)
      if (res.code === 200) {
        message.success('修改成功')
        showModal.value = false
        fetchData()
      }
    } else {
      const res = await createTag(params)
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

onMounted(fetchData)
</script>

<template>
  <NCard class="page-card">
    <NSpace justify="space-between" align="center" class="mb-4">
      <NSpace>
        <NInput v-model:value="keyword" placeholder="搜索标签名称" clearable style="width: 240px" @clear="handleSearch" @keydown.enter="handleSearch" />
        <NButton type="primary" @click="handleSearch">
          <template #icon><NIcon :component="SearchOutline" /></template>
          搜索
        </NButton>
      </NSpace>
      <NButton v-if="isAdmin" type="primary" @click="handleCreate">
        <template #icon><NIcon :component="AddOutline" /></template>
        新增
      </NButton>
    </NSpace>

    <NDataTable
      :columns="columns"
      :data="data"
      :loading="loading"
      :pagination="pagination"
      :row-key="(row: TagInfo) => row.id"
    />

    <NModal
      v-model:show="showModal"
      preset="card"
      :title="isEdit ? '编辑标签' : '新增标签'"
      style="width: 460px"
      :mask-closable="false"
    >
      <NForm ref="formRef" :model="formModel" :rules="formRules" label-placement="left" label-width="80">
        <NFormItem label="标签名称" path="name">
          <NInput v-model:value="formModel.name" placeholder="请输入标签名称" />
        </NFormItem>
        <NFormItem label="颜色" path="color">
          <NSpace align="center" :size="12" style="width: 100%">
            <NColorPicker
              v-model:value="formModel.color"
              :show-alpha="false"
              style="width: 180px"
            />
            <NTag
              :color="{ color: formModel.color + '1A', textColor: formModel.color, borderColor: formModel.color }"
              size="medium"
              round
            >
              {{ formModel.name || '预览' }}
            </NTag>
          </NSpace>
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="showModal = false">取消</NButton>
          <NButton type="primary" :loading="formSaving" @click="handleSubmit">确定</NButton>
        </NSpace>
      </template>
    </NModal>
  </NCard>
</template>
