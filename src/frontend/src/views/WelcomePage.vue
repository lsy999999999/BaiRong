<template>
  <div class="welcome-container">
    <div class="welcome-content">
      <div class="title-area">
        <h1 class="main-title">AI Social Behavior Simulator</h1>
        <p class="subtitle">A Platform to Train AI in Understanding Complex Social Behavior Patterns</p>
      </div>
      
      <div class="animation-container">
        <div class="taiji-container">
          <svg class="taiji" width="150" height="150" viewBox="0 0 150 150" xmlns="http://www.w3.org/2000/svg">
  <!-- 黑色部分 -->
  <path class="taiji-dark" d="
    M75,0
    A75,75 0 0,0 75,150
    A37.5,37.5 0 0,1 75,75
    A37.5,37.5 0 0,0 75,0
    Z" />
  <!-- 白色部分 -->
  <path class="taiji-light" d="
    M75,150
    A75,75 0 0,0 75,0
    A37.5,37.5 0 0,1 75,75
    A37.5,37.5 0 0,0 75,150
    Z" />
  <!-- 上方白色小圆点（在黑色区域内） -->
  <circle cx="75" cy="37.5" r="7.5" class="taiji-light"/>
  <!-- 下方黑色小圆点（在白色区域内） -->
  <circle cx="75" cy="112.5" r="7.5" class="taiji-dark"/>
</svg>
</div>
      </div>
      
      <router-link to="/" class="enter-button">
        <span>Enter System</span>
        <i class="fa fa-arrow-right"></i>
      </router-link>
      
      <div class="info-section">
        <p>This system aims to train AI models to understand and simulate complex social behavior patterns, providing a controlled experimental environment for social behavior research. Through simulating various social scenarios, it helps AI systems learn subtle patterns and decision processes in human social interactions.</p>
        <p>The system integrates three major modules: individual behavior, group dynamics, and social networks, offering rich behavior simulation scenarios and precise analysis tools.</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'WelcomePage'
}
</script>

<style scoped>
/* Welcome页面特定App样式 */
:deep(#app) {
  height: 100vh;
  overflow: hidden;
  position: relative;
}

.welcome-container {
  height: 100vh;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  position: relative;
  background-color: var(--bg-color);
  /* 确保这个页面固定为全屏 */
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.welcome-content {
  width: 90%;
  max-width: 800px;
  height: 90vh;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  text-align: center;
  z-index: 2;
  animation: fadeIn 1s ease;
}

.title-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding-bottom: 2vh;
}

.main-title {
  font-size: min(3.5rem, 6vh);
  font-weight: 700;
  color: var(--text-color);
  margin-bottom: 15px;
  letter-spacing: 1px;
  animation: fadeIn 1.5s ease-in-out;
}

.subtitle {
  font-size: min(1.4rem, 2.5vh);
  color: var(--secondary-color);
  animation: fadeIn 1.8s ease-in-out;
}

.animation-container {
  flex: 2;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* Taiji (Yin-Yang) animation */
.taiji-container {
  position: relative;
  width: min(150px, 20vh);
  height: min(150px, 20vh);
  display: flex;
  justify-content: center;
  align-items: center;
}

.taiji {
  width: 100%;
  height: 100%;
  animation: rotateCW 8s linear infinite;
}

/* 太极图颜色 */
.taiji-dark {
  fill: var(--taiji-dark);
}

.taiji-light {
  fill: var(--taiji-light);
}

@keyframes rotateCW {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.enter-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: min(15px, 2vh) min(40px, 4vh);
  background-color: var(--accent-color);
  color: white;
  border: none;
  border-radius: 50px;
  font-size: min(1.2rem, 2.2vh);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  margin-bottom: 4vh;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

.enter-button span {
  margin-right: 10px;
}

.enter-button:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 25px rgba(0, 0, 0, 0.3);
}

.enter-button:active {
  transform: translateY(0);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}

.info-section {
  flex: 2;
  color: var(--secondary-color);
  font-size: min(1.1rem, 2vh);
  line-height: 1.7;
  max-width: 700px;
  margin: 0 auto;
  animation: fadeIn 2s ease-in-out;
  overflow-y: auto;
  padding: 0 1rem;
}

.info-section p {
  margin-bottom: 15px;
}

/* 隐藏移动端样式，专注于电脑端 */
@media (max-width: 768px) {
  /* 保留基本布局 */
}
</style>