<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import {
  NModal,
  NForm,
  NFormItem,
  NInput,
  NButton,
  NSpace,
  useMessage,
  type FormInst,
  type FormRules,
} from 'naive-ui'
import { createFragment, updateFragment } from '@/api/fragment'
import type { FragmentInfo } from '@/api/fragment'
import TagSelect from '../components/TagSelect.vue'

const props = defineProps<{
  show: boolean
  editData: FragmentInfo | null
}>()

const emit = defineEmits<{
  (e: 'update:show', val: boolean): void
  (e: 'saved'): void
}>()

const message = useMessage()
const formRef = ref<FormInst | null>(null)
const formSaving = ref(false)

const formModel = reactive({
  title: '',
  content: '',
  tagIds: [] as number[],
})

const formRules: FormRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
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
      formModel.content = props.editData.content
      formModel.tagIds = props.editData.tags?.map((t) => t.id) || []
    } else {
      isEdit.value = false
      editingId.value = null
      formModel.title = ''
      formModel.content = ''
      formModel.tagIds = []
    }
  },
)

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
        emit('update:show', false)
        emit('saved')
      }
    } else {
      const res = await createFragment(params)
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
    :title="isEdit ? '编辑碎片知识' : '新增碎片知识'"
    style="width: 640px"
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
        <TagSelect v-model="formModel.tagIds" placeholder="选择标签（可选）" />
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
