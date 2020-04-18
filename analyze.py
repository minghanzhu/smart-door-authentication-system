import boto3
from botocore.exceptions import ClientError
import pprint

with open('accessKeys.csv') as f:
    lines = f.readlines()
ACCESS_KEY = str(lines[1].split(",")[0])
SECRET_KEY = str(lines[1].split(",")[1])


def create_collection(collection_id):
    client = boto3.client('rekognition',
                          aws_access_key_id=ACCESS_KEY,
                          aws_secret_access_key=SECRET_KEY,
                          region_name="us-east-1"
                          )

    # Create a collection
    print('Creating collection:' + collection_id)
    response = client.create_collection(CollectionId=collection_id)
    print('Collection ARN: ' + response['CollectionArn'])
    print('Status code: ' + str(response['StatusCode']))
    print('Done...')


def delete_collection(collection_id):
    print('Attempting to delete collection ' + collection_id)
    client = boto3.client('rekognition',
                          aws_access_key_id=ACCESS_KEY,
                          aws_secret_access_key=SECRET_KEY,
                          region_name="us-east-2"
                          )
    status_code = 0
    try:
        response = client.delete_collection(CollectionId=collection_id)
        status_code = response['StatusCode']

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print('The collection ' + collection_id + ' was not found ')
        else:
            print('Error other than Not Found occurred: ' + e.response['Error']['Message'])
        status_code = e.response['ResponseMetadata']['HTTPStatusCode']
    return (status_code)


def list_collections():
    max_results = 2

    client = boto3.client('rekognition',
                          aws_access_key_id=ACCESS_KEY,
                          aws_secret_access_key=SECRET_KEY,
                          region_name="us-east-1"
                          )

    # Display all the collections
    print('Displaying collections...')
    response = client.list_collections(MaxResults=max_results)
    collection_count = 0
    done = False

    while done == False:
        collections = response['CollectionIds']

        for collection in collections:
            print(collection)
            collection_count += 1
        if 'NextToken' in response:
            nextToken = response['NextToken']
            response = client.list_collections(NextToken=nextToken, MaxResults=max_results)

        else:
            done = True

    return collection_count


def describe_collection(collection_id):
    print('Attempting to describe collection ' + collection_id)
    client = boto3.client('rekognition',
                          aws_access_key_id=ACCESS_KEY,
                          aws_secret_access_key=SECRET_KEY,
                          region_name="us-east-1"
                          )

    try:
        response = client.describe_collection(CollectionId=collection_id)
        print("Collection Arn: " + response['CollectionARN'])
        print("Face Count: " + str(response['FaceCount']))
        print("Face Model Version: " + response['FaceModelVersion'])
        print("Timestamp: " + str(response['CreationTimestamp']))


    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print('The collection ' + collection_id + ' was not found ')
        else:
            print('Error other than Not Found occurred: ' + e.response['Error']['Message'])
    print('Done...')


def add_faces_to_collection(bucket, photo, collection_id):
    client = boto3.client('rekognition',
                          aws_access_key_id=ACCESS_KEY,
                          aws_secret_access_key=SECRET_KEY,
                          region_name="us-east-1"
                          )

    response = client.index_faces(CollectionId=collection_id,
                                  Image={'S3Object': {'Bucket': bucket, 'Name': photo}},
                                  ExternalImageId=photo,
                                  MaxFaces=1,
                                  QualityFilter="AUTO",
                                  DetectionAttributes=['ALL'])

    print('Results for ' + photo)
    print('Faces indexed:')
    for faceRecord in response['FaceRecords']:
        print('  Face ID: ' + faceRecord['Face']['FaceId'])
        print('  Location: {}'.format(faceRecord['Face']['BoundingBox']))

    print('Faces not indexed:')
    for unindexedFace in response['UnindexedFaces']:
        print(' Location: {}'.format(unindexedFace['FaceDetail']['BoundingBox']))
        print(' Reasons:')
        for reason in unindexedFace['Reasons']:
            print('   ' + reason)
    return len(response['FaceRecords'])


def list_faces_in_collection(collection_id):
    # maxResults = 2
    faces_count = 0
    tokens = True

    client = boto3.client('rekognition',
                          aws_access_key_id=ACCESS_KEY,
                          aws_secret_access_key=SECRET_KEY,
                          region_name="us-east-1"
                          )

    response = client.list_faces(CollectionId=collection_id,
                                 # MaxResults=maxResults
                                 )

    print('Faces in collection ' + collection_id)

    while tokens:

        faces = response['Faces']

        for face in faces:
            print(face)
            faces_count += 1
        if 'NextToken' in response:
            nextToken = response['NextToken']
            response = client.list_faces(CollectionId=collection_id,
                                         NextToken=nextToken,
                                         # MaxResults=maxResults
                                         )
        else:
            tokens = False
    return faces_count


def search_face_in_collection(face_id, collection_id):
    threshold = 90
    # max_faces = 2
    client = boto3.client('rekognition',
                          aws_access_key_id=ACCESS_KEY,
                          aws_secret_access_key=SECRET_KEY,
                          region_name="us-east-1"
                          )

    response = client.search_faces(CollectionId=collection_id,
                                   FaceId=face_id,
                                   FaceMatchThreshold=threshold,
                                   # MaxFaces=max_faces
                                   )

    face_matches = response['FaceMatches']
    print('Matching faces')
    for match in face_matches:
        print('FaceId:' + match['Face']['FaceId'])
        print('Similarity: ' + "{:.2f}".format(match['Similarity']) + "%")
        print
    return len(face_matches)


def main():
    client = boto3.client('rekognition',
                          aws_access_key_id=ACCESS_KEY,
                          aws_secret_access_key=SECRET_KEY,
                          region_name="us-east-1"
                          )
    collection_id = 'Collection'

    '''Creating a Collection'''
    # create_collection(collection_id)

    '''Deleting a Collection'''
    # status_code = delete_collection(collection_id)
    # print('Status code: ' + str(status_code))

    '''Listing Collections'''
    # collection_count = list_collections()
    # print("collections: " + str(collection_count))

    '''Describing a Collection'''
    # describe_collection(collection_id=collection_id)

    '''Adding Faces to a Collection'''
    # bucket = 'visitor-photo-b1'
    # fileName = 'trump_2.jpg'
    # indexed_faces_count = add_faces_to_collection(bucket, fileName, collection_id)
    # print("Faces indexed count: " + str(indexed_faces_count))

    '''Listing Faces in a Collection'''
    # faces_count = list_faces_in_collection(collection_id)
    # print("faces count: " + str(faces_count))

    '''Searching for a Face Using Its Face ID'''
    # face_id = 'b738b637-a44b-460c-bf80-2106ca073aa6'
    # faces = []
    # faces.append(face_id)
    #
    # faces_count = search_face_in_collection(face_id, collection_id)
    # print("faces found: " + str(faces_count))

    '''Searching for a Face Using an Image'''
    # bucket = 'visitor-photo-b1'
    # fileName = 'trump_3.jpg'
    # threshold = 70
    # # maxFaces = 2
    #
    # response = client.search_faces_by_image(CollectionId=collection_id,
    #                                         Image={'S3Object': {'Bucket': bucket, 'Name': fileName}},
    #                                         FaceMatchThreshold=threshold,
    #                                         # MaxFaces=maxFaces
    #                                         )
    #
    # faceMatches = response['FaceMatches']
    # print('Matching faces')
    # for match in faceMatches:
    #     print('FaceId: ' + match['Face']['FaceId'])
    #     print('Similarity: ' + "{:.2f}".format(match['Similarity']) + "%")

    '''Creates an Amazon Rekognition stream processor that you can use to detect and recognize faces in a streaming 
    video.'''
    # response = client.create_stream_processor(
    #     Input={
    #         'KinesisVideoStream': {
    #             'Arn': 'arn:aws:kinesisvideo:us-east-1:288120673821:stream/KVS1/1586988432719'
    #         }
    #     },
    #
    #     Output={
    #         'KinesisDataStream': {
    #             'Arn': 'arn:aws:kinesis:us-east-1:288120673821:stream/KDS1'
    #         }
    #     },
    #
    #     Name='RekognitionStreamProcessor',
    #
    #     Settings={
    #         'FaceSearch': {
    #             'CollectionId': collection_id,
    #             'FaceMatchThreshold': 70
    #         }
    #     },
    #     RoleArn='arn:aws:iam::288120673821:role/Rekognition'
    # )
    # print(response)

    '''Provides information about a stream processor'''
    response = client.describe_stream_processor(
        Name='RekognitionStreamProcessor'
    )
    pprint.pprint(response)

    # '''Starts processing a stream processor'''
    # response = client.start_stream_processor(
    #     Name='RekognitionStreamProcessor'
    # )
    # pprint.pprint(response)
    #
    # '''Stops a running stream processor'''
    # response = client.stop_stream_processor(
    #     Name='RekognitionStreamProcessor'
    # )
    # pprint.pprint(response)


if __name__ == "__main__":
    main()
