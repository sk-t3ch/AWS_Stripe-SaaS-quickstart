# 💸 Pay Me: Quickstart for creating a SaaS pt.2 — Stripe Payments

Creating a SaaS solution is fun, but creating a payment system can be a minefield. In this article, I demonstrate how to create a serverless SaaS on AWS. It uses the Stripe API and Vue-Checkout library to perform payments and manages users with Cognito, building on the architecture from part 1. Check out the live demo 💽.

![](https://cdn-images-1.medium.com/max/4000/1*9RH_PC5EM5l0fM9wnEE97Q.png)

Payments systems are a complex but necessary part of running a SaaS. Turning to a payment service side-steps most of the complexity and responsibility, but usually costs a percentage or flat fee for each transaction. [Stripe](https://stripe.com/) offers payment system solution and charges 1.4%+20p for European cards and 2.9%+20p for for non-European cards per transaction. Stripe also has other useful features such as:

* customer management, including storing payment details

* manage products and prices

* create payments and subscriptions

* dashboards and insights

In this article, I will demonstrate integrating Stripe’s payment solution and how to store user details, make subscriptions and instant payments. In a previous article, I demonstrated how to create a SaaS user management application which allows users to manage their API key and monitor usage.
[**🚫 Users Only: Quickstart for creating a SaaS pt. 1 — User Management
**M*anaging users and API keys is a necessary task for creating a Software as a Service (SaaS). In this article, I…m*edium.com](https://medium.com/@t3chflicks/users-only-quickstart-for-creating-a-saas-pt-1-user-management-3ca7e3332565)

I want to limit the number of requests a user can make per month and scale that with an amount of money that would make the SaaS profitable. I have chosen to use credits instead of number of requests to open up the possibility of having multiple services which might be more costly to run. This also allows you to charge multiple credits.

I have divided plans up into three tiers which can be subscribed to or as pay-as-you-go:

* *Free* — 50 Credits per week

* *Basic* —1,000 Credits per month

* *Power* — 100,000 Credits per month
> *In a future article, I hope to investigate the cost of the architecture per user to determine a fair price for the service.*

Stripe offers both the ability to make instant payments and subscriptions. Your products and prices must be stored on the Stripe service and when a purchase is successfully completed, Stripe will notify you using a web hook that you define. This web hook is called on subscription payment being successful too.

The architecture extends upon the previous User Manager App with another DynamoDB table to store products, a checkout function on the User API, a Stripe web hook API, and a State machine to manage users’ credit.

![SaaS Architecture Diagram](https://cdn-images-1.medium.com/max/2056/1*lvDDAutc-VL-sFUzYZxCng.png)*

SaaS Architecture Diagram*
> # [The full code for this project can be found here ☁️](https://github.com/sk-t3ch/AWS_Stripe-SaaS-quickstart)
> # [The live demo can be found here 💽](https://saas-app.t3chflicks.org)

![Video of User buying subscription with SaaS App](https://cdn-images-1.medium.com/max/2000/1*VJ5IjcLZ8taS1JKt0Gib_g.gif)*

Video of User buying subscription with SaaS App*

## Let’s Build! 🔩

## Backend

### Credit

User credit is managed using a [State Machine](https://aws.amazon.com/step-functions). The Cognito post-confirmation hook trigger a Lambda to create a user and begin an execution of the State Machine with the *Free *plan.

![User Management State Machine](https://cdn-images-1.medium.com/max/2000/1*vwxGotYkwlGmvkZD6cwalA.png)*

User Management State Machine*

State Machines offer the ability to wait a specific amount of time and this does not cost. This allows us to periodically add credits to users on the *Free* plan. This is a requirement as this plan is not purchased and therefore cannot use the Stripe web hook as a trigger to add credits (see later).

Using a State Machines to construct flows means that extensions are easily added, such as sending email alerts. The cost of a [standard](https://aws.amazon.com/step-functions/pricing/) State Machine is $0.025 per thousand state transitions. In the above State Machine, a free user would cost $0.025/1000 * 3 = $0.000075 per User per week — not including the Lambda fees. There is also a limit of 25,000 executions at a time.

### Product Table

Stripe allows you to create products which can have multiple prices. This is particularly useful for SaaS where you may offer the same product as an instant buy or recurring subscription.

I have defined the products in a JSON file and attempted to sync this details with both Stripe and a DynamoDB table using the following script:

    import stripe
    import json
    import boto3
    import os
    import time

    dynamodb = boto3.resource('dynamodb')
    TABLE_NAME = '<YOUR_PRODUCTS_TABLE_NAME>'
    table = dynamodb.Table(TABLE_NAME)
    stripe.api_key = "<YOUR_SECRET_KEY>"

    def get_plans():
        with open('./plans.json', 'r') as file:
            plans = json.loads(file.read())
        return plans

    def sync_stripe_product(plan):
        if 'product_id' in plan.keys():
            print("Stripe Plan exists: getting item")
            get_stripe_product_resp = stripe.Product.retrieve(plan['product_id'])
            stripe_product = get_stripe_product_resp['metadata']

            instant_prices = stripe.Price.list(
                active=True,
                lookup_keys=[f"{plan['name']}_instant_price"]
            )
            print(instant_prices)
            current_instant_price = instant_prices['data'][0]
            instant_stripe_plan = {
                **plan,
                "product_id": current_instant_price['product'],
                "cost": current_instant_price['unit_amount']
            }
            if plan != instant_stripe_plan:
                print("Stripe Plan instant price is different: updating item")
                update_stripe_price_resp = stripe.Price.modify(
                    current_instant_price['id'],
                    active=False
                )
                create_stripe_price_resp = stripe.Price.create(
                    product=plan['product_id'],
                    unit_amount=plan['cost'],
                    currency='gbp',
                    lookup_key=f"{plan['name']}_instant_price",
                    transfer_lookup_key=True
                )
            sub_prices = stripe.Price.list(
                active=True,
                lookup_keys=[f"{plan['name']}_monthly_price"],
            )
            print(sub_prices)
            current_sub_price = sub_prices['data'][0]

            sub_stripe_plan = {
                **plan,
                "product_id": current_sub_price['product'],
                "cost": current_sub_price['unit_amount']
            }
            if plan != sub_stripe_plan:
                print("Stripe Plan sub price is different: updating item")
                update_stripe_price_resp = stripe.Price.modify(
                    current_sub_price['id'],
                    active=False
                )
                create_stripe_price_resp = stripe.Price.create(
                    product=plan['product_id'],
                    unit_amount=plan['cost'],
                    currency='gbp',
                    recurring={
                    'interval': 'month',
                    },
                    lookup_key=f"{plan['name']}_monthly_price",
                    transfer_lookup_key=True
                )
            
        else:
            print("Stripe Plan does not exist: creating item")
            create_stripe_product_resp = stripe.Product.create(name=plan['name'])
            plan['product_id'] = create_stripe_product_resp["id"]
            # create addon
            create_stripe_price_resp = stripe.Price.create(
                product=plan['product_id'],
                unit_amount=plan['cost'],
                currency='gbp',
                lookup_key=f"{plan['name']}_instant_price",
            )
            # create subscription
            create_stripe_price_resp = stripe.Price.create(
                product=plan['product_id'],
                unit_amount=plan['cost'],
                currency='gbp',
                recurring={
                    'interval': 'month',
                },
                lookup_key=f"{plan['name']}_monthly_price"
            )
            # maybe check response

    def sync_dynamo_product(plan):
        get_dynamo_product_resp = table.get_item(Key={'name':plan['name']})
        dynamo_product = get_dynamo_product_resp.get('Item', False)
        if dynamo_product:
            if plan != dynamo_product:
                print("Dynamo Plan is different: updating item")
                update_dynamo_product_resp = table.put_item(Item={ **plan })
                # maybe check response
        else:
            print("Dynamo Plan does not exist: creating item")
            create_stripe_product_resp = table.put_item(Item={ **plan })
            # maybe check response

    def store_updates(plans):
        with open('./plans.json', 'w') as file:
            file.write(json.dumps(plans))

    def main():
        PLAN_DB = get_plans()
        for plan in PLAN_DB:
            print(plan)
            try:
                if plan['name'] != 'Free':
                    sync_stripe_product(plan)
                sync_dynamo_product(plan)
            except Exception as err:
                print("ERROR: ", err)
        store_updates(PLAN_DB)

    if __name__ == '__main__':
        main()

### User API

The previous User Management system from [part 1](https://medium.com/@t3chflicks/users-only-quickstart-for-creating-a-saas-pt-1-user-management-3ca7e3332565) has:

`/generate-key` — this regenerates the User’s API key

`/user` — returns details like API key, last Update time, and subscription Plan

This is extended with:

`/create-session`

`/cancel-subscriptions`

### Create Session

The Stripe-checkout frontend component requires a session-Id to initiate the payment sequence.


When the user selects a product on the frontend, a request is sent to the `/create-session` endpoint where following function is run:

    import boto3
    import os
    import json
    import stripe
        
    dynamodb = boto3.resource('dynamodb')
    PRODUCT_TABLE_NAME = os.environ['PRODUCT_TABLE_NAME']
    product_table = dynamodb.Table(PRODUCT_TABLE_NAME)
    USER_TABLE_NAME = os.environ['USER_TABLE_NAME']
    user_table = dynamodb.Table(USER_TABLE_NAME)

    STRIPE_SECRET_KEY = os.environ['STRIPE_SECRET_KEY']
    stripe.api_key = STRIPE_SECRET_KEY

    def handler(event, context):
    print(event)
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
            success_url='http://localhost:8080',
            cancel_url='http://localhost:8080',
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
            success_url='http://localhost:8080',
            cancel_url='http://localhost:8080',
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


When creating a session, you can also attach `meta-data`. This data is accessible on the resultant success object of the payment sent by Stripe to your web hook.

### Cancel Subscriptions

Users should be able to cancel their subscription to the SaaS at any time. In this example, selecting the *Free* plan in the frontend cancels all other subscriptions. This is achieved simply by referencing a customer id on a cancel call to Stipe.

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

### WebHook API

Stripe sends transaction events to a web hook which you must create and define using the Stripe API:

    import stripe

    STRIPE_SECRET_KEY = "<your_secret_key>"
    stripe.api_key = STRIPE_SECRET_KEY

    URL = "<your_web_hook_api_address" + "/payment-success"

    create_web_hook_resp = stripe.WebhookEndpoint.create(
    url=URL,
    enabled_events=[
        "charge.succeeded",
        ],
    )
    secret = create_web_hook_resp["secret"]
    print(f"The web hook created for {URL} has a secret={secret}")


Once you have defined the web hook, the secret is used in the following Lambda function which processes the successful charge events:

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

    STRIPE_SECRET_KEY = os.environ['STRIPE_SECRET_KEY']
    stripe.api_key = STRIPE_SECRET_KEY
    STRIPE_WEB_HOOK_SECRET = os.environ['STRIPE_WEB_HOOK_SECRET']

    def handler(event, context):
    print(event)
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


Again, I have added open CORS whilst developing. For security, these should been locked down so that only Stripe can call this API.

### Test API

The test service API still uses the user’s API key for a query on a GSI of the User table to get the username and credit count. The credit field is decremented every time a request is made to the service.

    import boto3
    from boto3.dynamodb.conditions import Key
    import os
    import json

    dynamodb = boto3.resource('dynamodb')
    TABLE_NAME = os.environ['TABLE_NAME']
    table = dynamodb.Table(TABLE_NAME)


    def handler(event, context):
        """
        Test Key - this functions expects an API key.
        The API key is searched for on the user table secondary index and credit decremented.
        """
        response = {
            'isBase64Encoded': False,
            'headers': {
                'access-control-allow-methods': 'POST',
                'Access-Control-Allow-Origin': '*',
                'access-control-allow-headers': 'Content-Type, Access-Control-Allow-Headers'
            },
            'statusCode': 200
        }
        if event['httpMethod'] == 'OPTIONS':
            return response
        try:
            count = "UNKNOWN"
            key = json.loads(event["body"]).get("key")
            table_query_resp = table.query(
                IndexName='KeyLookup',
                KeyConditionExpression=Key('Key').eq(key)
            )
            item = table_query_resp["Items"][0]
            count = item["Credits"]
            id = item["Id"]
            if(count < 1):  
                response["body"] = json.dumps({"ERROR": "NO CREDITS REMAINING"})
                response["statusCode"] = 400
            
            else:
                table_update_resp = table.update_item(
                    Key={
                        'Id': id,
                    },
                    UpdateExpression="set #c = #c -:num",
                    ExpressionAttributeNames={
                        "#c": "Credits"
                    },
                    ExpressionAttributeValues={
                        ':num': 1,
                    },
                    ReturnValues="UPDATED_NEW"
                )

                count = table_update_resp["Attributes"]["Credits"]
                response["body"] = json.dumps({"CREDITS": int(count)})
                response["statusCode"] = 200

        except Exception as err:
            print("ERR: ", err)
            response["statusCode"] = 500

        return response

## Frontend

The frontend is created using Vue JS with the AWS Amplify package and components — this is described in the pevious User Manager App from [part 1](https://medium.com/@t3chflicks/users-only-quickstart-for-creating-a-saas-pt-1-user-management-3ca7e3332565). Here, we add the ability to make payments.

### Stripe Checkout

Stripe Checkout is a payment page hosted by Stripe that users are redirected to in order to complete their purchase. [Vue-Stripe-Checkout](https://github.com/jofftiquez/vue-stripe-checkout) is a plugin that means Stripe Checkout can be added in just a few lines:

    <stripe-checkout
     ref="sessionRef"
     :pk="publishableKey"
     :session-id="sessionId"
     successUrl="http://localhost:8080#success"
     cancelUrl="http://localhost:8080#cancel"
     >
        <template slot="checkout-button">
            <v-btn  @click="$refs.sessionRef.redirectToCheckout()" v- show="!isLoadingSession">Pay</v-btn>
        </template>
    </stripe-checkout>

The pricing page for this site looks like this:

![SaaS Frontend Vue Checkout Component](https://cdn-images-1.medium.com/max/3200/1*9VJ3WDeUNpWT6iqwW3nwFQ.png)*

SaaS Frontend Vue Checkout Component*

When the user clicks pay they are redirected to the Stripe page which looks like this:

![Stripe Checkout Page for Power Subscription](https://cdn-images-1.medium.com/max/3200/1*XvZoBgzv26uTmqW0xkBM3A.png)*

Stripe Checkout Page for Power Subscription*

### After Thoughts

This Architecture is a basis for creating your own SaaS. It would be great to extend this SaaS to cover:

* processing unsuccessful subscription payments

* connecting to social identity providers

## Thanks for reading

I hope you have enjoyed this article. If you like the style, check out [T3chFlicks.org](https://t3chflicks.org/Projects/aws-saas-quickstart) for more tech-focused educational content ([YouTube](https://www.youtube.com/channel/UC0eSD-tdiJMI5GQTkMmZ-6w), [Instagram](https://www.instagram.com/t3chflicks/), [Facebook](https://www.facebook.com/t3chflicks), [Twitter](https://twitter.com/t3chflicks)).
> # [The full code for this project can be found here ☁️](https://github.com/sk-t3ch/AWS_Stripe-SaaS-quickstart)
> # [The live demo can be found here ⚡](https://saas-app.t3chflicks.org)



Resources:

* [https://chaosgears.com/lets-start-developing-using-vue-and-amplify/](https://chaosgears.com/lets-start-developing-using-vue-and-amplify/)

* [https://docs.amplify.aws/lib/auth/getting-started/q/platform/js](https://docs.amplify.aws/lib/auth/getting-started/q/platform/js)

* [https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification.html](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification.html)

* [https://www.youtube.com/watch?v=7dQZLY9-wL0](https://www.youtube.com/watch?v=7dQZLY9-wL0)