import Vue from 'vue'
import App from './App.vue'
import '@aws-amplify/ui-vue';
import Amplify from 'aws-amplify';
import  { Auth } from 'aws-amplify';

import store from './store'
import router from './router'
import vuetify from './plugins/vuetify';

import VueClipboard from 'vue-clipboard2';
import fullscreen from 'vue-fullscreen';
const VueScrollTo = require('vue-scrollto');

Vue.use(fullscreen);
Vue.use(VueScrollTo);
Vue.use(VueClipboard);

const ROOT_DOMAIN = 't3chflicks.org';

Amplify.configure({
    Auth: {
        region: 'EU-WEST-1',
        userPoolId: 'eu-west-1_h8FW1S7W7',
        userPoolWebClientId: '2ifgth5iiamln4u77sjm50kvpb',
        mandatorySignIn: false,
        oauth: {
            scope: [ 'email', 'openid'],
            redirectSignIn: `https://saas-app.${ROOT_DOMAIN}/`,
            redirectSignOut: `https://saas-app.${ROOT_DOMAIN}/`,
            responseType: 'code'
        }
    },
    API: {
        endpoints: [
            {
                name: "UserAPI",
                endpoint: `https://saas-user.${ROOT_DOMAIN}`,
                custom_header: async () => { 
                    return { Authorization: `Bearer ${(await Auth.currentSession()).getIdToken().getJwtToken()}` }                  
                }
            },
            {
                name: "TestAPIKey",
                endpoint: `https://saas-test.${ROOT_DOMAIN}`,
            }
        ]
    }
});


Vue.prototype.$Amplify = Amplify;
                    
Vue.config.productionTip = false;

new Vue({
    store,
    router,
    vuetify,
    render: h => h(App)
}).$mount('#app')