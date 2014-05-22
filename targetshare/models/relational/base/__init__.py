from core.models import base


class BaseModel(base.BaseModel):

    class Meta(base.BaseModel.Meta):
        abstract = True
        app_label = 'targetshare'
