from .base import (
    Item, ItemField, HashKeyField, RangeKeyField, NUMBER, NUMBER_SET
)


class FBSyncTask(Item):

    # Statuses
    WAITING = 'waiting'
    IN_PROCESS = 'in_process'
    BACK_FILLING = 'back_filling'

    fbid = HashKeyField(data_type=NUMBER)
    token = ItemField()
    status = ItemField()
    fbids_to_crawl = ItemField(data_type=NUMBER_SET)
    back_filled = ItemField(data_type=NUMBER)

    @property
    def is_processing(self):
        ''' The opposite of is_finished '''
        return self.status in (self.WAITING, self.IN_PROCESS)


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
    back_filled = ItemField(data_type=NUMBER)
    back_fill_epoch = ItemField(data_type=NUMBER)
    incremental_epoch = ItemField(data_type=NUMBER)
    status = ItemField()
    bucket = ItemField()

    def change_status(self, status):
        self.status = status
        self.save(overwrite=True)

    @property
    def s3_key_name(self):
        return u'{}_{}'.format(self.fbid_primary, self.fbid_secondary)
