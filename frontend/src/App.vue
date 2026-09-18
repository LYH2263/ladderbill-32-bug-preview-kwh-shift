<script setup>
</script>
<template>
  <div class="layout-meter">
    <aside class="meter-rail">
      <div class="brand">⚡ 阶梯电费</div>
      <router-link to="/">总览</router-link>
      <router-link to="/accounts">户号</router-link>
      <router-link to="/readings">抄表</router-link>
      <router-link to="/workbench">测算台</router-link>
      <router-link to="/tiers">阶梯表</router-link>
      <router-link to="/compare">尖峰对比</router-link>
      <router-link to="/history">记录</router-link>
      <router-link to="/settings">设置</router-link>
    </aside>
    <main><router-view /></main>
  </div>
</template>
