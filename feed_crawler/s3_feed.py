import json
from tempfile import TemporaryFile

import boto
from boto.s3 import bucket, connection, key
from django.utils import timezone
from faraday.utils import epoch

from targetshare.integration import facebook


class FeedKey(key.Key):

    def __init__(self, *args, **kwargs):
        super(FeedKey, self).__init__(*args, **kwargs)
        self.data = {}

    def retrieve_fb_feed(self, fbid, token, since, until):
        ''' Seeds to FeedKey.data element from FB '''
        self.data = facebook.client.urlload(
            'https://graph.facebook.com/{}/feed/'.format(fbid), {
                'access_token': token,
                'method': 'GET',
                'format': 'json',
                'suppress_http_code': 1,
                'limit': 5000,
                'since': since,
                'until': until,
            }, timeout=120
        )

    def crawl_pagination(self):
        ''' Inspects the current data set for the next url to paginate through
        and exhausts it
        '''
        next_url = self.data.get('paging', {}).get('next')
        if next_url and 'data' in self.data:
            result = facebook.client.exhaust_pagination(next_url)
            self.data['data'].extend(result)

    def save_to_s3(self):
        ''' Commits the current populated FeedKey to s3 '''
        self.data['updated'] = epoch.from_date(timezone.now())
        with TemporaryFile() as tmp_file:
            json.dump(self.data, tmp_file)
            tmp_file.seek(0)
            self.set_contents_from_file(tmp_file)

    def extend_s3_data(self, append=True):
        ''' Extends the data we have in S3, typically in incremental or
        back_fill jobs. Append flag lets you dictate if the new data ends up
        in front or in back of the existing data
        '''
        with TemporaryFile() as s3_file, TemporaryFile() as json_file:
            self.get_contents_to_file(s3_file)
            s3_file.seek(0)
            full_data = json.load(s3_file)
            existing_data = full_data.setdefault('data', [])
            if append:
                existing_data.extend(self.data['data'])
                self.data = full_data
            else:
                self.data['data'].extend(existing_data)
            self.data['updated'] = epoch.from_date(timezone.now())
            json.dump(self.data, json_file)
            json_file.seek(0)
            self.set_contents_from_file(json_file)

    def populate_from_s3(self):
        ''' Populates the FeedKey.data element from S3 '''
        with TemporaryFile() as tmp_file:
            self.get_contents_to_file(tmp_file)
            tmp_file.seek(0)
            self.data = json.load(tmp_file)


class BucketManager(bucket.Bucket):

    def __init__(self, *args, **kwargs):
        super(BucketManager, self).__init__(*args, **kwargs)
        self.key_class = FeedKey

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
        given key. Returns a list of keys found, as duplicate key names can
        be used in different buckets.
        '''
        keys = []
        for bucket_name in bucket_names:
            try:
                bucket = self.get_bucket(bucket_name)
            except boto.exception.S3ResponseError:
                continue

            key = bucket.get_key(key_name)
            if key:
                keys.append(key)

        return keys
