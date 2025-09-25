<template>
  <teleport to="body">
    <transition name="sheet-fade">
      <div v-if="modelValue" class="ms-overlay" @click="onMask">
        <transition name="sheet-slide">
          <div class="ms-container" :style="sheetStyle" @click.stop>
            <div class="ms-header">
              <div class="ms-handle" v-if="showHandle"></div>
              <div class="ms-title">{{ title }}</div>
              <button v-if="showClose" class="ms-close" @click="close">×</button>
            </div>
            <div class="ms-body">
              <slot />
            </div>
            <div class="ms-footer" v-if="$slots.footer">
              <slot name="footer" />
            </div>
          </div>
        </transition>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '' },
  height: { type: String, default: 'auto' }, // e.g. '70vh'
  showClose: { type: Boolean, default: true },
  maskClosable: { type: Boolean, default: true },
  showHandle: { type: Boolean, default: true }
})

const emit = defineEmits(['update:modelValue', 'close'])

const sheetStyle = computed(() => ({
  height: props.height === 'auto' ? undefined : props.height
}))

const close = () => {
  emit('update:modelValue', false)
  emit('close')
}

const onMask = () => {
  if (props.maskClosable) close()
}
</script>

<style scoped>
.ms-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: flex-end;
  z-index: 2000;
}
.ms-container {
  width: 100%;
  background: #fff;
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
  box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.1);
  max-height: 92vh;
  display: flex;
  flex-direction: column;
}
.ms-header {
  position: relative;
  padding: 10px 16px 8px;
  border-bottom: 1px solid #f1f5f9;
}
.ms-handle {
  position: absolute;
  top: 6px;
  left: 50%;
  transform: translateX(-50%);
  width: 36px;
  height: 4px;
  border-radius: 9999px;
  background: #e5e7eb;
}
.ms-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  text-align: center;
}
.ms-close {
  position: absolute;
  right: 8px;
  top: 6px;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  font-size: 22px;
  line-height: 32px;
  cursor: pointer;
  color: #6b7280;
}
.ms-body {
  padding: 12px 16px 16px;
  overflow: auto;
}
.ms-footer {
  padding: 10px 16px 16px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* Animations */
.sheet-fade-enter-active, .sheet-fade-leave-active { transition: opacity .2s ease; }
.sheet-fade-enter-from, .sheet-fade-leave-to { opacity: 0; }
.sheet-slide-enter-active, .sheet-slide-leave-active { transition: transform .2s ease; }
.sheet-slide-enter-from, .sheet-slide-leave-to { transform: translateY(100%); }
</style>

