# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    url(r'^$',  views.ConnectView.as_view(), name="connect"),
    url(r'^results/$',  views.ResultsView.as_view(), name="results"),
    url(r'^p/(?P<share_key>\w+)$',  views.ProfileView.as_view(), name="profile"),
    url(r'^c/(?P<share_key>\w+)(?:/(?P<other_share_key>\w+))?/$',  views.CompareView.as_view(), name="compare"),
    url(r'^delete/(?P<share_key>\w+)$', views.ProfileDeleteView.as_view(), name="delete"),
    url(r'^thank-you/$', TemplateView.as_view(template_name='personify/thank_you.html'), name="thank_you"),
    url(r'^empty/$', TemplateView.as_view(template_name='personify/empty.html'), name="empty"),
]

