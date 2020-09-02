
import boto3
import os
import json
import stripe
      
dynamodb = boto3.resource('dynamodb')
PRODUCT_TABLE_NAME = os.environ['PRODUCT_TABLE_NAME']
DOMAIN_NAME = os.environ['DOMAIN_NAME']
product_table = dynamodb.Table(PRODUCT_TABLE_NAME)
USER_TABLE_NAME = os.environ['USER_TABLE_NAME']
user_table = dynamodb.Table(USER_TABLE_NAME)
# TODO: ssm keys
STRIPE_SECRET_KEY = os.environ['STRIPE_SECRET_KEY']
stripe.api_key = STRIPE_SECRET_KEY

def handler(event, context):
  """
  Stripe Checkout - This function expects a POST request with { 'plan': 'Basic', 'subscribe': True } and username.
  The stripe API is used to create a Session for purchasing a plan.
  """
  # TODO reduce acccess control to your domain requests
  response = {
    "headers": {
      'Access-Control-Allow-Origin': '*'
    }
  }

  try:
    username = event["requestContext"]["authorizer"]["claims"]["cognito:username"]
    user_table_query_resp = user_table.get_item(Key={'Id':username})
    user = user_table_query_resp["Item"]
    stripe_customer_id = user["StripeId"]
    username = user["Id"]

    request = json.loads(event["body"])
    plan_name = request["plan"]
    subscribe = request["subscribe"]
    get_dynamo_product_resp = product_table.get_item(Key={'name':plan_name})
    plan = get_dynamo_product_resp.get('Item', False)
    if plan:
      lookup_key = f"{plan['name']}_{ 'monthly_price' if subscribe else 'instant_price' }"
      get_stripe_price_resp = stripe.Price.list(
          active=True,
          lookup_keys=[lookup_key]
      )
      stripe_price_id = get_stripe_price_resp['data'][0]['id']
      if subscribe:
        # TODO replace success and failure urls with one from site
        session = stripe.checkout.Session.create(
          payment_method_types=['card'],
          line_items=[{
            'price': stripe_price_id,
            'quantity': 1,
          }],
          mode='subscription',
          customer=stripe_customer_id,
          subscription_data={'metadata': { 'username': username, 'plan': plan['name'], 'price_id': stripe_price_id, 'subscribe': subscribe }},
          success_url=f'https://{DOMAIN_NAME}',
          cancel_url=f'https://{DOMAIN_NAME}',
        )
      else:
        session = stripe.checkout.Session.create(
          payment_method_types=['card'],
          line_items=[{
            'price': stripe_price_id,
            'quantity': 1,
          }],
          mode='payment',
          customer=stripe_customer_id,
          payment_intent_data={'metadata': { 'username': username, 'plan': plan['name'], 'price_id': stripe_price_id, 'subscribe': subscribe }},
          success_url=f'https://{DOMAIN_NAME}',
          cancel_url=f'https://{DOMAIN_NAME}',
        )
      session_id = session["id"]

      response["statusCode"] = 200
      response["body"] = json.dumps({"session_id": session_id})

    else:
      response["statusCode"] = 400
      response["body"] = json.dumps({"ERROR": "plan not available"})

  except Exception as err:
    print("ERR: ", err)
    response["statusCode"] = 500

  return response

