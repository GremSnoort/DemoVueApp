<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

const slides = [
  { src: "/slider/image07.jpg", alt: "Slide 1" },
  { src: "/slider/image08.webp", alt: "Slide 2" },
  { src: "/slider/image10.webp", alt: "Slide 3" },
];

const idx = ref(0);
const paused = ref(false);

const trackStyle = computed(() => ({
  transform: `translateX(-${idx.value * 100}%)`,
}));

function next() {
  idx.value = (idx.value + 1) % slides.length;
}

function go(i) {
  idx.value = i;
}

let t = null;

onMounted(() => {
  t = setInterval(() => {
    if (!paused.value) next();
  }, 4500);
});

onBeforeUnmount(() => {
  if (t) clearInterval(t);
});
</script>

<template>
  <div
    class="slider"
    @mouseenter="paused = true"
    @mouseleave="paused = false"
  >
    <div class="track" :style="trackStyle">
      <div v-for="(s, i) in slides" :key="i" class="slide">
        <img :src="s.src" :alt="s.alt" />
        <div class="shade"></div>
      </div>
    </div>

    <div class="dots">
      <button
        v-for="(_, i) in slides"
        :key="i"
        class="dot"
        :class="{ active: i === idx }"
        @click="go(i)"
        aria-label="Go to slide"
      />
    </div>
  </div>
</template>
