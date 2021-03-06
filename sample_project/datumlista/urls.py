from django.urls import path

from .views import (EventListView,
                    event_create_view,
                    event_delete_all_redirect,
                    vanishing_update)

urlpatterns = [
    path('', EventListView.as_view(), name='event-list'),
    path('new/', event_create_view, name='event-create'),
    path('delete-all/', event_delete_all_redirect, name='event-delete-all'),
    path('v-update/', vanishing_update, name='event-vanishing-update'),
]