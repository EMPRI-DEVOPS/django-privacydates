from django.shortcuts import redirect
from django.views.generic import (ListView)

from django.utils import timezone

from privacydates.annihilation import annihilation_policy_creator, annihilation_updater,\
    datetimeannihilation_creator
from privacydates.enumeration import enumeration_key_gen
from .models import Event

# Create your views here.


# ListView of Event containing just different timestamps
class EventListView(ListView):
    model = Event
    template_name = 'datumlista/event_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx

    def get_queryset(self):
        if 'order' in self.request.GET:
            return Event.objects.order_by('-' + str(self.request.GET['order']))
        return Event.objects.order_by('-base_date')


# Creates a new Event.
def event_create_view(request):
    policy_dict = {
        "events": [
            {
                "offset": 1,
                "reduction": 5
            },
            {
                "offset": 2,
                "reduction": 30
            },
        ],
    }

    Event.objects.create(base_date=timezone.now(),
                         generalized_date=timezone.now(),
                         annihilation_date=datetimeannihilation_creator(timezone.now(),
                                                                        annihilation_policy_creator(policy_dict)),
                         annihilation_enumeration_date=datetimeannihilation_creator(timezone.now(),
                                                                                    annihilation_policy_creator(
                                                                                        policy_dict,
                                                                                        enumeration_key=
                                                                                        enumeration_key_gen(
                                                                                            str(request.user) + "dtae"
                                                                                        )
                                                                                    )
                                                                                    ),
                         enumeration_date=enumeration_key_gen(str(request.user) + "en"),
                         enumeration_similarity_date = enumeration_key_gen(str(request.user) + "en2"))
    return redirect('/?order=base_date')


# Delete all stored Events
def event_delete_all_redirect(request):
    Event.objects.all().delete()
    return redirect('/?order=base_date')


def annihilation_update(request):
    annihilation_updater()
    return redirect('/?order=base_date')
