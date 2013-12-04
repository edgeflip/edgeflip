from .base import Item, ItemField, HashKeyField, NUMBER, NUMBER_SET


class FBSyncTask(Item):

    WAITING = 'waiting'
    IN_PROCESS = 'in_process'

    fbid = HashKeyField(data_type=NUMBER)
    token = ItemField()
    status = ItemField()
    fbids_to_crawl = ItemField(data_type=NUMBER_SET)

    @property
    def is_processing(self):
        ''' The opposite of is_finished '''
        return self.status in (self.WAITING, self.IN_PROCESS)
