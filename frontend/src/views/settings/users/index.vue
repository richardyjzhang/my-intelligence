<script setup lang="ts">
import { h, ref, reactive, onMounted } from 'vue'
import {
  NCard,
  NDataTable,
  NButton,
  NInput,
  NSpace,
  NModal,
  NForm,
  NFormItem,
  NSwitch,
  NTag,
  useMessage,
  useDialog,
  type DataTableColumns,
  type FormInst,
  type FormRules,
} from 'naive-ui'
import { getUsers, createUser, updateUser, deleteUser } from '@/api/user'
import type { UserInfo } from '@/api/auth'
import { hashPassword } from '@/utils/crypto'

const message = useMessage()
const dialog = useDialog()

const keyword = ref('')
const loading = ref(false)
const data = ref<UserInfo[]>([])
const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  prefix: ({ itemCount }: { itemCount: number }) => `共 ${itemCount} 条`,
})

const showModal = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInst | null>(null)
const formModel = reactive({
  username: '',
  nickname: '',
  phone: '',
  email: '',
  password: '',
  admin: false,
})
const formSaving = ref(false)

const createRules: FormRules = {
  username: [{ required: true, message: '请输入登录名', trigger: 'blur' }],
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
}

const editRules: FormRules = {
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  password: [{ min: 6, message: '密码至少6位', trigger: 'blur' }],
}

const columns: DataTableColumns<UserInfo> = [
  { title: '登录名', key: 'username', width: 120 },
  { title: '昵称', key: 'nickname', width: 120 },
  { title: '手机号', key: 'phone', width: 140 },
  { title: '邮箱', key: 'email', width: 200 },
  {
    title: '管理员',
    key: 'admin',
    width: 80,
    render(row) {
      return h(NTag, { type: row.admin ? 'success' : 'default', size: 'small' }, { default: () => (row.admin ? '是' : '否') })
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
    width: 140,
    render(row) {
      return h(NSpace, { size: 'small' }, () => [
        h(NButton, { size: 'small', quaternary: true, type: 'info', onClick: () => handleEdit(row) }, { default: () => '编辑' }),
        h(NButton, { size: 'small', quaternary: true, type: 'error', onClick: () => handleDelete(row) }, { default: () => '删除' }),
      ])
    },
  },
]

async function fetchData() {
  loading.value = true
  try {
    const res = await getUsers({
      keyword: keyword.value || undefined,
      page: pagination.page - 1,
      size: pagination.pageSize,
    })
    if (res.code === 200) {
      data.value = res.data.content
      pagination.itemCount = res.data.totalElements
    }
  } finally {
    loading.value = false
  }
}

function handlePageChange(page: number) {
  pagination.page = page
  fetchData()
}

function handlePageSizeChange(pageSize: number) {
  pagination.pageSize = pageSize
  pagination.page = 1
  fetchData()
}

function handleSearch() {
  pagination.page = 1
  fetchData()
}

function resetForm() {
  formModel.username = ''
  formModel.nickname = ''
  formModel.phone = ''
  formModel.email = ''
  formModel.password = ''
  formModel.admin = false
}

function handleCreate() {
  resetForm()
  isEdit.value = false
  editingId.value = null
  showModal.value = true
}

function handleEdit(row: UserInfo) {
  isEdit.value = true
  editingId.value = row.id
  formModel.username = row.username
  formModel.nickname = row.nickname
  formModel.phone = row.phone || ''
  formModel.email = row.email || ''
  formModel.password = ''
  formModel.admin = row.admin
  showModal.value = true
}

function handleDelete(row: UserInfo) {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除用户「${row.nickname}」吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const res = await deleteUser(row.id)
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
    if (isEdit.value && editingId.value !== null) {
      let hashedPwd: string | undefined
      if (formModel.password) {
        hashedPwd = await hashPassword(formModel.username, formModel.password)
      }
      const res = await updateUser(editingId.value, {
        nickname: formModel.nickname,
        phone: formModel.phone || undefined,
        email: formModel.email || undefined,
        password: hashedPwd,
        admin: formModel.admin,
      })
      if (res.code === 200) {
        message.success('修改成功')
        showModal.value = false
        fetchData()
      }
    } else {
      const hashedPwd = await hashPassword(formModel.username, formModel.password)
      const res = await createUser({
        username: formModel.username,
        nickname: formModel.nickname,
        phone: formModel.phone || undefined,
        email: formModel.email || undefined,
        password: hashedPwd,
        admin: formModel.admin,
      })
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
        <NInput v-model:value="keyword" placeholder="搜索用户名/昵称" clearable style="width: 240px" @clear="handleSearch" @keydown.enter="handleSearch" />
        <NButton type="primary" @click="handleSearch">搜索</NButton>
      </NSpace>
      <NButton type="primary" @click="handleCreate">新增用户</NButton>
    </NSpace>

    <NDataTable
      :columns="columns"
      :data="data"
      :loading="loading"
      :pagination="pagination"
      :remote="true"
      :row-key="(row: UserInfo) => row.id"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
    />

    <NModal
      v-model:show="showModal"
      preset="card"
      :title="isEdit ? '编辑用户' : '新增用户'"
      style="width: 500px"
      :mask-closable="false"
    >
      <NForm ref="formRef" :model="formModel" :rules="isEdit ? editRules : createRules" label-placement="left" label-width="80">
        <NFormItem label="登录名" path="username">
          <NInput v-model:value="formModel.username" :disabled="isEdit" placeholder="请输入登录名" />
        </NFormItem>
        <NFormItem label="昵称" path="nickname">
          <NInput v-model:value="formModel.nickname" placeholder="请输入昵称" />
        </NFormItem>
        <NFormItem label="手机号" path="phone">
          <NInput v-model:value="formModel.phone" placeholder="请输入手机号（可选）" />
        </NFormItem>
        <NFormItem label="邮箱" path="email">
          <NInput v-model:value="formModel.email" placeholder="请输入邮箱（可选）" />
        </NFormItem>
        <NFormItem label="密码" path="password">
          <NInput
            v-model:value="formModel.password"
            type="password"
            show-password-on="click"
            :placeholder="isEdit ? '留空则不修改密码' : '请输入密码'"
          />
        </NFormItem>
        <NFormItem label="管理员" path="admin">
          <NSwitch v-model:value="formModel.admin" />
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
