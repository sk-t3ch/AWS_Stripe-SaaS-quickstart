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
    Post Confirmation - this functions expects an Cognito post confirmation input event link.
    The user is initialised on the Free plan.
    """
    try:
        user_email = event['request']['userAttributes']['email']
        create_stripe_customer_resp = stripe.Customer.create(email=user_email)
        stripe_id = create_stripe_customer_resp['id']
        new_event = { "username": event["userName"], "plan": "Free", "subscribe": True }
        timestamp = int(time.time())

        response = client.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=f"UserManager_{new_event['username']}_{timestamp}_{os.urandom(4).hex()}",
            input=json.dumps(new_event)
        )
        execution_arn = response['executionArn']
        table.put_item(
            Item={
                'Id': new_event["username"],
                'Key': os.urandom(64).hex(),
                'Credits': 0,
                'Plan': new_event['plan'],
                'ManagerArn': execution_arn,
                'LastUpdate': timestamp,
                'StripeId': stripe_id,
            }
          )
        # TODO: send success email


    except Exception as err:
        # TODO: fail post confirmation event and send failure to email
        print("ERR: ", err)
    
    return event
