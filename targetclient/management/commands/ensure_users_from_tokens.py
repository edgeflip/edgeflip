from django.core.management.base import NoArgsCommand
from django.utils import timezone

from targetshare.integration import facebook
from targetshare.models import dynamo, Client, FBApp


class Command(NoArgsCommand):
    help = "Starts the crawler service"

    def handle_noargs(self, *args, **options):
        self.stdout.write('Starting up...')
        self.crawl()

    def crawl(self):
        secrets = dict(FBApp.objects.values_list('appid', 'secret').iterator())
        for token in dynamo.Token.items.scan():
            self.stdout.write('Checking {}'.format(token))
            if token.expires > timezone.now():
                try:
                    debug_response = facebook.client.debug_token(
                        token.appid, secrets[token.appid], token.token
                    )
                    old_expires = token.expires
                    token.expires = debug_response['data']['expires_at']
                    if token.needs_save():
                        self.stdout.write("Overwriting Token.expires ({} => {})".format(old_expires, token.expires))
                        token.save(overwrite=True)
                except IOError as e:
                    self.stderr.write('Token check request failed for {} with error {}'.format(token, e))

            clients = None
            client_queryset = Client.objects.filter(fb_app_id=token.appid)
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
                self.stderr.write(
                    "fbid {} has no associated clients".format(token.fbid)
                )
