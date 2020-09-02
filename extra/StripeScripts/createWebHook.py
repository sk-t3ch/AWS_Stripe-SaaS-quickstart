import stripe

STRIPE_SECRET_KEY = "sk_test_51HKlevJAV1tclqKuuFvkoHoOoygiavnUNDet2HXnyXd2bsNVCzvxkW2bNAA8HivobXs5idcpa5VCzK0b90wub2h100rsOtHlun"
stripe.api_key = STRIPE_SECRET_KEY

# URL = Webhook url
URL = "https://stripe.t3chflicks.org/payment-success"


create_web_hook_resp = stripe.WebhookEndpoint.create(
  url=URL,
  enabled_events=[
    "charge.succeeded",
  ],
)


secret = create_web_hook_resp["secret"]

print(f"The web hook created for {URL} has a secret={secret}")
# whsec_GJx2kmziA8JG3Cjs3EVVcRZzYaD5nsmz