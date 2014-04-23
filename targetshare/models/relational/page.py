import re

from django.db import models

from . import manager
from .base import BaseModel


class Page(BaseModel):

    BUTTON = 'button'
    FRAME_FACES = 'frame_faces'

    page_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    code = models.SlugField(max_length=100, unique=True)

    objects = manager.TypeObjectManager()

    class Meta(BaseModel.Meta):
        db_table = 'pages'

    def __unicode__(self):
        return u'{}'.format(self.name)


class PageStyle(BaseModel):

    HTTP_PROTOCOLS = re.compile(r'^https?:')

    page_style_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    page = models.ForeignKey('Page', related_name='pagestyles')
    client = models.ForeignKey('Client', null=True, related_name='pagestyles')
    starred = models.BooleanField(default=False) # offer to user to link to new campaign
                                                 # (rather than globals and/or inheritance)
    visible = models.BooleanField(default=True)
    url = models.URLField(max_length=255)

    class Meta(BaseModel.Meta):
        db_table = 'page_styles'
        unique_together = ('name', 'client')

    def __unicode__(self):
        name = self.name and u' ({})'.format(self.name)
        return u'{}{}'.format(self.page, name)

    @property
    def href(self):
        return self.HTTP_PROTOCOLS.sub('', self.url)


class PageStyleSet(BaseModel):

    page_style_set_id = models.AutoField(primary_key=True)
    page_styles = models.ManyToManyField('PageStyle', related_name='pagestylesets')

    class Meta(BaseModel.Meta):
        db_table = 'page_style_sets'

    def __unicode__(self):
        text = u''
        for page_style in self.page_styles.all():
            if text:
                text += u', '

                if len(text) > 100:
                    text += u'...'
                    break

            text += unicode(page_style)

        return u'[{}]'.format(text)


class CampaignPageStyleSet(BaseModel):

    campaign_page_style_set_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign', related_name='campaignpagestylesets')
    page_style_set = models.OneToOneField('PageStyleSet')
    rand_cdf = models.DecimalField(decimal_places=9, max_digits=10)

    objects = manager.AssignedObjectManager.make(page_style_set)

    class Meta(BaseModel.Meta):
        db_table = 'campaign_page_style_sets'

    def __unicode__(self):
        return u'{} ({}) | {}'.format(self.campaign, self.rand_cdf, self.page_style_set)
