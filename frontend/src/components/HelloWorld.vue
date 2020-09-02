<template>
  <v-container>
    <v-row class="text-center">
      <v-col class="mb-4" cols="12">
        <v-card color="primary px-6">
          <v-card-title class="white--text display-2 mb-1">
            SaaS Quickstart
            <a href="https://github.com/sk-t3ch/AWS-saas-quickstart" target="new">
              <v-icon dark class="mx-4">mdi-git</v-icon>
            </a>
          </v-card-title>
          <v-divider dark></v-divider>
          <v-card class="primary lighten-1 mt-2 mx-4">
            <v-card-title class="white--text pb-8 text-left">Test your API Key</v-card-title>
            <v-card-text>
              <v-text-field color="white" dark label="Your API Key" v-model="testAPIKey"></v-text-field>
              <v-btn dark text outlined @click="testKey">TEST</v-btn>
              <v-text-field v-if="response" dark max-width="400" :value="response" readonly></v-text-field>
            </v-card-text>
          </v-card>
          <v-card-text>
            <v-divider dark></v-divider>
            <v-row>
              <v-col cols="8">
                <v-card-text
                  class="text-left subtitle white--text"
                >This example app has the following features:</v-card-text>
                <v-list color="primary" class="text-left" dark dense left shaped>
                  <v-list-item>
                    <v-list-item-icon>
                      <v-icon>mdi-atom</v-icon>
                    </v-list-item-icon>
                    <v-list-item-content>
                      <v-list-item-title>Stripe Payments</v-list-item-title>
                      <v-list-item-subtitle>Use stripe API to manage all payments including subscriptions</v-list-item-subtitle>
                    </v-list-item-content>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-icon>
                      <v-icon>mdi-atom</v-icon>
                    </v-list-item-icon>
                    <v-list-item-content>
                      <v-list-item-title>Step Functions</v-list-item-title>
                      <v-list-item-subtitle>Manage subscriptions as workflows</v-list-item-subtitle>
                    </v-list-item-content>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-icon>
                      <v-icon>mdi-atom</v-icon>
                    </v-list-item-icon>
                    <v-list-item-content>
                      <v-list-item-title>User Management</v-list-item-title>
                      <v-list-item-subtitle>AWS Cognito service manages users and provide hooks for flows wuth Lambda functions</v-list-item-subtitle>
                    </v-list-item-content>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-icon>
                      <v-icon>mdi-atom</v-icon>
                    </v-list-item-icon>
                    <v-list-item-content>
                      <v-list-item-title>Authenticated User API</v-list-item-title>
                      <v-list-item-subtitle>AWS Amplify components with Vue JS to create authenticated API requests</v-list-item-subtitle>
                    </v-list-item-content>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-icon>
                      <v-icon>mdi-atom</v-icon>
                    </v-list-item-icon>
                    <v-list-item-content>
                      <v-list-item-title>Test Service with ALB</v-list-item-title>
                      <v-list-item-subtitle>Application load balancer with Lambda Function</v-list-item-subtitle>
                    </v-list-item-content>
                  </v-list-item>
                </v-list>
              </v-col>
              <v-col cols="4">
                <fullscreen class="wrapper" ref="fullscreen" @change="fullscreenChange">
                  <v-img
                    contain
                    @click="toggle"
                    class="white rounded-lg image-container elevation-12"
                    src="@/assets/architecture.png"
                  ></v-img>
                </fullscreen>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { API } from "aws-amplify";

export default {
  name: "HelloWorld",
  data: () => ({
    testAPIKey: "",
    response: "",
    fullscreen: false,
  }),
  methods: {
    toggle() {
      this.$refs["fullscreen"].toggle();
    },
    fullscreenChange(fullscreen) {
      this.fullscreen = fullscreen;
    },
    async testKey() {
      if (this.testAPIKey !== "") {
        try {
          const myInit = {
            headers: {},
            body: {
              key: this.testAPIKey,
            },
          };
          const response = await API.post("TestAPIKey", "/", myInit);
          this.response = JSON.stringify(response);
        } catch (err) {
          if (err.message === "Request failed with status code 400") {
            this.response = JSON.stringify({
              ERROR: "400",
            });
          }
          if (err.message === "Request failed with status code 500") {
            this.response = JSON.stringify({
              ERROR: "500",
            });
          }
          console.log("ERR: ", err);
        }
      } else {
        alert("enter your key");
      }
    },
  },
};
</script>
<style lang="scss" scoped>
.wrapper {
  position: relative;
  height: 300px;
  .image-container {
    height: 100%;
    width: 100%;
    cursor: zoom-in;
  }
  &.fullscreen {
    display: flex;
    justify-content: center;
    align-items: center;
    .image-container {
      height: 80%;
      width: 80%;
      cursor: zoom-out;
    }
  }
}
</style>
