import boto3
import os
import json

      
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ['TABLE_NAME']
table = dynamodb.Table(TABLE_NAME)

def handler(event, context):
  # TODO: restrict access origin to site 
  response = {
    "headers": {
      'Access-Control-Allow-Origin': '*'
    }
  }
  key = "UNKNOWN"

  try:
    username = event["requestContext"]["authorizer"]["claims"]["cognito:username"]
    key = os.urandom(64).hex()
    
    keyUpdateResp = table.update_item(
      Key={'Id': username },
      UpdateExpression="set #k = :key",
      ExpressionAttributeNames={ "#k": "Key"},
      ExpressionAttributeValues={':key': key},
      ReturnValues="UPDATED_NEW"
    )
        
    new_key = keyUpdateResp["Attributes"]["Key"]

    response["statusCode"] = 200
    response["body"] = json.dumps({"key": new_key})
    
  except Exception as err:
    print("ERR: ", err)
    response["statusCode"] = 500

  return response
