<template>
  <v-container>
    <v-row justify="space-around" class="pt-12">
      <v-col cols="auto" v-for="(plan, planIdx) in plans" :key="'plan-' + planIdx">
        <v-card class="primary pt-2 px-2" dark>
          <div class="subtitle-2" v-if="user && user.plan === plan.name">
            <v-chip>
              <v-icon>mdi-star</v-icon>Current Plan
            </v-chip>
          </div>
          <v-card-title class="pb-8">{{ plan.name }}</v-card-title>
          <v-card-text class="pb-8">
            <v-btn to="/" text class="d-flex align-center display-1">
              <v-icon>mdi-hand</v-icon>API
            </v-btn>
            <div class="features">{{ plan.description }}</div>
            <div class="cost">
              <v-chip>£{{ plan.cost }}</v-chip>
            </div>
          </v-card-text>
          <div v-if="user === undefined">
            <v-card-actions v-if="plan.name !== 'Free'">
              <v-btn depressed text outlined to="/user">Buy</v-btn>
              <v-spacer />
              <v-btn text outlined to="/user">
                Subscribe
                <v-icon>mdi-lock</v-icon>
              </v-btn>
            </v-card-actions>
            <v-card-actions v-else>
              <v-btn text outlined depressed to="/user">Set</v-btn>
              <v-spacer />
            </v-card-actions>
          </div>
          <!-- user is defined -->
          <div v-else>
            <!-- if different plan to one user is currently on -->
            <div v-if="user.plan !== plan.name">
              <!-- if this differnt plan is not the free plan -->
              <v-card-actions v-if="plan.name !== 'Free'">
                <v-btn text outlined depressed @click="checkout(planIdx, false)">Buy</v-btn>
                <v-spacer />
                <v-btn text outlined @click="checkout(planIdx, true)" v-scroll-to="'#checkout'">
                  Subscribe
                  <v-icon>mdi-lock</v-icon>
                </v-btn>
              </v-card-actions>
              <!-- if this different plan is the free plan -->
              <v-card-actions v-else>
                <v-btn text outlined depressed @click="checkout(planIdx, true)">Set</v-btn>
                <v-spacer />
              </v-card-actions>
              <v-spacer />
            </div>
            <!-- if same plan as user is currently on -->
            <div v-else>
              <!-- if same plan as user and not free -->
              <v-card-actions v-if="plan.name !== 'Free'">
                <v-btn class="primary" depressed @click="checkout(planIdx, false)">Buy</v-btn>
                <v-spacer />
                <v-btn class="primary" @click="checkout(planIdx, true)" v-scroll-to="'#checkout'">
                  Subscribe
                  <v-icon>mdi-lock</v-icon>
                </v-btn>
              </v-card-actions>
              <v-spacer />
            </div>
            <!-- if same plan as user on and free -->
          </div>
        </v-card>
      </v-col>
    </v-row>
    <div v-if="isPaying" class="pt-8" id="checkout">
      <v-card class="primary py-2 px-2 white--text" dark>
        <v-card-title>Payment</v-card-title>
        <v-card-subtitle class="subtitle-2 pb-8">Powered by Stripe (Test Card 4000 0582 6000 0005)</v-card-subtitle>
        <v-card-text class="pb-0 white--text">
          <div class="basket pa-4" v-if="!isLoadingSession">
            Plan: {{ selectedPlan.name }} {{ selectedPlan.isSubscribe ? 'subscription' : ''}}
            <br />
            <div v-if="selectedPlan.isSubscribe">
              Start Date: {{ new Date().toLocaleDateString() }}
              <v-tooltip top>
                <template v-slot:activator="{ on, attrs }">
                  <v-icon color="info" dark small v-bind="attrs" v-on="on">mdi-information</v-icon>
                </template>
                <span>Previous subscriptions will terminate.</span>
              </v-tooltip>
            </div>
            <br />
            Amount: £{{ selectedPlan.cost }}
          </div>
          <div class="basket pa-4" v-else>
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
          </div>
        </v-card-text>
        <v-card-actions class="px-4" v-if="selectedPlan.name !=='Free'">
          <v-spacer />
          <stripe-checkout
            ref="sessionRef"
            :pk="publishableKey"
            :session-id="sessionId"
          >
            <template slot="checkout-button">
              <v-btn @click="$refs.sessionRef.redirectToCheckout()" v-show="!isLoadingSession">Pay</v-btn>
            </template>
          </stripe-checkout>
        </v-card-actions>
        <v-card-actions class="px-4" v-else>
          <v-spacer />
          <v-btn @click="setFreePlan">Set</v-btn>
        </v-card-actions>
      </v-card>
    </div>
  </v-container>
</template>
 
<script>
import { StripeCheckout } from "vue-stripe-checkout";
import { API } from "aws-amplify";

export default {
  name: "Home",
  components: {
    StripeCheckout,
  },
  data() {
    return {
      isLoadingSession: false,
      isPaying: false,
      isChangingPlan: false,
      sessionId: null,
      selectedPlan: null,
      plans: [
        {
          name: "Free",
          description: "50 credits per week",
          cost: 0,
        },
        {
          name: "Basic",
          description: "1,000 credits per month",
          cost: 5,
        },
        {
          name: "Power",
          description: "100,000 credits per month",
          cost: 50,
        },
      ],
      loading: false,
      publishableKey:
        "",
    };
  },
  computed: {
    user() {
      return this.$store.getters.user || undefined;
    },
  },
  methods: {
    setFreePlan() {
      this.isPaying = false;
      API.get("UserAPI", "/stop-subscriptions")
        .then((resp) => {
          this.isLoadingSession = false;
          this.$store.commit("setUser", resp.user);
          this.$store.commit("setAlert", {
            type: "success",
            message: "All subscriptions cancelled and reverted to Free plan.",
          });
        })
        .catch((err) => {
          console.log("ERROR: ", err);
          this.isLoadingSession = false;
        });
    },
    checkout(planIdx, isSubscribe) {
      const plan = this.plans[planIdx];
      this.selectedPlan = {
        ...plan,
        isSubscribe,
      };
      this.isPaying = true;
      if (this.selectedPlan.name === "Free") return;
      this.isLoadingSession = true;

      const request = {
        headers: {},
        body: {
          plan: plan.name,
          subscribe: isSubscribe,
        },
      };
      API.post("UserAPI", "/checkout", request)
        .then((resp) => {
          this.sessionId = resp.session_id;
          this.isLoadingSession = false;
        })
        .catch((err) => {
          console.log("ERROR: ", err);
          this.isLoadingSession = false;
        });
    },
  },
};
</script>
<style>
.features {
  padding-top: 20px;
  padding-bottom: 20px;
  font-size: 20px;
}

.basket {
  background: #1b2037;
  border-radius: 20px 5px 0px 0px;
}
</style>