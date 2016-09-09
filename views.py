# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.generic import TemplateView, DetailView, DeleteView
from .models import Profile
from .data import tooltips


class ConnectView(TemplateView):
    template_name = "personify/connect.html"

    def get_context_data(self, **kwargs):
        context = super(ConnectView, self).get_context_data(**kwargs)
        context.update({
            'url_for_results': reverse('personify:results')
        })
        return context


class ResultsView(TemplateView):
    template_name = "personify/processing.html"

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated():
            return redirect("personify:connect")

        return super(ResultsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ResultsView, self).get_context_data(**kwargs)

        profile, created = Profile.objects.get_or_create(user=self.request.user)

        context.update({
            'profile': profile,
        })

        return context


class BaseProfileView(DetailView):
    model = Profile
    slug_url_kwarg = 'share_key'
    slug_field = 'share_key'


class ProfileView(BaseProfileView):
    template_name = "personify/profile.html"

    def fetch(self):
        profile = self.get_object()

        if not profile.name or not profile.picture_url:
            profile.sync_social()

        if not profile.personality:
            profile.sync_personality()

    def dispatch(self, request, *args, **kwargs):
        if request.is_ajax():
            self.fetch()
            return JsonResponse({})

        profile = self.get_object()
        if profile.word_count() < 100:
            return redirect('personify:empty')

        return super(ProfileView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)

        profile = self.get_object()

        share_url = self.request.build_absolute_uri(reverse('personify:profile', args=(profile.share_key, )))

        context.update({
            'profile': profile,
            'own_profile': profile.user == self.request.user,
            'result': profile.get_personality(),
            'famous_people': profile.get_similar_famous(7 if profile.is_famous else 6),
            'friends': profile.get_similar_friends(),
            'share_url': share_url,
            'tooltips': tooltips,
        })

        return context


class CompareView(BaseProfileView):
    template_name = 'personify/compare.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            return super(CompareView, self).dispatch(request, *args, **kwargs)
        except (Profile.DoesNotExist, TypeError):
            return redirect('personify:connect')

    def get_context_data(self, **kwargs):
        context = super(CompareView, self).get_context_data(**kwargs)

        profile = self.get_object()

        other_key = self.kwargs.get('other_share_key', '')

        if other_key:
            compare_with = Profile.objects.get(share_key=other_key)
        else:
            compare_with = Profile.objects.get(user=self.request.user)

        if profile.user == self.request.user:
            # always put own profile to the right
            profile, compare_with = compare_with, profile

        share_url = self.request.build_absolute_uri(
            reverse('personify:compare', args=(profile.share_key, compare_with.share_key))
        )

        own_profile = compare_with.user == self.request.user

        profile.get_ratio(compare_with)

        context.update({
            'profile': profile,
            'other_profile': compare_with,
            'own_profile': own_profile,
            'famous': profile.get_similar_famous(1)[0],
            'other_famous': compare_with.get_similar_famous(1)[0],
            'share_url': share_url,
            'tooltips': tooltips,
        })

        return context


class ProfileDeleteView(DeleteView, BaseProfileView):

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.user == request.user:
            self.object.delete()
            return redirect(reverse('personify:thank_you'))
        raise ObjectDoesNotExist()

