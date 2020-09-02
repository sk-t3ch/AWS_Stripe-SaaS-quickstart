<template>
  <v-card class="elevation-8" color="primary" dark>
    <v-card-title class="ml-1">User: {{ username }}</v-card-title>
    <v-card-text class="body-1 white--text">
      <div class="infoContainer">
        <v-progress-linear v-if="isLoading" indeterminate></v-progress-linear>
        <div v-if="email">
          <h3>Email</h3>
          <p>{{ email }}</p>
        </div>
        <div v-if="user && user.plan">
          <h3>Plan</h3>
          <p class="d-inline-flex">{{ user.plan }}</p>
          <v-btn small text color="info ml-4" dark to="/pricing">change?</v-btn>
          <p
            class="caption font-weight-thin"
          >Last Renewed - {{ new Date(user.lastUpdate * 1000).toLocaleString() }}</p>
        </div>
        <div v-if="user && user.startDate">
          <h3>Start Date</h3>
          <p>{{ new Date(user.startDate * 1000).toLocaleString() }}</p>
        </div>
      </div>
      <div class="infoContainer mt-4" v-if="user && user.key">
        <h3 class="mb-1">API Key</h3>
        <v-progress-linear v-if="isLoadingKey" color="info" indeterminate></v-progress-linear>
        {{ user.key }}
        <v-btn
          class="ma-2"
          color="info"
          v-clipboard:copy="user.key"
          v-clipboard:success="() => $store.commit('setAlert', {type: 'success', message: 'Copied!'})"
          icon
          x-small
        >
          <v-icon light>mdi-content-copy</v-icon>
        </v-btn>
        <v-btn class="ma-2" color="info" icon x-small @click="getNewAPIKey">
          <v-icon light>mdi-cached</v-icon>
        </v-btn>
      </div>
    </v-card-text>
    <v-card-actions></v-card-actions>
  </v-card>
</template>

<script>
import { Auth } from "aws-amplify";
import { API } from "aws-amplify";

export default {
  name: "HelloWorld",
  data() {
    return {
      email: null,
      isLoading: false,
      isShowingInfo: null,
      username: "",
      APIKey: "",
      isShowingKey: null,
      isLoadingKey: false
    };
  },
  async created() {
    const cognitoUser = await Auth.currentAuthenticatedUser();
    this.email = cognitoUser.attributes.email;
    this.username = cognitoUser.username;
  },
  computed: {
    user() {
      return this.$store.getters.user;
    }
  },
  methods: {
    async getNewAPIKey() {
      this.isLoadingKey = true;
      const response = await API.get("UserAPI", "/generate-key");
      this.isLoadingKey = false;
      this.$store.commit("setUser", {
        ...this.user,
        key: response.key
      });
    }
  }
};
</script>
<style scoped>
.infoContainer {
  background-color: #1b2037;
  border: 1px solid #007bff;
  border-radius: 10px;
  padding: 20px 20px 20px 20px;
  line-break: anywhere;
}
</style>