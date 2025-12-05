<template>
  <header class="header">
    <!-- 动态背景粒子效果 -->
    <div class="bg-particles">
      <div class="particle" v-for="i in 20" :key="i" :style="getParticleStyle(i)"></div>
    </div>

    <!-- 主要内容 -->
    <div class="header-content">
      <div class="container">
        <!-- Logo/图标区域 -->
        <div class="logo-section">
          <div class="logo-icon">
            <svg viewBox="0 0 100 100" class="logo-svg">
              <defs>
                <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
                </linearGradient>
              </defs>
              <circle cx="50" cy="50" r="40" fill="url(#logoGradient)" opacity="0.8"/>
              <path d="M30 50 L45 35 L70 60 L45 60 Z" fill="white" opacity="0.9"/>
            </svg>
          </div>
        </div>

        <!-- 标题区域 -->
        <div class="title-section">
          <h1 class="main-title">
            <span class="title-text">数据可视化分析平台</span>
            <span class="title-underline"></span>
          </h1>
          <p class="subtitle">
            <span class="subtitle-icon">📊</span>
            <span>多维度招聘数据分析 · 智能洞察 · 决策支持</span>
          </p>
        </div>

        <!-- 装饰性元素 -->
        <div class="decorative-elements">
          <div class="decorative-circle circle-1"></div>
          <div class="decorative-circle circle-2"></div>
          <div class="decorative-circle circle-3"></div>
        </div>
      </div>
    </div>

    <!-- 底部波浪装饰 -->
    <div class="wave-decoration">
      <svg viewBox="0 0 1200 120" preserveAspectRatio="none">
        <path d="M0,60 Q300,20 600,60 T1200,60 L1200,120 L0,120 Z" fill="rgba(255,255,255,0.05)"/>
      </svg>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'

// 生成粒子样式
const getParticleStyle = (index) => {
  const size = Math.random() * 4 + 2
  const left = Math.random() * 100
  const animationDelay = Math.random() * 5
  const animationDuration = Math.random() * 10 + 10

  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${left}%`,
    animationDelay: `${animationDelay}s`,
    animationDuration: `${animationDuration}s`
  }
}
</script>

<style scoped>
.header {
  position: relative;
  width: 100%;
  min-height: 280px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-size: 200% 200%;
  animation: gradientShift 15s ease infinite;
  overflow: hidden;
  margin-bottom: 40px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

/* 背景粒子效果 */
.bg-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 1;
}

.particle {
  position: absolute;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  animation: float linear infinite;
  pointer-events: none;
}

@keyframes float {
  0% {
    transform: translateY(100vh) translateX(0) rotate(0deg);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100px) translateX(100px) rotate(360deg);
    opacity: 0;
  }
}

/* 主要内容区域 */
.header-content {
  position: relative;
  z-index: 2;
  padding: 50px 20px 60px;
  backdrop-filter: blur(1px);
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  position: relative;
}

/* Logo区域 */
.logo-section {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.logo-icon {
  width: 80px;
  height: 80px;
  animation: logoFloat 3s ease-in-out infinite;
  filter: drop-shadow(0 10px 20px rgba(0, 0, 0, 0.3));
}

@keyframes logoFloat {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-10px) rotate(5deg); }
}

.logo-svg {
  width: 100%;
  height: 100%;
}

/* 标题区域 */
.title-section {
  text-align: center;
  color: white;
  position: relative;
  z-index: 3;
}

.main-title {
  font-size: 3.5em;
  font-weight: 700;
  margin-bottom: 15px;
  position: relative;
  display: inline-block;
  background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 30px rgba(255, 255, 255, 0.5);
  animation: titleFadeIn 1s ease-out;
}

@keyframes titleFadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.title-underline {
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 100px;
  height: 4px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
  border-radius: 2px;
  animation: underlineExpand 1.5s ease-out 0.5s both;
}

@keyframes underlineExpand {
  from {
    width: 0;
    opacity: 0;
  }
  to {
    width: 100px;
    opacity: 1;
  }
}

.subtitle {
  font-size: 1.3em;
  opacity: 0.95;
  font-weight: 300;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  animation: subtitleFadeIn 1s ease-out 0.3s both;
}

@keyframes subtitleFadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 0.95;
    transform: translateY(0);
  }
}

.subtitle-icon {
  font-size: 1.2em;
  animation: iconBounce 2s ease-in-out infinite;
}

@keyframes iconBounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

/* 装饰性圆圈 */
.decorative-elements {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.decorative-circle {
  position: absolute;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.2);
  animation: circlePulse 4s ease-in-out infinite;
}

.circle-1 {
  width: 200px;
  height: 200px;
  top: -50px;
  right: 10%;
  animation-delay: 0s;
}

.circle-2 {
  width: 150px;
  height: 150px;
  bottom: -30px;
  left: 15%;
  animation-delay: 1s;
}

.circle-3 {
  width: 100px;
  height: 100px;
  top: 50%;
  right: 20%;
  animation-delay: 2s;
}

@keyframes circlePulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.3;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.5;
  }
}

/* 底部波浪装饰 */
.wave-decoration {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 60px;
  z-index: 1;
}

.wave-decoration svg {
  width: 100%;
  height: 100%;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-title {
    font-size: 2.2em;
  }

  .subtitle {
    font-size: 1em;
    flex-direction: column;
    gap: 5px;
  }

  .logo-icon {
    width: 60px;
    height: 60px;
  }

  .header-content {
    padding: 40px 20px 50px;
  }

  .header {
    min-height: 220px;
  }
}

@media (max-width: 480px) {
  .main-title {
    font-size: 1.8em;
  }

  .subtitle {
    font-size: 0.9em;
  }
}
</style>

