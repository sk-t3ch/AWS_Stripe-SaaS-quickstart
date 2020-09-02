<template>
  <v-container fluid>
      <v-row align="center">
        <v-spacer/>
        <v-col cols="10">
            <amplify-authenticator username-alias="email" initial-auth-state="signup" v-if="!signedIn">
              <amplify-sign-up username-alias="email"  :form-fields.prop="formFields" slot="sign-up"></amplify-sign-up>
            </amplify-authenticator>
            <div v-if="signedIn ">
              <user-info class="my-2" />
              <amplify-sign-out />
            </div>
        </v-col>
        <v-spacer/>
      </v-row>
  </v-container>
</template>
<script>
import UserInfo from "../components/UserInfo";
import { onAuthUIStateChange } from '@aws-amplify/ui-components' 

export default {
  components: {
    UserInfo,
  },
  data() {
    return {
      user: this.$store.getters.user || undefined,
      authState: undefined,
      authConfig: {
        signInConfig:  { 
          isSignUpDisplayed: false,
          }, 
        },
        formFields: [ 
          { 
            type: 'email'
          }, 
          { 
            type: 'password',
          }
          ]
      };
    },
  created() {
    onAuthUIStateChange((authState) => {
      if (authState) this.authState = authState;
      if(this.authState === 'signedin' && this.user === undefined){
        this.$store.dispatch('getUser');
      }
    })
  },    
  computed: {
    signedIn() {
        return this.authState === 'signedin';
    },
  },
  beforeDestroy() {
    return onAuthUIStateChange;
  }
}
</script>
<style scoped>
.section{
        position: absolute;
        top: 50%;
        left: 50%;
        margin-right: -50%;
        transform: translate(-50%, -50%)
}


</style>


