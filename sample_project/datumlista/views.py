from django.shortcuts import redirect
from django.views.generic import ListView
from django.utils import timezone

from privacydates.precision import Precision
from privacydates.vanish import (
    update_vanishing,
    VanishingFactory,
)
from privacydates.order import ordering_key_gen

from .models import Event


class EventListView(ListView):
    """ListView of Event containing the different timestamps of
    privacydates."""
    model = Event
    template_name = 'datumlista/event_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx

    def get_queryset(self):
        if 'order' in self.request.GET:
            return Event.objects.order_by('-' + str(self.request.GET['order']))
        return Event.objects.order_by('-base_date')


def event_create_view(request):
    """Creates a new Event"""
    van_factory = VanishingFactory(policy=[
        Precision(seconds=30).after(seconds=10),
        Precision(minutes=15).after(minutes=1),
    ])

    Event.objects.create(
        base_date=timezone.now(),
        rough_date=timezone.now(),
        vanishing_date=van_factory.create(timezone.now()),
        vanishing_ordering_date=van_factory.create(
            timezone.now(),
            context=ordering_key_gen(str(request.user) + "dtae"),
        ),
        ordering_date=ordering_key_gen(str(request.user) + "en"),
        ordering_similarity_date=ordering_key_gen(str(request.user) + "en2"),
    )
    return redirect('/?order=base_date')


def event_delete_all_redirect(request):
    """Delete all stored Events"""
    Event.objects.all().delete()
    return redirect('/?order=base_date')


def vanishing_update(request):
    """Runs vanishing_update() to trigger vanishing of VanishingDateTimes"""
    update_vanishing()
    return redirect('/?order=base_date')
