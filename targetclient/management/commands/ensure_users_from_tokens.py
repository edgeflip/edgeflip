from datetime import datetime
import json
import requests

from django.core.management.base import NoArgsCommand
from django.utils import timezone

from targetclient import tasks
from targetshare.integration import facebook
from targetshare.models import dynamo, Client


class Command(NoArgsCommand):
    help = "Starts the crawler service"

    def handle_noargs(self, *args, **options):
        self.stdout.write('Starting up...')
        self.crawl()

    def crawl(self):
        for token in dynamo.Token.items.scan():
            self.stdout.write('Checking token for {}'.format(token.fbid))
            if token.expires > timezone.now():
                try:
                    response = json.loads(facebook.client.debug_token(
                        token.appid, token.token
                    ))
                    token_expiration = facebook.client.token_expiration(response)
                    if token_expiration != token.expires:
                        token.expires = token_expiration
                        token.save(overwrite=True)
                except requests.exceptions.RequestException as e:
                    self.stdout.write('Token check request failed for {} with error {}'.format(token.fbid, e))
                except ValueError as e:
                    self.stdout.write('Token check response for {} is unparseable: {}'.format(token.fbid, e))

            clients = None
            client_queryset = Client.objects.filter(_fb_app_id=token.appid).all()
            if client_queryset.count() == 1:
                clients = client_queryset
            else:
                clients = Client.objects.filter(
                    campaigns__event__visit__app_id=token.appid,
                    campaigns__event__visit__visitor__fbid=token.fbid
                ).distinct()

            for client in clients:
                client.userclients.get_or_create(fbid=token.fbid)

            if len(clients) == 0:
                self.stdout.write(
                    "fbid {} has no associated clients".format(token.fbid)
                )
