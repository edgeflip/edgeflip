import unittest
import json

from targetshare.integration.facebook import neo_client


class FakeResponse(object):
    def __init__(self, response):
        self.response = response
        self.data = ""

    def json(self):
        return json.loads(self.response)



class TestFacebookIntegration(unittest.TestCase):

    user_id = 1001

    def assertNumInteractionsOfType(self, post, t, num):
        self.assertEqual(
            len([p for p in post.interactions if p.type == t]),
            num
        )

    def processStream(self, processor, response):
        res = FakeResponse(response)
        processor(None, res, self.user_id),
        stream = res.data
        self.assertEqual(len(stream), 1)
        return stream[0]

    def test_process_statuses(self):
        post = self.processStream(neo_client.process_statuses, STATUSES_RESPONSE)
        self.assertEqual(len(post.interactions), 12)
        self.assertNumInteractionsOfType(post, 'place_tags', 2)
        self.assertNumInteractionsOfType(post, 'stat_likes', 3)
        self.assertNumInteractionsOfType(post, 'stat_tags', 2)
        self.assertNumInteractionsOfType(post, 'stat_comms', 5)

    def test_process_links(self):
        post = self.processStream(neo_client.process_links, LINKS_RESPONSE)
        self.assertEqual(len(post.interactions), 7)
        self.assertNumInteractionsOfType(post, 'link_likes', 2)
        self.assertNumInteractionsOfType(post, 'link_comms', 5)

    def test_process_photos(self):
        post = self.processStream(neo_client.process_photos, PHOTOS_RESPONSE)
        self.assertEqual(len(post.interactions), 7)
        self.assertNumInteractionsOfType(post, 'photo_comms', 5)
        self.assertNumInteractionsOfType(post, 'photos_target', 1)
        self.assertNumInteractionsOfType(post, 'photo_tags', 1)

    def test_process_uploaded_photos(self):
        post = self.processStream(neo_client.process_photo_uploads, UPLOADED_PHOTOS_RESPONSE)
        self.assertEqual(len(post.interactions), 9)
        self.assertNumInteractionsOfType(post, 'photo_upload_likes', 4)
        self.assertNumInteractionsOfType(post, 'photo_upload_comms', 5)

    def test_process_videos(self):
        post = self.processStream(neo_client.process_videos, VIDEO_RESPONSE)
        self.assertEqual(len(post.interactions), 14)
        self.assertNumInteractionsOfType(post, 'video_tags', 12)
        self.assertNumInteractionsOfType(post, 'video_comms', 1)
        self.assertNumInteractionsOfType(post, 'videos_target', 1)

    def test_process_uploaded_videos(self):
        post = self.processStream(neo_client.process_video_uploads, UPLOADED_VIDEO_RESPONSE)
        self.assertEqual(len(post.interactions), 9)
        self.assertNumInteractionsOfType(post, 'video_upload_likes', 4)
        self.assertNumInteractionsOfType(post, 'video_upload_comms', 5)


STATUSES_RESPONSE = """{
  "data": [
    {
      "id": "10102566703732170",
      "from": {
        "id": "10102136605223030",
        "name": "Primary"
      },
      "message": "Message",
      "place": {
        "id": "45120837507",
        "name": "Cambridge Brewing Company",
        "location": {
          "city": "Cambridge",
          "country": "United States",
          "latitude": 42.366324771621,
          "longitude": -71.091288293804,
          "state": "MA",
          "street": "1 Kendall Square, Bldg 100",
          "zip": "02139"
        }
      },
      "updated_time": "2015-01-15T23:56:32+0000",
      "tags": {
        "data": [
          {
            "id": "10100310661169647",
            "name": "Secondary One"
          },
          {
            "id": "10101348749197701",
            "name": "Secondary Two"
          }
        ],
        "paging": {
          "next": "https://graph.facebook.com/v2.2/10102566703732170/tags?limit=25&offset=25&__after_id=enc_AexfDzHAV7YX1W3SEjFUGBmCDKkNWEcM43Fv2xC02t2IgA07mMsnNwfFa9BgHGrnfuI"
        }
      },
      "comments": {
        "data": [
          {
            "id": "10152501842691267_10152501852051267",
            "can_remove": false,
            "created_time": "2014-11-02T04:06:20+0000",
            "from": {
              "id": "10152574644056267",
              "name": "Secondary"
            },
            "like_count": 0,
            "message": "message",
            "user_likes": false
          },
          {
            "id": "10152501842691267_10152501876156267",
            "can_remove": false,
            "created_time": "2014-11-02T04:20:17+0000",
            "from": {
              "id": "10204451905080422",
              "name": "Secondary"
            },
            "like_count": 0,
            "message": "message",
            "user_likes": false
          },
          {
            "id": "10152501842691267_10152501878861267",
            "can_remove": false,
            "created_time": "2014-11-02T04:22:30+0000",
            "from": {
              "id": "10152574644056267",
              "name": "Secondary"
            },
            "like_count": 0,
            "message": "message",
            "user_likes": false
          },
          {
            "id": "10152501842691267_10152501883241267",
            "can_remove": false,
            "created_time": "2014-11-02T04:25:50+0000",
            "from": {
              "id": "10204451905080422",
              "name": "Secondary"
            },
            "like_count": 0,
            "message": "message",
            "user_likes": false
          },
          {
            "id": "10152501842691267_10152501883781267",
            "can_remove": false,
            "created_time": "2014-11-02T04:26:07+0000",
            "from": {
              "id": "10152574644056267",
              "name": "Secondary"
            },
            "like_count": 1,
            "message": "message",
            "user_likes": false
          }
        ],
        "paging": {
          "cursors": {
            "before": "WTI5dGJXVnVkRjlqZFhKemIzSTZNVEF4TlRJMU1ERTROVEl3TlRFeU5qYzZNVFF4TkRrd01URTRNQT09",
            "after": "WTI5dGJXVnVkRjlqZFhKemIzSTZNVEF4TlRJMU1ERTRPRE0zT0RFeU5qYzZNVFF4TkRrd01qTTJOdz09"
          }
        }
      },
      "likes": {
        "data": [
          {
            "id": "10100310661169647",
            "name": "Secondary"
          },
          {
            "id": "10101011051751181",
            "name": "Secondary"
          },
          {
            "id": "10152045573676244",
            "name": "Secondary"
          }
        ],
        "paging": {
          "cursors": {
            "after": "MTAxNTIwNDU1NzM2NzYyNDQ=",
            "before": "MTAxMDAzMTA2NjExNjk2NDc="
          }
        }
      }
    }
  ],
  "paging": {
    "next": "https://graph.facebook.com/v2.2/10102136605223030/statuses?limit=25&offset=25&__after_id=enc_AeyG6Ea7wFmBlHsfD5GIfb_nlxgp7QvSazcexpSCq4gwnOeD_qpBcLq-RC5hQINO10qcQlh1zpnZNZlQA5LTHHO-"
  }
}"""
LINKS_RESPONSE = """{
"data": [
{
  "id": "10102499464365400",
  "from": {
    "id": "10102136605223030",
    "name": "Primary"
  },
  "message": "Signing off for a week, landlubbers!",
  "picture": "https://fbexternal-a.akamaihd.net/safe_image.php?d=AQDSQAZiskr7t1D6&w=130&h=130&url=http%3A%2F%2Fi.ytimg.com%2Fvi%2FavaSdC0QOUM%2Fhqdefault.jpg",
  "privacy": {
    "description": "Public",
    "value": "EVERYONE",
    "allow": "",
    "deny": "",
    "networks": "",
    "friends": ""
  },
  "link": "http://www.youtube.com/watch?v=avaSdC0QOUM",
  "name": "I'm On A Boat (Explicit Version)",
  "description": "Music video by The Lonely Island performing I'm On A Boat. (C) 2009 Universal Republic Records",
  "icon": "https://fbstatic-a.akamaihd.net/rsrc.php/v2/yD/r/aS8ecmYRys0.gif",
  "created_time": "2014-12-27T17:16:40+0000",
  "comments": {
    "data": [
      {
        "id": "10152501842691267_10152501852051267",
        "can_remove": false,
        "created_time": "2014-11-02T04:06:20+0000",
        "from": {
          "id": "10152574644056267",
          "name": "Secondary"
        },
        "like_count": 0,
        "message": "message",
        "user_likes": false
      },
      {
        "id": "10152501842691267_10152501876156267",
        "can_remove": false,
        "created_time": "2014-11-02T04:20:17+0000",
        "from": {
          "id": "10204451905080422",
          "name": "Secondary"
        },
        "like_count": 0,
        "message": "message",
        "user_likes": false
      },
      {
        "id": "10152501842691267_10152501878861267",
        "can_remove": false,
        "created_time": "2014-11-02T04:22:30+0000",
        "from": {
          "id": "10152574644056267",
          "name": "Secondary"
        },
        "like_count": 0,
        "message": "message",
        "user_likes": false
      },
      {
        "id": "10152501842691267_10152501883241267",
        "can_remove": false,
        "created_time": "2014-11-02T04:25:50+0000",
        "from": {
          "id": "10204451905080422",
          "name": "Secondary"
        },
        "like_count": 0,
        "message": "message",
        "user_likes": false
      },
      {
        "id": "10152501842691267_10152501883781267",
        "can_remove": false,
        "created_time": "2014-11-02T04:26:07+0000",
        "from": {
          "id": "10152574644056267",
          "name": "Secondary"
        },
        "like_count": 1,
        "message": "message",
        "user_likes": false
      }
    ],
    "paging": {
      "cursors": {
        "before": "WTI5dGJXVnVkRjlqZFhKemIzSTZNVEF4TlRJMU1ERTROVEl3TlRFeU5qYzZNVFF4TkRrd01URTRNQT09",
        "after": "WTI5dGJXVnVkRjlqZFhKemIzSTZNVEF4TlRJMU1ERTRPRE0zT0RFeU5qYzZNVFF4TkRrd01qTTJOdz09"
      }
    }
  },
  "likes": {
    "data": [
      {
        "id": "10101011051751181",
        "name": "Secondary"
      },
      {
        "id": "995974668592",
        "name": "Secondary"
      }
    ],
    "paging": {
      "cursors": {
        "after": "OTk1OTc0NjY4NTky",
        "before": "MTAxMDEwMTEwNTE3NTExODE="
      }
    }
  }
}
],
"paging": {
"cursors": {
  "after": "TVRBeE1ESTBPVGswTmpRek5qVTBNREE2TVRReE9UY3dNRFl3TURvME9UVXhNell4T1RNNU1qSTNOVEU9",
  "before": "TVRBeE1ESTBPVGswTmpRek5qVTBNREE2TVRReE9UY3dNRFl3TURvME9UVXhNell4T1RNNU1qSTNOVEU9"
},
"next": "https://graph.facebook.com/v2.2/10102136605223030/links?limit=1&after=TVRBeE1ESTBPVGswTmpRek5qVTBNREE2TVRReE9UY3dNRFl3TURvME9UVXhNell4T1RNNU1qSTNOVEU9"
}
}"""

PHOTOS_RESPONSE = """{
"data": [
{
  "id": "10152501842691267",
  "created_time": "2014-11-02T04:00:37+0000",
  "from": {
    "id": "10152574644056267",
    "name": "Secondary"
  },
  "height": 482,
  "icon": "https://fbstatic-a.akamaihd.net/rsrc.php/v2/yz/r/StEh3RhPvjk.gif",
  "images": [
    {
      "height": 878,
      "source": "https://fbcdn-sphotos-f-a.akamaihd.net/hphotos-ak-xap1/t31.0-8/10688303_10152501842691267_5294898468831353598_o.jpg",
      "width": 1310
    },
    {
      "height": 720,
      "source": "https://fbcdn-sphotos-f-a.akamaihd.net/hphotos-ak-xap1/t31.0-8/p720x720/10688303_10152501842691267_5294898468831353598_o.jpg",
      "width": 1074
    },
    {
      "height": 600,
      "source": "https://fbcdn-sphotos-f-a.akamaihd.net/hphotos-ak-xap1/t31.0-8/p600x600/10688303_10152501842691267_5294898468831353598_o.jpg",
      "width": 895
    },
    {
      "height": 480,
      "source": "https://fbcdn-sphotos-f-a.akamaihd.net/hphotos-ak-xap1/t31.0-8/p480x480/10688303_10152501842691267_5294898468831353598_o.jpg",
      "width": 716
    },
    {
      "height": 320,
      "source": "https://fbcdn-sphotos-f-a.akamaihd.net/hphotos-ak-xap1/v/t1.0-9/p320x320/10352035_10152501842691267_5294898468831353598_n.jpg?oh=6f7f9c9d1e25eef79c7ba60b8ed040a3&oe=552D78EE&__gda__=1428767061_d2f61ed4ad47b2481988229187048c1e",
      "width": 477
    },
    {
      "height": 540,
      "source": "https://fbcdn-sphotos-f-a.akamaihd.net/hphotos-ak-xap1/t31.0-8/p180x540/10688303_10152501842691267_5294898468831353598_o.jpg",
      "width": 805
    },
    {
      "height": 130,
      "source": "https://fbcdn-sphotos-f-a.akamaihd.net/hphotos-ak-xap1/v/t1.0-9/p130x130/10352035_10152501842691267_5294898468831353598_n.jpg?oh=7af917597aa1fca5a90bc3954d6d8e49&oe=5556FAFE&__gda__=1433074757_59a9823f8f6f41ea9e7c7884f54df00b",
      "width": 194
    },
    {
      "height": 225,
      "source": "https://fbcdn-sphotos-f-a.akamaihd.net/hphotos-ak-xap1/v/t1.0-9/p75x225/10352035_10152501842691267_5294898468831353598_n.jpg?oh=36db255f1509b5af9f736450179362cf&oe=552B9D80&__gda__=1433023416_52647c04bc79fa0d07a2ee4bc37f7a34",
      "width": 335
    }
  ],
  "link": "https://www.facebook.com/photo.php?fbid=10152501842691267&set=p.10152501842691267&type=1",
  "name": "2003",
  "picture": "https://fbcdn-sphotos-f-a.akamaihd.net/hphotos-ak-xap1/v/t1.0-9/s130x130/10352035_10152501842691267_5294898468831353598_n.jpg?oh=f298f47b8c0c42b82a5a28451ca4cb58&oe=556AB0BF&__gda__=1432561412_893937324d5bbcaee47b8088c15cef4f",
  "source": "https://fbcdn-sphotos-f-a.akamaihd.net/hphotos-ak-xap1/t31.0-8/s720x720/10688303_10152501842691267_5294898468831353598_o.jpg",
  "updated_time": "2014-11-02T04:03:19+0000",
  "width": 720,
  "tags": {
    "data": [
      {
        "id": "10102136605223030",
        "name": "Secondary",
        "created_time": "2014-11-02T04:03:19+0000",
        "x": 55.190311418685,
        "y": 36.528497409326
      }
    ],
    "paging": {
      "cursors": {
        "before": "MTAxMDIxMzY2MDUyMjMwMzA=",
        "after": "MTAxMDIxMzY2MDUyMjMwMzA="
      }
    }
  },
  "comments": {
    "data": [
      {
        "id": "10152501842691267_10152501852051267",
        "can_remove": false,
        "created_time": "2014-11-02T04:06:20+0000",
        "from": {
          "id": "10152574644056267",
          "name": "Secondary"
        },
        "like_count": 0,
        "message": "message",
        "user_likes": false
      },
      {
        "id": "10152501842691267_10152501876156267",
        "can_remove": false,
        "created_time": "2014-11-02T04:20:17+0000",
        "from": {
          "id": "10204451905080422",
          "name": "Secondary"
        },
        "like_count": 0,
        "message": "message",
        "user_likes": false
      },
      {
        "id": "10152501842691267_10152501878861267",
        "can_remove": false,
        "created_time": "2014-11-02T04:22:30+0000",
        "from": {
          "id": "10152574644056267",
          "name": "Secondary"
        },
        "like_count": 0,
        "message": "message",
        "user_likes": false
      },
      {
        "id": "10152501842691267_10152501883241267",
        "can_remove": false,
        "created_time": "2014-11-02T04:25:50+0000",
        "from": {
          "id": "10204451905080422",
          "name": "Secondary"
        },
        "like_count": 0,
        "message": "message",
        "user_likes": false
      },
      {
        "id": "10152501842691267_10152501883781267",
        "can_remove": false,
        "created_time": "2014-11-02T04:26:07+0000",
        "from": {
          "id": "10152574644056267",
          "name": "Secondary"
        },
        "like_count": 1,
        "message": "message",
        "user_likes": false
      }
    ],
    "paging": {
      "cursors": {
        "before": "WTI5dGJXVnVkRjlqZFhKemIzSTZNVEF4TlRJMU1ERTROVEl3TlRFeU5qYzZNVFF4TkRrd01URTRNQT09",
        "after": "WTI5dGJXVnVkRjlqZFhKemIzSTZNVEF4TlRJMU1ERTRPRE0zT0RFeU5qYzZNVFF4TkRrd01qTTJOdz09"
      }
    }
  }
}
],
"paging": {
"cursors": {
  "before": "TVRBeE5USTFNREU0TkRJMk9URXlOamM2TVRReE5Ea3dNRGs1T1Rvek9UUXdPRGsyTkRBMk5EYzRNelk9",
  "after": "TVRBeE5USTFNREU0TkRJMk9URXlOamM2TVRReE5Ea3dNRGs1T1Rvek9UUXdPRGsyTkRBMk5EYzRNelk9"
},
"next": "https://graph.facebook.com/v2.2/10102136605223030/photos?pretty=0&limit=1&after=TVRBeE5USTFNREU0TkRJMk9URXlOamM2TVRReE5Ea3dNRGs1T1Rvek9UUXdPRGsyTkRBMk5EYzRNelk9"
}
}"""

UPLOADED_PHOTOS_RESPONSE = """{
  "data": [
    {
      "id": "10102519656525150",
      "created_time": "2015-01-03T17:29:48+0000",
      "from": {
        "id": "10102136605223030",
        "name": "Secondary"
      },
      "height": 640,
      "icon": "https://fbstatic-a.akamaihd.net/rsrc.php/v2/yz/r/StEh3RhPvjk.gif",
      "images": [
        {
          "height": 640,
          "source": "https://fbcdn-sphotos-a-a.akamaihd.net/hphotos-ak-xpa1/v/t1.0-9/10888760_10102519656525150_3272199599873278007_n.jpg?oh=9327b9ada411ebf6dc7da454f16d9cd5&oe=55274E5D&__gda__=1428527691_af40c57d8e00715d12e76baea3378220",
          "width": 640
        },
        {
          "height": 600,
          "source": "https://fbcdn-sphotos-a-a.akamaihd.net/hphotos-ak-xpa1/v/t1.0-9/p600x600/10888760_10102519656525150_3272199599873278007_n.jpg?oh=d8584a8a4759d502bb5c2629f57b30ac&oe=55288D6D&__gda__=1432934034_162f16c1f92a9e7227bbf12201675561",
          "width": 600
        },
        {
          "height": 480,
          "source": "https://fbcdn-sphotos-a-a.akamaihd.net/hphotos-ak-xpa1/v/t1.0-9/p480x480/10888760_10102519656525150_3272199599873278007_n.jpg?oh=60a167e62da73f4bd49d762373c4dd75&oe=555AC857&__gda__=1431804840_3534b3aac3ce3f0c0cb483eec8beb615",
          "width": 480
        },
        {
          "height": 320,
          "source": "https://fbcdn-sphotos-a-a.akamaihd.net/hphotos-ak-xpa1/v/t1.0-9/p320x320/10888760_10102519656525150_3272199599873278007_n.jpg?oh=38e38b1682ec2f2fffda0d7532db5c30&oe=552BD215&__gda__=1428595178_7b567d603b7f5e8c3ade784e5fe11421",
          "width": 320
        },
        {
          "height": 540,
          "source": "https://fbcdn-sphotos-a-a.akamaihd.net/hphotos-ak-xpa1/v/t1.0-9/p180x540/10888760_10102519656525150_3272199599873278007_n.jpg?oh=6d340dce59f840f25fc60c6865002194&oe=5527D630&__gda__=1432691407_a41a9629bcb1cff7f3a42293a2982129",
          "width": 540
        },
        {
          "height": 130,
          "source": "https://fbcdn-sphotos-a-a.akamaihd.net/hphotos-ak-xpa1/v/t1.0-9/p130x130/10888760_10102519656525150_3272199599873278007_n.jpg?oh=fc3db83cf7c70c338430c7e1ce86a16e&oe=5564CD05&__gda__=1428822778_43cb872bcdf1e5916f042e680dc12d60",
          "width": 130
        },
        {
          "height": 225,
          "source": "https://fbcdn-sphotos-a-a.akamaihd.net/hphotos-ak-xpa1/v/t1.0-9/p75x225/10888760_10102519656525150_3272199599873278007_n.jpg?oh=80449bab06cd3c173e0b0d9a82b12169&oe=5565C27B&__gda__=1428550334_9fc2b8461a1b7b06c3e5f9ca5e1e6eba",
          "width": 225
        }
      ],
      "link": "https://www.facebook.com/photo.php?fbid=10102519656525150&set=a.10101366211328570.1073741825.22924712&type=1",
      "picture": "https://fbcdn-sphotos-a-a.akamaihd.net/hphotos-ak-xpa1/v/t1.0-9/p130x130/10888760_10102519656525150_3272199599873278007_n.jpg?oh=fc3db83cf7c70c338430c7e1ce86a16e&oe=5564CD05&__gda__=1428822778_43cb872bcdf1e5916f042e680dc12d60",
      "place": {
        "id": "135300709852537",
        "name": "Musical Legends Park",
        "location": {
          "city": "New Orleans",
          "country": "United States",
          "latitude": 29.955795874605,
          "longitude": -90.068367337647,
          "state": "LA",
          "street": "311 Bourbon St",
          "zip": "70112"
        }
      },
      "source": "https://fbcdn-sphotos-a-a.akamaihd.net/hphotos-ak-xpa1/v/t1.0-9/10888760_10102519656525150_3272199599873278007_n.jpg?oh=9327b9ada411ebf6dc7da454f16d9cd5&oe=55274E5D&__gda__=1428527691_af40c57d8e00715d12e76baea3378220",
      "updated_time": "2015-01-03T17:29:53+0000",
      "width": 640,
      "comments": {
        "data": [
          {
            "id": "10152501842691267_10152501852051267",
            "can_remove": false,
            "created_time": "2014-11-02T04:06:20+0000",
            "from": {
              "id": "10152574644056267",
              "name": "Secondary"
            },
            "like_count": 0,
            "message": "message",
            "user_likes": false
          },
          {
            "id": "10152501842691267_10152501876156267",
            "can_remove": false,
            "created_time": "2014-11-02T04:20:17+0000",
            "from": {
              "id": "10204451905080422",
              "name": "Secondary"
            },
            "like_count": 0,
            "message": "message",
            "user_likes": false
          },
          {
            "id": "10152501842691267_10152501878861267",
            "can_remove": false,
            "created_time": "2014-11-02T04:22:30+0000",
            "from": {
              "id": "10152574644056267",
              "name": "Secondary"
            },
            "like_count": 0,
            "message": "message",
            "user_likes": false
          },
          {
            "id": "10152501842691267_10152501883241267",
            "can_remove": false,
            "created_time": "2014-11-02T04:25:50+0000",
            "from": {
              "id": "10204451905080422",
              "name": "Secondary"
            },
            "like_count": 0,
            "message": "message",
            "user_likes": false
          },
          {
            "id": "10152501842691267_10152501883781267",
            "can_remove": false,
            "created_time": "2014-11-02T04:26:07+0000",
            "from": {
              "id": "10152574644056267",
              "name": "Secondary"
            },
            "like_count": 1,
            "message": "message",
            "user_likes": false
          }
        ],
        "paging": {
          "cursors": {
            "before": "WTI5dGJXVnVkRjlqZFhKemIzSTZNVEF4TlRJMU1ERTROVEl3TlRFeU5qYzZNVFF4TkRrd01URTRNQT09",
            "after": "WTI5dGJXVnVkRjlqZFhKemIzSTZNVEF4TlRJMU1ERTRPRE0zT0RFeU5qYzZNVFF4TkRrd01qTTJOdz09"
          }
        }
      },
      "likes": {
        "data": [
          {
            "id": "10205434390758878",
            "name": "Secondary"
          },
          {
            "id": "10101011051751181",
            "name": "Secondary"
          },
          {
            "id": "10152574644056267",
            "name": "Secondary"
          },
          {
            "id": "663310473768030",
            "name": "Secondary"
          }
        ],
        "paging": {
          "cursors": {
            "before": "MTAyMDU0MzQzOTA3NTg4Nzg=",
            "after": "NjYzMzEwNDczNzY4MDMw"
          }
        }
      }
    }
  ],
  "paging": {
    "cursors": {
      "before": "MTAxMDI1MTk2NTY1MjUxNTA=",
      "after": "MTAxMDI1MTk2NTY1MjUxNTA="
    },
    "next": "https://graph.facebook.com/v2.2/10102136605223030/photos?pretty=0&type=uploaded&limit=1&after=MTAxMDI1MTk2NTY1MjUxNTA="
  }
}
"""

VIDEO_RESPONSE = """\
{
  "data": [
    {
      "id": "518615539166",
      "from": {
        "id": "617824518576",
        "name": "Secondary"
      },
      "tags": {
        "data": [
          {
            "id": "10204412229840565",
            "name": "Secondary",
            "created_time": "2011-03-20T17:42:40+0000"
          },
          {
            "id": "792733960791686",
            "name": "Secondary",
            "created_time": "2011-03-20T17:38:08+0000"
          },
          {
            "id": "871631922886836",
            "name": "Secondary",
            "created_time": "2011-03-20T17:38:08+0000"
          },
          {
            "id": "1012466942112845",
            "name": "Secondary",
            "created_time": "2011-03-20T17:38:08+0000"
          },
          {
            "id": "10202154888272229",
            "name": "Secondary",
            "created_time": "2011-03-20T17:38:08+0000"
          },
          {
            "id": "10205716671504573",
            "name": "Secondary",
            "created_time": "2011-03-20T17:38:08+0000"
          },
          {
            "id": "10205609618706172",
            "name": "Secondary",
            "created_time": "2011-03-20T17:38:08+0000"
          },
          {
            "id": "10203258318273342",
            "name": "Secondary",
            "created_time": "2011-03-20T17:38:08+0000"
          },
          {
            "id": "617824518576",
            "name": "Secondary",
            "created_time": "2011-03-20T17:38:08+0000"
          },
          {
            "id": "10102136605223030",
            "name": "Secondary",
            "created_time": "2011-03-20T17:38:08+0000"
          },
          {
            "id": "10104516286821820",
            "name": "Secondary",
            "created_time": "2011-03-20T17:38:08+0000"
          },
          {
            "id": "10100885596354717",
            "name": "Secondary",
            "created_time": "2011-03-20T17:38:07+0000"
          }
        ]
      },
      "name": "ac-cent-tchu-ate the positive",
      "description": "stuff",
      "picture": "https://fbcdn-vthumb-a.akamaihd.net/hvthumb-ak-xap1/v/t15.0-10/50916_518616043156_518615539166_60530_1422_t.jpg?oh=5389de249b71d3c471742caad3ea9c94&oe=5556A0F1&__gda__=1428558901_04911f362b3287ce3430fccaf8c12611",
      "embed_html": "skip this",
      "icon": "https://fbstatic-a.akamaihd.net/rsrc.php/v2/yD/r/DggDhA4z4tO.gif",
      "source": "https://fbcdn-video-f-a.akamaihd.net/hvideo-ak-xpa1/v/t43.1792-2/1221765_573278474206_53800_n.mp4?rl=1500&vabr=901&oh=d13b010d625eb55fdebd7882ec159b05&oe=54C570A7&__gda__=1422201096_1e9c4bd8497604d971651a9be13f94c1",
      "created_time": "2011-03-20T16:49:37+0000",
      "updated_time": "2011-03-20T16:49:37+0000",
      "format": [
        {
          "embed_html": "skip this",
          "width": 130,
          "height": 73,
          "filter": "130x130",
          "picture": "https://fbcdn-vthumb-a.akamaihd.net/hvthumb-ak-xap1/v/t15.0-10/s130x130/50916_518616043156_518615539166_60530_1422_t.jpg?oh=e99dd26c21a42a42e6287224801fec88&oe=556AB799&__gda__=1432344112_8b57a94475d23c6a428cd09018f3f942"
        },
        {
          "embed_html": "skip this",
          "width": 480,
          "height": 270,
          "filter": "480x480",
          "picture": "https://fbcdn-vthumb-a.akamaihd.net/hvthumb-ak-xap1/v/t15.0-10/s480x480/50916_518616043156_518615539166_60530_1422_b.jpg?oh=0c27c5283ed789a304094cb89d24e3b7&oe=55667D90&__gda__=1432753721_b51692472e76ba06ec5b55fda6f28dd8"
        },
        {
          "embed_html": "skip this",
          "width": 720,
          "height": 405,
          "filter": "720x720",
          "picture": "https://fbcdn-vthumb-a.akamaihd.net/hvthumb-ak-xap1/v/t15.0-10/s720x720/50916_518616043156_518615539166_60530_1422_b.jpg?oh=017560dd4660d479770eeeb613f976c0&oe=556EDAA5&__gda__=1432589068_0320eb4035fbcbf56f68e3350299344c"
        },
        {
          "embed_html": "skip this",
          "width": 1280,
          "height": 720,
          "filter": "native",
          "picture": "https://fbcdn-vthumb-a.akamaihd.net/hvthumb-ak-xap1/v/t15.0-10/50916_518616043156_518615539166_60530_1422_b.jpg?oh=628075079d7b3812944841835b90ddfc&oe=555EEFD3&__gda__=1433134103_8b2db6ad263eab4fb0dee0c9917fd44d"
        }
      ],
      "comments": {
        "data": [
          {
            "id": "518615539166_137899",
            "can_remove": false,
            "created_time": "2011-03-20T21:05:55+0000",
            "from": {
              "id": "10205716671504573",
              "name": "Secondary"
            },
            "like_count": 0,
            "message": "Love it! Nice work!",
            "user_likes": false
          }
        ],
        "paging": {
          "cursors": {
            "before": "WTI5dGJXVnVkRjlqZFhKemIzSTZOVEU0TmpFNU5qTTFPVFUyT2pFek56ZzVPUT09",
            "after": "WTI5dGJXVnVkRjlqZFhKemIzSTZOVEU0TmpFNU5qTTFPVFUyT2pFek56ZzVPUT09"
          }
        }
      }
    }
  ],
  "paging": {
    "previous": "https://graph.facebook.com/v2.2/10102136605223030/videos?limit=1&type=tagged&since=1300639778",
    "next": "https://graph.facebook.com/v2.2/10102136605223030/videos?limit=1&type=tagged&until=1300639776"
  }
}
"""

UPLOADED_VIDEO_RESPONSE = """\
{
  "data": [
    {
      "id": "10101939815022170",
      "from": {
        "id": "10102136605223030",
        "name": "Secondary"
      },
      "description": "Another night art installation, this one a prerecorded animation set to music and projected onto an old church on the UQAM campus",
      "picture": "https://scontent.xx.fbcdn.net/hvthumb-xpf1/v/l/t15.0-10/1976490_10101939815286640_10101939815022170_1482_433_t.jpg?oh=32bf718f052984ae81d1547382e8ace3&oe=55283474",
      "embed_html": "skip this",
      "icon": "https://fbstatic-a.akamaihd.net/rsrc.php/v2/yD/r/DggDhA4z4tO.gif",
      "source": "https://fbcdn-video-e-a.akamaihd.net/hvideo-ak-xfp1/v/t43.1792-2/10258421_10101939815251710_266929836_n.mp4?rl=1584&vabr=1056&oh=4a01c8b84b615b513197138bd6e9b8ae&oe=54C527AD&__gda__=1422145718_06d9482214e5435216661c70c161eb42",
      "created_time": "2014-04-13T04:09:44+0000",
      "updated_time": "2014-04-13T04:09:44+0000",
      "format": [
        {
          "embed_html": "skip this",
          "width": 130,
          "height": 130,
          "filter": "130x130",
          "picture": "https://scontent.xx.fbcdn.net/hvthumb-xpf1/v/l/t15.0-10/s130x130/1976490_10101939815286640_10101939815022170_1482_433_t.jpg?oh=01f7dd4bf58f32c225e8ca7022f9ff8d&oe=5568F1E7"
        },
        {
          "embed_html": "skip this",
          "width": 480,
          "height": 480,
          "filter": "480x480",
          "picture": "https://scontent.xx.fbcdn.net/hvthumb-xpf1/v/l/t15.0-10/s480x480/1976490_10101939815286640_10101939815022170_1482_433_b.jpg?oh=3f43b0ee215f898b023068c3e8aaf5c4&oe=555FA472"
        },
        {
          "embed_html": "skip this",
          "width": 640,
          "height": 640,
          "filter": "native",
          "picture": "https://scontent.xx.fbcdn.net/hvthumb-xpf1/v/l/t15.0-10/1976490_10101939815286640_10101939815022170_1482_433_b.jpg?oh=6d68cba8f6212cc5a9bb27d9d746861e&oe=55619856"
        }
      ],
      "comments": {
        "data": [
          {
            "id": "10152501842691267_10152501852051267",
            "can_remove": false,
            "created_time": "2014-11-02T04:06:20+0000",
            "from": {
              "id": "10152574644056267",
              "name": "Secondary"
            },
            "like_count": 0,
            "message": "message",
            "user_likes": false
          },
          {
            "id": "10152501842691267_10152501876156267",
            "can_remove": false,
            "created_time": "2014-11-02T04:20:17+0000",
            "from": {
              "id": "10204451905080422",
              "name": "Secondary"
            },
            "like_count": 0,
            "message": "message",
            "user_likes": false
          },
          {
            "id": "10152501842691267_10152501878861267",
            "can_remove": false,
            "created_time": "2014-11-02T04:22:30+0000",
            "from": {
              "id": "10152574644056267",
              "name": "Secondary"
            },
            "like_count": 0,
            "message": "message",
            "user_likes": false
          },
          {
            "id": "10152501842691267_10152501883241267",
            "can_remove": false,
            "created_time": "2014-11-02T04:25:50+0000",
            "from": {
              "id": "10204451905080422",
              "name": "Secondary"
            },
            "like_count": 0,
            "message": "message",
            "user_likes": false
          },
          {
            "id": "10152501842691267_10152501883781267",
            "can_remove": false,
            "created_time": "2014-11-02T04:26:07+0000",
            "from": {
              "id": "10152574644056267",
              "name": "Secondary"
            },
            "like_count": 1,
            "message": "message",
            "user_likes": false
          }
        ],
        "paging": {
          "cursors": {
            "before": "WTI5dGJXVnVkRjlqZFhKemIzSTZNVEF4TlRJMU1ERTROVEl3TlRFeU5qYzZNVFF4TkRrd01URTRNQT09",
            "after": "WTI5dGJXVnVkRjlqZFhKemIzSTZNVEF4TlRJMU1ERTRPRE0zT0RFeU5qYzZNVFF4TkRrd01qTTJOdz09"
          }
        }
      },
      "likes": {
        "data": [
          {
            "id": "10205434390758878",
            "name": "Secondary"
          },
          {
            "id": "10101011051751181",
            "name": "Secondary"
          },
          {
            "id": "10152574644056267",
            "name": "Secondary"
          },
          {
            "id": "663310473768030",
            "name": "Secondary"
          }
        ],
        "paging": {
          "cursors": {
            "before": "MTAyMDU0MzQzOTA3NTg4Nzg=",
            "after": "NjYzMzEwNDczNzY4MDMw"
          }
        }
      }
    }
  ],
  "paging": {
    "previous": "https://graph.facebook.com/v2.2/10102136605223030/videos?type=uploaded&limit=25&since=1397362185",
    "next": "https://graph.facebook.com/v2.2/10102136605223030/videos?type=uploaded&limit=25&until=1397362183"
  }
}"""
