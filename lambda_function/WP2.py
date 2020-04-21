import json
import boto3
from boto3.dynamodb.conditions import Key

dynamoDB = boto3.resource('dynamodb')


def queryID(otp):
    db1_table = dynamoDB.Table('passcodes')
    id = db1_table.scan(
        FilterExpression=Key('OTP').eq(otp)
    )
    if (id['Items'] == []):
        return None
    print(id['Items'])
    return id['Items'][0]['visitor_id']


def queryInfo(faceId):
    db2_table = dynamoDB.Table('visitors')
    person = db2_table.query(
        KeyConditionExpression=Key('faceId').eq(faceId)
    )
    return person['Items'][0]['name']


def lambda_handler(event, context):
    otp = event['OTP']
    faceId = queryID(otp)

    if (faceId == None):
        return {
            'message': json.dumps('Permission denied, refresh to retry!')
        }

    name = queryInfo(faceId)
    respond_msg = "Door opens, welcome " + name + "!"
    return {
        'message': json.dumps(respond_msg)
    }
