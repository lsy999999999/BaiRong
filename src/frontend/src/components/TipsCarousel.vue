<template>
    <div class="tips-carousel">
        <transition name="slide">
            <div class="tips-content" :key="currentIndex">
                <span class="tip-number">{{ currentIndex + 1 }}/{{ tips.length }}</span>
                <span class="tip-text">{{ currentTip }}</span>
            </div>
        </transition>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';

const tips = ref([]);
const currentIndex = ref(0);
const currentTip = ref('');
let timer = null;

const getTips = async () => {
    try {
        const res = await axios.get('/api/pipeline/tips');
        tips.value = res.data.tips;
        if (tips.value.length > 0) {
            currentTip.value = tips.value[0];
        }
    } catch (error) {
        console.error('获取tips失败:', error);
    }
};

const rotateTips = () => {
    if (tips.value.length <= 1) return;
    
    let newIndex;
    do {
        newIndex = Math.floor(Math.random() * tips.value.length);
    } while (newIndex === currentIndex.value);
    
    currentIndex.value = newIndex;
    currentTip.value = tips.value[currentIndex.value];
};

onMounted(() => {
    getTips();
    timer = setInterval(rotateTips, 5000);
});

onUnmounted(() => {
    if (timer) {
        clearInterval(timer);
    }
});
</script>

<style scoped>
.tips-carousel {
    height: 60px;
    width: 100%;
    overflow: hidden;
    position: relative;
    background: transparent;
    border-radius: 8px;
}

.tips-content {
    font-size: 14px;
    color: #4a90e2;
    line-height: 1.5;
    text-align: center;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    position: absolute;
    left: 0;
    right: 0;
    padding: 0 15px;
    box-sizing: border-box;
}

.tip-number {
    background: rgba(74, 144, 226, 0.1);
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    color: #4a90e2;
    min-width: 40px;
    flex-shrink: 0;
    text-align: center;
}

.tip-text {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: #4a90e2;
    text-shadow: none;
    height: 20px;
    line-height: 20px;
    text-align: center;
    min-width: 200px;
}

.slide-enter-active,
.slide-leave-active {
    transition: all 0.3s ease;
    position: absolute;
    width: 100%;
    left: 0;
    right: 0;
    padding: 0 15px;
    box-sizing: border-box;
}

.slide-enter-from {
    transform: translateY(100%);
    opacity: 0;
}

.slide-leave-to {
    transform: translateY(-100%);
    opacity: 0;
}
</style> 