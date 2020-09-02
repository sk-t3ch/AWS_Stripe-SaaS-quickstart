import boto3
import os
import time
import datetime
      
dynamodb = boto3.resource('dynamodb')
USER_TABLE_NAME = os.environ['USER_TABLE_NAME']
user_table = dynamodb.Table(USER_TABLE_NAME)
PRODUCT_TABLE_NAME = os.environ['PRODUCT_TABLE_NAME']
product_table = dynamodb.Table(PRODUCT_TABLE_NAME)

def handler(event, context):
    """
    Add Plan - This function expects an input event such as {'username': '1234', 'plan': 'Power', 'subscribe': True }
    The number of credits that the plan defines are added to the User's account
    If the user is on the Free plan then the process will loop using 'subscription_end' field configure the wait step 
    """
    response = { **event }
    try:
        user_table_query_resp = user_table.get_item(Key={'Id': event['username']})
        user = user_table_query_resp.get('Item', False)
        product_table_query_resp = product_table.get_item(Key={'name': event['plan']}) 
        new_plan = product_table_query_resp.get('Item', False)
        new_credits = int(user['Credits']) + new_plan['credits']

        if (user and new_plan):
            now = datetime.datetime.now()

            user_update_resp = user_table.update_item(
                Key={ 'Id': user['Id'] },
                UpdateExpression='SET #p = :p, #c = :c, #l = :l',
                ExpressionAttributeValues={
                    ':p': event['plan'] if event['subscribe'] else user['Plan'],
                    ':c': new_credits,
                    ':l': int(now.timestamp())
                },
                ExpressionAttributeNames={
                    '#p': 'Plan',
                    '#c': 'Credits',
                    '#l': 'LastUpdate'
                },
                ReturnValues='UPDATED_NEW'
            )

            if event['plan'] == 'Free':
                week_interval = datetime.timedelta(seconds=7*24*60*60)
                end_date = (now + week_interval).replace(microsecond=0).astimezone()
                response['subscription_end'] =  end_date.isoformat()


    except Exception as err:
        # TODO: send this error to next step for email - username, plan and time
        print('ERR: ', err)

    return response

