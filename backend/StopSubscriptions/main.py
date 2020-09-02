import boto3
import os
import time
import json
import stripe
      
dynamodb = boto3.resource('dynamodb')
client = boto3.client('stepfunctions')
TABLE_NAME = os.environ['TABLE_NAME']
STATE_MACHINE_ARN = os.environ['STATE_MACHINE_ARN']
table = dynamodb.Table(TABLE_NAME)

# TODO: ssm keys
STRIPE_SECRET_KEY = os.environ['STRIPE_SECRET_KEY']
stripe.api_key = STRIPE_SECRET_KEY

def handler(event, context):
  """
  Stop Subscriptions - this functions expects a username.
  All subscriptions attached to stripe account of this user are cancelled.
  """
  # TODO: restrict access to site
  response = {
    "headers": {
      'Access-Control-Allow-Origin': '*'
    }
  }

  try:
    username = event["requestContext"]["authorizer"]["claims"]["cognito:username"]
    table_query_resp = table.get_item(Key={'Id':username})
    user =  table_query_resp["Item"]
    stripe_user_id = user['StripeId']
    stripe_customer = stripe.Customer.retrieve(stripe_user_id, expand=['subscriptions'])
    stripe_subscriptions = stripe_customer['subscriptions']['data']
    for stripe_subscription in stripe_subscriptions:
      stripe.Subscription.delete(stripe_subscription['id'])

    
    new_event = { 'username': username, 'plan': 'Free', 'subscribe': True }
    timestamp = int(time.time())
    state_machine_start_resp = client.start_execution(
      stateMachineArn=STATE_MACHINE_ARN,
      name=f"UserManager_{new_event['username']}_{timestamp}_{os.urandom(4).hex()}",
      input=json.dumps(new_event)
      )
    execution_arn = state_machine_start_resp['executionArn']
    table_update_resp = table.update_item(
        Key={ 'Id': user['Id'] },
        UpdateExpression='SET #p = :p, #m = :m, #l = :l',
        ExpressionAttributeValues={
            ':p': 'Free',
            ':l': timestamp,
            ':m': execution_arn
        },
        ExpressionAttributeNames={
            '#p': 'Plan',
            '#l': 'LastUpdate',
            '#m': 'ManagerArn'
        },
        ReturnValues='ALL_NEW'
      )
    user = table_update_resp['Attributes']

    filtered_user = {"user": {
        "credits": int(user.get("Credits", 0)),
        "key": user.get("Key", None),
        "lastUpdate": int(user.get("LastUpdate", 0)),
        "plan": user.get("Plan", None),
        "subscribe": user.get("Subscribe", False),
      }
    }

    response["statusCode"] = 200
    response["body"] = json.dumps(filtered_user)

    # TODO: email user that all subscriptions have stopped succesfully



  except Exception as err:
    print("ERR: ", err)
    response["statusCode"] = 500

  return response