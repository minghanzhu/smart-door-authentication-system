import csv
import random
import string
import boto3
import time
import datetime
import calendar
import difflib

with open('accessKeys.csv') as f:
    lines = f.readlines()
aws_access_key_id = str(lines[1].split(",")[0])
aws_secret_access_key = str(lines[1].split(",")[1])


# https://www.geeksforgeeks.org/python-program-to-generate-one-time-password-otp/
def rand_pass(size):
    generate_pass = ''.join(
        [random.choice(string.ascii_uppercase +
                       string.ascii_lowercase +
                       string.digits)
         for n in range(size)]
    )
    return generate_pass


def add_otp_to_passcodes(table, visitor_id, otp, ttl):
    table.put_item(
        Item={
            "visitor_id": visitor_id,
            "OTP": otp,
            "ttl": ttl
        }
    )


def add_faceId_to_visitors(table, faceId, name, phoneNumber, objectKey, bucket, createdTimestamp):
    table.put_item(
        Item={
            'faceId': faceId,
            'name': name,
            'phoneNumber': phoneNumber,
            'photos': [
                {
                    'objectKey': objectKey,
                    'bucket': bucket,
                    'createdTimestamp': createdTimestamp,
                }
            ]
        }
    )


if __name__ == '__main__':

    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )

    dynamodb = session.resource('dynamodb')
    passcodes_table = dynamodb.Table('passcodes')

    for i in range(10):
        visitor_id = rand_pass(6)
        otp = rand_pass(10)
        ttl = calendar.timegm(time.gmtime()) + 300

        print(visitor_id, otp, ttl)
        add_otp_to_passcodes(passcodes_table, visitor_id, otp, ttl)

    # visitors_table = dynamodb.Table('visitors')
    #
    # add_faceId_to_visitors(table=visitors_table, faceId="{UUID}", name="Jane Doe", phoneNumber="+12345678901",
    #                        objectKey="my-photo.jpg", bucket="my-photo-bucket", createdTimestamp="2018-11-05T12:40:02")
