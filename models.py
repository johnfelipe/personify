# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import force_unicode
from django.utils.functional import cached_property
from django_extensions.db.models import TimeStampedModel
from allauth.socialaccount.models import SocialToken, SocialAccount

from jsonfield import JSONField
from hashids import Hashids

import uuid
import twitter
import facepy
import requests

from .util import humanize_ibm_output, cosine_similarity, mean_similarity


class Profile(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    picture_url = models.CharField(max_length=512, blank=True, null=True)
    social_url = models.URLField(max_length=515, blank=True, null=True, help_text="Twitter URL")
    friends = models.ManyToManyField('self', symmetrical=True, blank=True)
    friend_ids_cache = JSONField(blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    is_famous = models.BooleanField(default=False)
    manually_added = models.BooleanField(default=False)
    share_key = models.CharField(max_length=255, blank=True, null=True)
    personality = JSONField(blank=True, null=True)
    personality_flat = JSONField(blank=True, null=True)
    personality_raw = JSONField(blank=True, null=True)

    def __unicode__(self):
        return self.name or '<Profile object>'

    @cached_property
    def facebook(self):
        return SocialToken.objects.filter(account__user=self.user, account__provider='facebook').first()

    @cached_property
    def twitter(self):
        return SocialToken.objects.filter(account__user=self.user, account__provider='twitter').first()

    @cached_property
    def social_type(self):
        if self.facebook:
            return 'facebook'
        if self.twitter or 'twitter.com' in self.social_url:
            return 'twitter'

    def sync_social(self):

        if self.facebook:
            graph = facepy.GraphAPI(self.facebook.token)
            profile = graph.get('me', fields=['name','id'])
            self.name = profile['name']
            self.picture_url = u"https://graph.facebook.com/%s/picture?type=normal" % profile['id']
            self.save()

            for page in graph.get('me/friends', page=True):
                friends = page['data']
                for friend in friends:
                    try:
                        acc = SocialAccount.objects.get(provider='facebook', uid=friend['id'])
                        profile = Profile.objects.get(user=acc.user)
                    except (SocialAccount.DoesNotExist, Profile.DoesNotExist):
                        continue
                    self.friends.add(profile)

        elif self.twitter:
            api = twitter.Api(
                consumer_key=self.twitter.app.client_id,
                consumer_secret=self.twitter.app.secret,
                access_token_key=self.twitter.token,
                access_token_secret=self.twitter.token_secret
            )
            profile = api.VerifyCredentials()
            self.name = profile.screen_name
            self.picture_url = profile.profile_image_url
            if not 'default_profile_images' in self.picture_url:
                self.picture_url = self.picture_url.replace("_normal", "_80x80")

            try:
                friend_ids = list(api.GetFriendIDs(screen_name=profile.screen_name))
            except twitter.TwitterError:
                friend_ids = []

            self.friend_ids_cache = friend_ids
            self.save()

            friend_user_ids = SocialAccount.objects.filter(provider='twitter', uid__in=friend_ids).values_list('user_id', flat=True)

            for p in Profile.objects.filter(user__id__in=friend_user_ids):
                if p.friend_ids_cache and profile.id in p.friend_ids_cache:
                    self.friends.add(p)

    def sync_text(self):
        text = ''

        if self.facebook:
            graph = facepy.GraphAPI(self.facebook.token)
            posts = graph.get('me/posts', limit=400)['data']
            text += '\n'.join(post.get('message', '') for post in posts)

        if self.twitter:
            api = twitter.Api(
                consumer_key=self.twitter.app.client_id,
                consumer_secret=self.twitter.app.secret,
                access_token_key=self.twitter.token,
                access_token_secret=self.twitter.token_secret
            )
            posts = api.GetUserTimeline(trim_user=True, include_rts=False, count=200)
            text += '\n'.join(post.text or '' for post in posts)

        self.text = force_unicode(text)
        self.save()

    def word_count(self):
        text = self.get_text()
        if not text:
            return 0
        return len(text.split())

    def flatten_personality(self, personality=None):
        personality = personality or self.personality
        flat = list()
        try:
            # using the big 5 traits only (found in the 'personality' store)
            for key, value in personality['personality'].items():
                # assuming keys are always in the same order (alphabetical), because they seem to
                # be returned like that by IBM Watson
                flat.extend([v['percentage'] for v in value['children'].values()])
        except KeyError:
            pass
        return flat

    def sync_personality(self):
        text = self.get_text()
        personality = dict()

        if text and self.word_count() >= 100:
            r = requests.post(
                'https://gateway.watsonplatform.net/personality-insights/api/v2/profile',
                auth=(settings.IBM_USERNAME, settings.IBM_PASSWORD),
                headers={'Content-Type': 'text/plain', 'X-Watson-Learning-Opt-Out': 'true'},
                data=text.encode('utf-8')
            )
            try:
                self.personality_raw = r.json()
                personality = humanize_ibm_output(self.personality_raw)
            except KeyError:
                pass

        self.personality = personality
        self.personality_flat = self.flatten_personality()
        self.save()

        return self.personality

    def get_text(self):
        if not self.text:
            self.sync_text()

        return self.text

    def get_personality(self):
        if not self.personality:
            self.sync_personality()
        return self.personality

    def get_personality_flat(self):
        if not self.personality_flat:
            self.sync_personality()
        return self.personality_flat

    def get_ratio(self, profile):
        profile.ratio = mean_similarity(self.get_personality_flat(), profile.get_personality_flat())
        return profile.ratio

    def get_similar(self, compared_set):
        def compare(x, y):
            return cmp(self.get_ratio(x), self.get_ratio(y))
        if len(compared_set) == 1:
            self.get_ratio(compared_set[0])
            return compared_set
        return sorted(compared_set, cmp=compare, reverse=True)

    def get_similar_famous(self, limit=6):
        return self.get_similar(Profile.objects.exclude(pk=self.pk).filter(is_famous=True))[:limit]

    def get_similar_friends(self):
        return self.get_similar(self.friends.all())


@receiver(post_save, sender=Profile)
def generate_share_key(sender, instance, *args, **kwargs):
    if not instance.share_key:
        hashids = Hashids(salt=settings.SECRET_KEY, min_length=6)
        instance.share_key = hashids.encode(instance.id)
        instance.save()

