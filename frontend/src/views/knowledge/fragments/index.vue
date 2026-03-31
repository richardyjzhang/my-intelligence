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
  NSelect,
  useMessage,
  useDialog,
  type DataTableColumns,
  type FormInst,
  type FormRules,
  type SelectOption,
} from 'naive-ui'
import {
  SearchOutline,
  AddOutline,
  CreateOutline,
  TrashOutline,
  EyeOutline,
} from '@vicons/ionicons5'
import { getFragments, createFragment, updateFragment, deleteFragment } from '@/api/fragment'
import type { FragmentInfo } from '@/api/fragment'
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
const data = ref<FragmentInfo[]>([])
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
  content: '',
  tagIds: [] as number[],
})
const formSaving = ref(false)

const showDetailModal = ref(false)
const detailData = ref<FragmentInfo | null>(null)

const formRules: FormRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
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
    const res = await getFragments(
      keyword.value || undefined,
      filterTagId.value || undefined,
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

function resetForm() {
  formModel.title = ''
  formModel.content = ''
  formModel.tagIds = []
}

function handleCreate() {
  resetForm()
  isEdit.value = false
  editingId.value = null
  showModal.value = true
}

function handleEdit(row: FragmentInfo) {
  isEdit.value = true
  editingId.value = row.id
  formModel.title = row.title
  formModel.content = row.content
  formModel.tagIds = row.tags?.map((t) => t.id) || []
  showModal.value = true
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

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  formSaving.value = true
  try {
    const params = {
      title: formModel.title,
      content: formModel.content,
      tagIds: formModel.tagIds,
    }
    if (isEdit.value && editingId.value !== null) {
      const res = await updateFragment(editingId.value, params)
      if (res.code === 200) {
        message.success('修改成功')
        showModal.value = false
        fetchData()
      }
    } else {
      const res = await createFragment(params)
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
          placeholder="搜索标题或内容"
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
      :row-key="(row: FragmentInfo) => row.id"
    />

    <!-- 新增 / 编辑弹窗 -->
    <NModal
      v-model:show="showModal"
      preset="card"
      :title="isEdit ? '编辑碎片知识' : '新增碎片知识'"
      style="width: 640px"
      :mask-closable="false"
    >
      <NForm
        ref="formRef"
        :model="formModel"
        :rules="formRules"
        label-placement="left"
        label-width="80"
      >
        <NFormItem label="标题" path="title">
          <NInput v-model:value="formModel.title" placeholder="请输入标题" />
        </NFormItem>
        <NFormItem label="内容" path="content">
          <NInput
            v-model:value="formModel.content"
            type="textarea"
            placeholder="请输入内容"
            :autosize="{ minRows: 4, maxRows: 12 }"
          />
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
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="showModal = false">取消</NButton>
          <NButton type="primary" :loading="formSaving" @click="handleSubmit">确定</NButton>
        </NSpace>
      </template>
    </NModal>

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
