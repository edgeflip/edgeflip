from .base import Item, ItemField, HashKeyField, NUMBER, NUMBER_SET


class FBSyncTask(Item):

    WAITING = 'waiting'
    IN_PROCESS = 'in_process'
    COMPLETED = 'completed'
    FAILED = 'failed'

    fbid = HashKeyField(data_type=NUMBER)
    token = ItemField()
    status = ItemField()
    fbids_to_crawl = ItemField(data_type=NUMBER_SET)

    @property
    def is_finished(self):
        ''' Returns true if we've stopped working on this task due to
        successful completion or failure
        '''
        return self.status in (self.COMPLETED, self.FAILED)

    @property
    def is_processing(self):
        ''' The opposite of is_finished '''
        return self.status in (self.WAITING, self.IN_PROCESS)
