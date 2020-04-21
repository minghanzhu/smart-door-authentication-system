import json
import boto3
import secrets
import string
from boto3.dynamodb.conditions import Key
import time
import random
import calendar

dynamodb = boto3.resource('dynamodb')
client = boto3.client('rekognition')
db1_table = dynamodb.Table('passcodes')


def lambda_handler(event, context):
    print(event)
    imgKey = event['faceId']
    name = event['name']
    phoneNumber = "+1" + event['phoneNumber']
    faceId = get_faceId(imgKey, name)

    if (name != 'N/A' and phoneNumber != 'N/A'):
        response = storeUserInfo(faceId, name, phoneNumber, imgKey)
        make_otp(faceId, phoneNumber)
        return {
            'message': json.dumps(response)
        }
    else:
        return {
            'message': json.dumps('Alright, we got it, thank you for your time!')
        }


def get_faceId(imgKey, name):
    response = client.index_faces(
        CollectionId='Collection_0',
        Image={
            'S3Object': {
                'Bucket': 'visitor-photo',
                'Name': imgKey
            }
        },
        ExternalImageId=name,
        DetectionAttributes=[
            'DEFAULT',
        ],
        MaxFaces=1,
        QualityFilter='AUTO'
    )
    return response['FaceRecords'][0]['Face']['FaceId']


def storeUserInfo(faceId, name, phone_number, imgKey):
    # put in db2
    db2_table = dynamodb.Table('visitors')
    photo_info = {
        'objectKey': imgKey,
        'bucket': 'visitor-photo',
        'createdTimestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    }
    try:
        db2_table.put_item(
            Item={
                'faceId': faceId,
                'name': name,
                'phoneNumber': phone_number,
                'photos': [photo_info]
            }
        )
    except Exception as e:
        print('Exception: ', e)
        return False
    return "Ok, We have stored the visitor's information, thank you!"


# https://www.geeksforgeeks.org/python-program-to-generate-one-time-password-otp/
def rand_pass(size):
    generate_pass = ''.join(
        [random.choice(string.ascii_uppercase +
                       string.ascii_lowercase +
                       string.digits)
         for n in range(size)]
    )
    return generate_pass


def make_otp(face_id, phone_number):
    otp = rand_pass(9)
    ttl = calendar.timegm(time.gmtime()) + 300

    # put OTP into db1
    response = db1_table.query(KeyConditionExpression=Key('visitor_id').eq(face_id))
    print(response)
    if len(response['Items']) == 0:
        try:
            print(otp)
            db1_table.put_item(
                Item={
                    'visitor_id': face_id,
                    'OTP': otp,
                    'ttl': ttl
                }
            )
        except Exception as e:
            print('Exception: ', e)
            return False

        msg = 'OTP: ' + otp
        client = boto3.client('sns',
                              aws_access_key_id='',
                              aws_secret_access_key='')
        try:
            print("sns")
            print(phone_number)

            client.publish(
                PhoneNumber=phone_number,
                Message=msg,
                MessageAttributes={
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )
        except Exception as e:
            print('Exception: ', e)
