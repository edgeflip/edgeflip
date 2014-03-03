import os
import json
from tempfile import NamedTemporaryFile

import boto
from boto.s3 import bucket, connection, key
from django.utils import timezone
from faraday.utils import epoch

from targetshare.integration import facebook


class FeedKey(key.Key):

    def __init__(self, *args, **kwargs):
        super(FeedKey, self).__init__(*args, **kwargs)
        self.data = None

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
        fh = NamedTemporaryFile(delete=False)
        json.dump(self.data, fh.file)
        fh.file.close()
        self.set_contents_from_filename(fh.name)
        os.remove(fh.name)

    def extend_s3_data(self, append=True):
        ''' Extends the data we have in S3, typically in incremental or
        back_fill jobs. Append flag lets you dictate if the new data ends up
        in front or in back of the existing data
        '''
        fh = NamedTemporaryFile(delete=False)
        fh.close()
        self.get_contents_to_filename(fh.name)
        fh = open(fh.name)
        full_data = json.load(fh)
        existing_data = full_data.setdefault('data', [])
        if append:
            existing_data.extend(self.data['data'])
            self.data = full_data
        else:
            self.data['data'].extend(existing_data)
        full_data['updated'] = epoch.from_date(timezone.now())
        json_file = NamedTemporaryFile(delete=False)
        json.dump(full_data, json_file.file)
        json_file.close()
        self.set_contents_from_filename(json_file.name)
        os.remove(json_file.name)
        os.remove(fh.name)

    def populate_from_s3(self):
        ''' Populates the FeedKey.data element from S3 '''
        fh = NamedTemporaryFile(delete=False)
        fh.close()
        self.get_contents_to_filename(fh.name)
        fh = open(fh.name)
        self.data = json.load(fh)


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
