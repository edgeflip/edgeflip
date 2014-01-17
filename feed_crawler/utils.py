import boto
from boto.s3 import bucket, connection


class BucketManager(bucket.Bucket):

    def get_or_create_key(self, key_name):
        key = self.get_key(key_name)
        if key:
            return key, False
        else:
            return self.new_key(key_name), True


class S3Manager(connection.S3Connection):

    def __init__(self, *args, **kwargs):
        super(S3Manager, self).__init__(*args, **kwargs)
        self.bucket_class = BucketManager

    def get_or_create_bucket(self, bucket_name):
        try:
            bucket = self.get_bucket(bucket_name)
        except boto.exception.S3ResponseError:
            bucket = self.create_bucket(bucket_name)

        return bucket

    def find_key(self, bucket_names, key_name):
        ''' Takes a list of bucket and searches across all of them for a
        given key
        '''
        for bucket_name in bucket_names:
            try:
                bucket = self.get_bucket(bucket_name)
            except boto.exception.S3ResponseError:
                continue

            key = bucket.get_key(key_name)
            if key:
                break

        return key
