<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import {
  NModal,
  NForm,
  NFormItem,
  NInput,
  NDatePicker,
  NUpload,
  NButton,
  NSpace,
  useMessage,
  type FormInst,
  type FormRules,
  type UploadFileInfo,
} from 'naive-ui'
import { createDocument, updateDocument } from '@/api/document'
import type { DocumentInfo } from '@/api/document'
import TagSelect from '../components/TagSelect.vue'

const props = defineProps<{
  show: boolean
  editData: DocumentInfo | null
}>()

const emit = defineEmits<{
  (e: 'update:show', val: boolean): void
  (e: 'saved'): void
}>()

const message = useMessage()
const formRef = ref<FormInst | null>(null)
const formSaving = ref(false)
const fileList = ref<UploadFileInfo[]>([])

const formModel = reactive({
  title: '',
  code: '',
  publishDate: null as number | null,
  url: '',
  remark: '',
  tagIds: [] as number[],
})

const formRules: FormRules = {
  title: [{ required: true, message: '请输入名称', trigger: 'blur' }],
}

const isEdit = ref(false)
const editingId = ref<number | null>(null)

watch(
  () => props.show,
  (val) => {
    if (!val) return
    if (props.editData) {
      isEdit.value = true
      editingId.value = props.editData.id
      formModel.title = props.editData.title
      formModel.code = props.editData.code || ''
      formModel.publishDate = props.editData.publishDate
        ? new Date(props.editData.publishDate).getTime()
        : null
      formModel.url = props.editData.url || ''
      formModel.remark = props.editData.remark || ''
      formModel.tagIds = props.editData.tags?.map((t) => t.id) || []
    } else {
      isEdit.value = false
      editingId.value = null
      formModel.title = ''
      formModel.code = ''
      formModel.publishDate = null
      formModel.url = ''
      formModel.remark = ''
      formModel.tagIds = []
      fileList.value = []
    }
  },
)

function handleFileChange(files: UploadFileInfo[]) {
  const first = files[0]
  if (first && !formModel.title) {
    formModel.title = first.name.replace(/\.[^.]+$/, '')
  }
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
        emit('update:show', false)
        emit('saved')
      }
    } else {
      const fd = buildFormData(true)
      const res = await createDocument(fd)
      if (res.code === 200) {
        message.success('创建成功')
        emit('update:show', false)
        emit('saved')
      }
    }
  } catch {
    message.error(isEdit.value ? '修改失败' : '创建失败')
  } finally {
    formSaving.value = false
  }
}
</script>

<template>
  <NModal
    :show="show"
    preset="card"
    :title="isEdit ? '编辑文档' : '新增文档'"
    style="width: 680px"
    :mask-closable="false"
    @update:show="emit('update:show', $event)"
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
        <TagSelect v-model="formModel.tagIds" placeholder="选择标签（可选）" />
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
        <NButton @click="emit('update:show', false)">取消</NButton>
        <NButton type="primary" :loading="formSaving" @click="handleSubmit">确定</NButton>
      </NSpace>
    </template>
  </NModal>
</template>
