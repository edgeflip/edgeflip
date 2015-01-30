from django import template


PROFILE_PICTURE_URL = "https://graph.facebook.com/{fbid}/picture"

register = template.Library()


@register.filter(name='profilepic')
def pic_url(user):
    try:
        # TaggableFriend specifies pic:
        return user.picture
    except AttributeError:
        # Classic User provides FBID:
        fbid = user.fbid
        if not fbid:
            raise TypeError("could not generate profile pic url for {!r}".format(user))
        return PROFILE_PICTURE_URL.format(fbid=fbid)


@register.simple_tag(name="flexipic")
def flexible_pic(fbid, url):
    if url:
        return url
    elif fbid:
        return PROFILE_PICTURE_URL.format(fbid=fbid)
    else:
        raise TypeError("could not generate profile pic url (no data)")
