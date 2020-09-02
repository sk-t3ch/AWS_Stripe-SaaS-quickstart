import stripe
import json
import boto3
import os
import time

PRODUCT_TABLE_NAME = 'tables-ProductTable-12MIQBB89ICZ'
STRIPE_SECRET_KEY = "sk_test_51HKlevJAV1tclqKuuFvkoHoOoygiavnUNDet2HXnyXd2bsNVCzvxkW2bNAA8HivobXs5idcpa5VCzK0b90wub2h100rsOtHlun"
# boto3.setup_default_session(profile_name='sk')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(PRODUCT_TABLE_NAME)
stripe.api_key = STRIPE_SECRET_KEY

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

