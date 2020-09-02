import Vue from 'vue'
import Vuex from 'vuex'
import { API } from 'aws-amplify';

Vue.use(Vuex);

export default new Vuex.Store({
  state: {
    user: undefined,
    alert: {
      message: '',
      type: ''
    },
  },
  
  getters: {
    getAlertObj: state => {
      if (state.alert.message && state.alert.type){
        return state.alert;
      }
      return; 
    },
    user(state){
      return state.user;
    }
  },
  mutations: {
    setUser(state, user) {
      state.user = user;
    },
    setAlert(state, alert){
      state.alert.message = alert.message;
      state.alert.type = alert.type;
    },
    clearAlert(state){
      state.alert.message = '';
      state.alert.type = '';
    },
  },
  
  actions: {
    async getUser({ commit }) {
      const response = await API.get('UserAPI', '/user');
      return commit('setUser', response.user);
    }
  }
});
