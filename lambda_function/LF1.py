import time
import boto3
import string
import json
import base64
from boto3.dynamodb.conditions import Key
import sys
import random
import calendar

sys.path.insert(1, '/opt')
import cv2

with open('accessKeys.csv') as f:
    lines = f.readlines()
aws_access_key_id = str(lines[1].split(",")[0])
aws_secret_access_key = str(lines[1].split(",")[1])

dynamodb = boto3.resource('dynamodb')
db1_table = dynamodb.Table('passcodes')
db2_table = dynamodb.Table('visitors')


def lambda_handler(event, context):
    known, face_id, photo_info = if_known_face(event)
    print(known, face_id, photo_info)

    if known:
        print("A Known Face")
        response = db2_table.query(
            KeyConditionExpression=Key('faceId').eq(face_id)
        )
        print(response)
        phone_number = response['Items'][0]['phoneNumber']
        photos = response['Items'][0]['photos']
        updateVisitorPhoto(photos, face_id, photo_info)
        make_otp(face_id, phone_number)
    else:
        print("An Unknown Face")
        requestPermission(photo_info)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }


def if_known_face(event):
    for record in event['Records']:
        print(record)
        # Kinesis data is base64 encoded so decode here
        payload = base64.b64decode(record["kinesis"]["data"])

        data_json = json.loads(payload.decode('utf8'))
        # print(data_json)
        face_id = ""
        flag = False
        fragment_number = data_json['InputInformation']['KinesisVideo']['FragmentNumber']

        for face in data_json['FaceSearchResponse']:
            print(face)
            flag = True
            for matchedFace in face['MatchedFaces']:
                print(matchedFace)
                face_id = matchedFace['Face']['FaceId']
                break

        print("face_id:" + face_id + " fragment_number:" + fragment_number)

        if face_id != "" and flag:
            return True, face_id, get_picture(fragment_number)
        else:
            return False, face_id, get_picture(fragment_number)


def get_picture(ids):
    stream_arn = "arn:aws:kinesisvideo:us-east-1:447013652281:stream/KVS1/1587001515341"
    kvs = boto3.client("kinesisvideo")

    response = kvs.get_data_endpoint(
        StreamARN=stream_arn,
        APIName='GET_MEDIA'
    )

    endpoint_url_string = response['DataEndpoint']

    print("get endpoint:" + endpoint_url_string)

    streaming_client = boto3.client(
        'kinesis-video-media',
        endpoint_url=endpoint_url_string,
    )

    kinesis_stream = streaming_client.get_media(
        StreamARN=stream_arn,
        StartSelector={'StartSelectorType': 'NOW'},
    )

    stream_payload = kinesis_stream['Payload']
    print("get video")

    s3 = boto3.resource("s3")
    print("start reading video")
    data = stream_payload.read(512 * 1024)
    print("end reading video")

    f = open("/tmp/temp.mp4", "wb+")
    f.write(data)
    f.close()
    print("write video")

    cap = cv2.VideoCapture('/tmp/temp.mp4')
    print("open video")

    i = 0
    while (cap.isOpened()):
        ret, frame = cap.read()
        if ret == False:
            break
        i += 1
        if i == 1:
            cv2.imwrite('/tmp/temp.jpg', frame)
            print("write picture")
            s3.Bucket("visitor-photo").upload_file("/tmp/temp.jpg", ids + ".jpg")
            print("send pictrue")
            break

    cap.release()
    cv2.destroyAllWindows()
    return ids + ".jpg"


def storeNewVisitor(face_id, photo_info):
    try:
        db2_table.put_item(
            Item={
                'faceId': face_id,
                'name': 'None',
                'phoneNumber': 'None',
                'photos': [photo_info]
            }
        )
    except Exception as e:
        print('Exception: ', e)
        return False
    return True


def updateVisitorPhoto(photos, face_id, photo_info):
    try:
        db2_table.update_item(
            Key={
                'faceId': face_id
            },
            UpdateExpression="set #photos = :photos",
            ExpressionAttributeValues={
                ':photos': photos + [photo_info]

            },
            ExpressionAttributeNames={
                "#photos": "photos"
            }
        )
    except Exception as e:
        print('Exception: ', e)


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
    # generate OTP
    otp = rand_pass(9)
    ttl = calendar.timegm(time.gmtime()) + 300

    response = db1_table.query(KeyConditionExpression=Key('visitor_id').eq(face_id))
    print(response)
    if len(response['Items']) == 0:
        try:
            print(otp)
            db1_table.put_item(Item={
                'visitor_id': face_id,
                'OTP': otp,
                'ttl': ttl
            }
            )
        except Exception as e:
            print('Exception: ', e)

        # Send OPT to user through SNS
        msg = 'OTP: ' + otp
        client = boto3.client('sns',
                              aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key)
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


def requestPermission(photo_info):
    # Send to the photo and the comfirmation link to the owner through SNS
    photo_link = 'https://visitor-photo.s3.amazonaws.com/' + photo_info
    confirmation_link = 'https://cloudcomputinghw2.s3.amazonaws.com/WP1/webPage_1.html?faceId=' + photo_info
    client = boto3.client('sns',
                          aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key)
    try:
        client.publish(
            PhoneNumber='+13477220191',
            Message='photo link: ' + photo_link + '\nconfirmation link: ' + confirmation_link,
            MessageAttributes={
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': 'Transactional'
                }
            }
        )
    except Exception as e:
        print('Exception: ', e)
