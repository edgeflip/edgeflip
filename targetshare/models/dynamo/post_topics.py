from .base import Item, HashKeyField, NUMBER, STRING


class PostTopics(Item):

    postid = HashKeyField(data_type=STRING)

    class Meta(object):
        allow_undeclared_fields = True
        undeclared_data_type = NUMBER

    @classmethod
    def classify(cls, postid, text):
        """Dummy text classifier."""
        # TODO: REPLACE WITH ACTUAL CLASSIFIER
        dummy_classifications = {
            'Health': '8.2', # Might have trouble with Dynamo & raw floats
            'Sports': '0.3',
            'Weather': '0.2',
        }
        return cls(postid=postid, **dummy_classifications)
