<template>
  <v-alert
    v-model="show"
    :type="type"
    :dismissible="true"
    class="ott"
    elevation="5"
    transition="fade-transition"
  >
    {{ message }}
  </v-alert>
</template>

<script>
export default {
  data: () => ({
    show: false,
    type: 'success',
    message: ''
  }),
  computed: {
    new_alert() {
      return this.processAlert();
    }
  },
  watch: {
    new_alert() {
      return this.$store.getters.getAlertObj;
    }
  },
  methods: {
    processAlert() {
      const new_alert = this.$store.getters.getAlertObj;
      if (new_alert) {
        this.show = true;
        this.message = new_alert.message;
        this.type = new_alert.type;
        this.duration = new_alert.duration || 1500;
        setTimeout(() => {
          this.show = false;
        }, this.duration);
        this.$store.commit('clearAlert');
        return true;
      } else {
        this.show = false;
        return false;
      }
    }
  }
};
</script>
<style scoped>
.ott{
  z-index: 20;
  position: fixed;
  width: 100%;
  border-top-left-radius: 0%;
  border-top-right-radius: 0%;
  border-bottom-left-radius: 5%;
  border-bottom-right-radius: 5%;
  /* background-color: blue; */
  /* width:10px !important; */
}
</style>