from django.db import models
from django.utils import functional, timezone

from . import manager


class FBObjectAttributeManager(manager.TransitoryObjectManager):

    @functional.cached_property
    def _sourced_model_fields(self):
        return tuple(field.name for field in self.model._meta.fields
                     if isinstance(field, models.CharField))

    def source(self, raw_fb_attrs, default_attrs=None):
        """Conditionally store the given object, retiring any active, attribute-
        conflicting objects in the related object's set.

        Object default attributes may be specified, to be written to the given
        raw object.

        The up-to-date object is returned, (which, in case of a match, may be the
        pre-existing rather than the specified object).

        """
        try:
            fb_object = self.instance
        except AttributeError:
            raise TypeError("source is intended for use with RelatedManagers")

        if not isinstance(raw_fb_attrs, self.model):
            raise TypeError("Model mismatch")

        if raw_fb_attrs.fb_object is None:
            raw_fb_attrs.fb_object = fb_object
        elif raw_fb_attrs.fb_object != fb_object:
            raise ValueError("Facebook object mismatch")

        # Fill in defaults:
        if default_attrs is not None:
            for field in self._sourced_model_fields:
                if not getattr(raw_fb_attrs, field):
                    default_value = getattr(default_attrs, field)
                    setattr(raw_fb_attrs, field, default_value)

        try:
            fb_object_attrs = self.for_datetime().get()
        except self.model.DoesNotExist:
            pass
        else:
            if all(
                getattr(raw_fb_attrs, field) == getattr(fb_object_attrs, field)
                for field in self._sourced_model_fields
            ):
                # Update unnecessary
                return fb_object_attrs

        # Store new attrs:
        raw_fb_attrs.save()
        # Retire old, at end, and expansively, to handle races:
        self.for_datetime().exclude(pk=raw_fb_attrs.pk).update(end_dt=timezone.now())
        return raw_fb_attrs


class FBObjectAttribute(models.Model):

    fb_object_attributes_id = models.AutoField(primary_key=True)
    fb_object = models.ForeignKey('FBObject', null=True, blank=True)
    og_action = models.CharField('Action', max_length=64, blank=True)
    og_type = models.CharField('Type', max_length=64, blank=True)
    og_title = models.CharField('Title', max_length=128, blank=True)
    og_image = models.CharField('Image URL', max_length=2096, blank=True)
    og_description = models.CharField('FB Object Description',
                                      max_length=1024, blank=True)
    org_name = models.CharField('Organization Name',
                                max_length=1024, blank=True)
    page_title = models.CharField(max_length=256, blank=True)
    sharing_prompt = models.CharField(max_length=2096, blank=True)
    msg1_pre = models.CharField('Message 1 Pre', max_length=1024, blank=True)
    msg1_post = models.CharField('Message 1 Post', max_length=1024, blank=True)
    msg2_pre = models.CharField('Message 2 Pre', max_length=1024, blank=True)
    msg2_post = models.CharField('Message 2 Post', max_length=1024, blank=True)
    url_slug = models.CharField(max_length=64, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    objects = FBObjectAttributeManager()

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'fb_object_attributes'
