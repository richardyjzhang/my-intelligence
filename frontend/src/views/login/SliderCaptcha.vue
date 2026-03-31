<script setup lang="ts">
import { ref } from 'vue'

const verified = defineModel<boolean>({ default: false })

const trackEl = ref<HTMLElement | null>(null)
const thumbLeft = ref(0)
const THUMB_SIZE = 36

function getMaxLeft() {
  if (!trackEl.value) return 0
  return trackEl.value.clientWidth - THUMB_SIZE
}

function onPointerDown(e: PointerEvent) {
  if (verified.value) return
  const startX = e.clientX
  const startLeft = thumbLeft.value

  const onMove = (ev: PointerEvent) => {
    const maxLeft = getMaxLeft()
    thumbLeft.value = Math.max(0, Math.min(maxLeft, startLeft + ev.clientX - startX))
  }

  const onUp = () => {
    document.removeEventListener('pointermove', onMove)
    document.removeEventListener('pointerup', onUp)
    const maxLeft = getMaxLeft()
    if (thumbLeft.value >= maxLeft - 2) {
      thumbLeft.value = maxLeft
      verified.value = true
    } else {
      thumbLeft.value = 0
    }
  }

  document.addEventListener('pointermove', onMove)
  document.addEventListener('pointerup', onUp)
}

function reset() {
  verified.value = false
  thumbLeft.value = 0
}

defineExpose({ reset })
</script>

<template>
  <div
    ref="trackEl"
    class="relative w-full h-9 rounded-md overflow-hidden select-none touch-none border"
    :class="verified ? 'border-green-500' : 'border-gray-300'"
    style="background: #eef1f5"
  >
    <div
      class="absolute top-0 left-0 h-full rounded-md"
      :class="verified ? 'bg-green-500/15' : 'bg-[#008eaa]/12'"
      :style="{ width: thumbLeft + THUMB_SIZE + 'px' }"
    />

    <div
      v-if="!verified"
      class="absolute inset-0 flex items-center justify-center text-[13px] text-gray-400 pointer-events-none"
    >
      向右滑动完成验证
    </div>
    <div
      v-else
      class="absolute inset-0 flex items-center justify-center text-[13px] text-green-500 font-medium pointer-events-none"
    >
      验证通过
    </div>

    <div
      class="absolute top-0 w-9 h-9 rounded-md bg-white flex items-center justify-center shadow-sm transition-shadow duration-200"
      :class="verified ? 'text-green-500 cursor-default' : 'text-[#008eaa] cursor-grab active:cursor-grabbing active:shadow-md'"
      :style="{ left: thumbLeft + 'px' }"
      @pointerdown.prevent="onPointerDown"
    >
      <svg v-if="!verified" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
      <svg v-else viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
    </div>
  </div>
</template>
