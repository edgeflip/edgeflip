from boto.dynamodb2 import results as baseresults


# Subclass boto's BatchGetResultSet to prevent fetch_more() from bailing
# when any one batch is empty.

# WARNING: Upgrading boto? Upgrade this too! #

class BatchGetResultSet(baseresults.BatchGetResultSet):

    @classmethod
    def clone(cls, result_set):
        new = cls()
        new.__dict__ = result_set.__dict__
        return new

    # Copy of BatchGetResultSet's fetch_more (except for %%):
    def fetch_more(self):
        self._reset()

        args = self.call_args[:]
        kwargs = self.call_kwargs.copy()

        # Slice off the max we can fetch.
        kwargs['keys'] = self._keys_left[:self._max_batch_get]
        self._keys_left = self._keys_left[self._max_batch_get:]

        results = self.the_callable(*args, **kwargs)

        # %% Comment out bail condition:
        #if not len(results.get('results', [])):
        #    self._results_left = False
        #    return
        # %% Instead just ensure response is well-formed:
        results.setdefault('results', [])

        self._results.extend(results['results'])

        for offset, key_data in enumerate(results.get('unprocessed_keys', [])):
            # We've got an unprocessed key. Reinsert it into the list.
            # DynamoDB only returns valid keys, so there should be no risk of
            # missing keys ever making it here.
            self._keys_left.insert(offset, key_data)

        if len(self._keys_left) <= 0:
            self._results_left = False

        # Decrease the limit, if it's present.
        if self.call_kwargs.get('limit'):
            self.call_kwargs['limit'] -= len(results['results'])

        # %% If we didn't actually get any results, try again:
        if self._results_left and not self._results:
            self.fetch_more()
