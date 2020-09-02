import boto3
import os
import time
import json
import stripe
      
STATE_MACHINE_ARN = os.environ['STATE_MACHINE_ARN']
dynamodb = boto3.resource('dynamodb')
client = boto3.client('stepfunctions')
USER_TABLE_NAME = os.environ['USER_TABLE_NAME']
user_table = dynamodb.Table(USER_TABLE_NAME)

# TODO: ssm keys
STRIPE_SECRET_KEY = os.environ['STRIPE_SECRET_KEY']
stripe.api_key = STRIPE_SECRET_KEY
STRIPE_WEB_HOOK_SECRET = os.environ['STRIPE_WEB_HOOK_SECRET']


def handler(event, context):
  """
  Stripe Web Hook - This function expects a GET request from stripe containing info from the successful payment event.
  A user management state machine is started to process the user purchase.
  """
  # TODO: only accept stripe origin
  response = {
    "headers": {
      'Access-Control-Allow-Origin': '*'
    }
  }

  try:
    payload = event["body"]
    sig_header = event['headers']['Stripe-Signature']
    stripe_event = stripe.Webhook.construct_event(
      payload, sig_header, STRIPE_WEB_HOOK_SECRET
    )

    if stripe_event['type'] == 'charge.succeeded':
      # TODO: HANDLE DUPLICATE EVENTS TRYING TO ADD CREDS
      print(stripe_event)
      invoice_id = stripe_event['data']['object']['invoice']
      if invoice_id:
        stripe_invoice = stripe.Invoice.retrieve(invoice_id)
        meta_data = stripe_invoice["lines"]["data"][0]["metadata"]
      else:
        meta_data = stripe_event['data']['object']['metadata']
      username = meta_data['username']
      plan = meta_data['plan']
      subscribe = True if meta_data['subscribe'] == "True" else False

      user_table_query_resp = user_table.get_item( Key={ 'Id': username } )
      user = user_table_query_resp['Item']
      if (subscribe and user['Plan'] == 'Free'):
        client.stop_execution(executionArn=user['ManagerArn'])
      else:
        stripe_user_id = user['StripeId']
        stripe_customer = stripe.Customer.retrieve(stripe_user_id, expand=['subscriptions'])
        stripe_subscriptions = stripe_customer['subscriptions']['data']
        for stripe_subscription in stripe_subscriptions:
          stripe.Subscription.delete(stripe_subscription['id'])

      new_event = { "username": username, "plan": plan, 'subscribe': subscribe }
      timestamp = int(time.time())

      user_manager_start_resp = client.start_execution(
          stateMachineArn=STATE_MACHINE_ARN,
          name=f"UserManager_{new_event['username']}_{timestamp}_{os.urandom(4).hex()}",
          input=json.dumps(new_event)
      )
      execution_arn = user_manager_start_resp['executionArn']
      user_update_resp = user_table.update_item(
          Key={ 'Id': username },
          UpdateExpression='SET #d = :d, #p = :p',
          ExpressionAttributeValues={
              ':d': timestamp,
              ':p': plan if subscribe else user['Plan'],
          },
          ExpressionAttributeNames={
              '#d': 'LastUpdate',
              '#p': 'Plan',
          },
          ReturnValues='UPDATED_NEW'
      )

      response["statusCode"] = 200


  except Exception as e:
    print("ERRR", e)    
    response["statusCode"] = 500

  return response
