<template>
  <div class="city-map-view">
    <CityMapParent />
  </div>
</template>

<script>
import CityMapParent from '../components/city-map/CityMapParent.vue';

export default {
  name: 'CityMapView',
  components: {
    CityMapParent
  }
}
</script>

<style scoped>
.city-map-view {
  width: 100%;
  height: 100vh;
  overflow: hidden;
  padding: 0;
  margin: 0;
  position: absolute;
  top: 0;
  left: 0;
}
</style> 