<template>
  <div class="action-menu-root">
    <button
      ref="triggerRef"
      class="ghost-button action-menu-trigger"
      type="button"
      :aria-label="buttonLabel"
      :aria-expanded="isOpen ? 'true' : 'false'"
      @click.stop="toggleMenu"
    >
      <span class="dots-icon" aria-hidden="true">•••</span>
    </button>

    <Teleport to="body">
      <div
        v-if="isOpen"
        ref="menuRef"
        class="action-menu-popup"
        :style="menuStyle"
        @click.stop
      >
        <button
          v-for="action in actions"
          :key="action.key"
          class="menu-item"
          :class="{ 'menu-item-danger': action.danger }"
          type="button"
          @click="selectAction(action.key)"
        >
          {{ action.label }}
        </button>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from "vue";

type ActionKey = string;

interface ActionMenuItem {
  key: ActionKey;
  label: string;
  danger?: boolean;
}

defineProps<{
  actions: ActionMenuItem[];
  buttonLabel: string;
}>();

const emit = defineEmits<{
  select: [key: ActionKey];
}>();

const triggerRef = ref<HTMLElement | null>(null);
const menuRef = ref<HTMLElement | null>(null);
const isOpen = ref(false);
const top = ref(0);
const left = ref(0);

const menuStyle = computed(() => ({
  top: `${top.value}px`,
  left: `${left.value}px`,
}));

function updatePosition() {
  const trigger = triggerRef.value;
  const menu = menuRef.value;

  if (!trigger || !menu) {
    return;
  }

  const triggerRect = trigger.getBoundingClientRect();
  const menuRect = menu.getBoundingClientRect();
  const gap = 8;
  const viewportPadding = 12;

  const openBelow =
    triggerRect.bottom + gap + menuRect.height <=
    window.innerHeight - viewportPadding;

  top.value = openBelow
    ? triggerRect.bottom + gap
    : Math.max(viewportPadding, triggerRect.top - menuRect.height - gap);
  left.value = Math.min(
    window.innerWidth - menuRect.width - viewportPadding,
    Math.max(viewportPadding, triggerRect.right - menuRect.width),
  );
}

async function openMenu() {
  isOpen.value = true;
  await nextTick();
  updatePosition();
  window.addEventListener("pointerdown", handlePointerDown);
  window.addEventListener("resize", handleViewportChange);
  window.addEventListener("scroll", handleViewportChange, true);
}

function closeMenu() {
  if (!isOpen.value) {
    return;
  }

  isOpen.value = false;
  window.removeEventListener("pointerdown", handlePointerDown);
  window.removeEventListener("resize", handleViewportChange);
  window.removeEventListener("scroll", handleViewportChange, true);
}

function toggleMenu() {
  if (isOpen.value) {
    closeMenu();
    return;
  }

  void openMenu();
}

function handlePointerDown(event: Event) {
  const target = event.target as Node | null;
  if (
    target &&
    (menuRef.value?.contains(target) || triggerRef.value?.contains(target))
  ) {
    return;
  }

  closeMenu();
}

function handleViewportChange() {
  if (!isOpen.value) {
    return;
  }

  updatePosition();
}

function selectAction(key: ActionKey) {
  closeMenu();
  emit("select", key);
}

onBeforeUnmount(() => {
  closeMenu();
});
</script>
