from faraday import (
    BOOL, Item, ItemField, HashKeyField, RangeKeyField, NUMBER
)


class FBSyncMap(Item):

    # Statuses
    WAITING = 'waiting'
    INITIAL_CRAWL = 'initial_crawl'
    BACK_FILL = 'back_fill'
    INCREMENTAL = 'incremental'
    COMMENT_CRAWL = 'comment_crawl'
    COMPLETE = 'complete'

    fbid_primary = HashKeyField(data_type=NUMBER)
    fbid_secondary = RangeKeyField(data_type=NUMBER)
    token = ItemField()
    back_filled = ItemField(data_type=BOOL)
    back_fill_epoch = ItemField(data_type=NUMBER)
    incremental_epoch = ItemField(data_type=NUMBER)
    status = ItemField()
    bucket = ItemField()

    def save_status(self, status):
        self.status = status
        self.save(overwrite=True)

    @property
    def s3_key_name(self):
        return u'{}_{}'.format(self.fbid_primary, self.fbid_secondary)
