<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-btn to="/" text class="d-flex align-center display-1">
        <v-icon>mdi-hand</v-icon>API
      </v-btn>

      <v-spacer></v-spacer>
      <v-btn to="pricing" large text>Pricing</v-btn>

      <v-btn to="user" large text>
        Account
        <v-icon class="ml-2">mdi-account-key</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main class="bax" fluid>
      <alert-bar />
      <router-view />
    </v-main>
    <v-footer dark color="primary">
      <v-spacer />Made by
      <v-btn
        text
        class="text-none px-1 mx-0"
        target="_blank"
        href="https://t3chflicks.org"
      >T3chFlicks</v-btn>- A tech focused education and services company
    </v-footer>
  </v-app>
</template>

<script>
import AlertBar from "./components/AlertBar";

export default {
  name: "App",
  components: {
    AlertBar,
  },
};
</script>
<style>
:root {
  --amplify-primary-color: #13216f;
  --amplify-primary-tint: #007bff;
  --amplify-primary-shade: #007bff;
}

.bax {
  background-image: url("./assets/wallpaper.png");
  background-repeat: repeat;
  background-size: 3vw;
}
</style>