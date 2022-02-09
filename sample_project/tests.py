from django.test import TestCase
from datumlista.models import Event, VDEvent
from django.utils import timezone

from privacydates.vanish import (
    VanishingFactory,
)
from privacydates.models import (
    OrderingContext,
    VanishingDateTime,
)
from privacydates.precision import Precision


class EventTest(TestCase):
    policy1 = [
        Precision(minutes=1),
        Precision(minutes=5).after(hours=1),
    ]

    def get_event(self):
        return Event(
            base_date=timezone.now(),
            rough_date=timezone.now(),
            vanishing_date=VanishingFactory().create(
                timezone.now(),
                policy=self.policy1,
            ),
            vanishing_ordering_date=VanishingFactory().create(
                timezone.now(),
                policy=self.policy1,
                context="userA" + "dtae",
                hashed=True,
            ),
            ordering_date="userA" + "en",
            ordering_similarity_date="userB" + "en2",
        )


    def test_roughdate(self):
        now = timezone.now()
        e = self.get_event()
        e.rough_date = now
        # TODO reduction happens late during save
        self.assertEqual(e.rough_date, now)
        e.save()
        self.assertNotEqual(e.rough_date, now)
        e.refresh_from_db()
        self.assertNotEqual(e.rough_date, now)

    def test_orderingdate(self):
        e = self.get_event()
        e.save()
        # now we should have 2 contexts
        self.assertEqual(OrderingContext.objects.count(), 2)
        # ... one hashed (so we cannot see the user name)
        self.assertEqual(
            OrderingContext.objects.filter(context_key__contains="userA").count(),
            0
        )
        # ... and one unhashed
        self.assertEqual(
            OrderingContext.objects.filter(context_key__contains="userB").count(),
            1
        )

    def test_vdtorder_insertion_preserved(self):
        """Evaluate whether the chronological order of VanishingDates is
        maintained by databases through the insertion order despite all
        VanishingDates having the same date value.
        Ideally: this test should fail to show that instertion orders are not
        maintained. But that's currently not the case.
        """
        events = []
        factory = VanishingFactory(policy=self.policy1)
        for _ in range(50):
            e = VDEvent(
                date=factory.create(timezone.now()),
            )
            e.save()
            e.refresh_from_db()
            events.append(e)
        # fetch objects ordered by date value
        vdts_by_date = list(VanishingDateTime.objects.order_by("dt").all())
        # all dates are the same
        self.assertEqual(len(set(vd.dt for vd in vdts_by_date)), 1)
        # list objects by their chronological insertion order
        vdts_by_insertion = [e.date for e in events]
        # compare if the two have the same order
        def uuid_list(dts):
            return [vd.pk for vd in dts]
        ids_by_date = uuid_list(vdts_by_date)
        ids_by_insertion = uuid_list(vdts_by_insertion)
        self.assertEqual(ids_by_insertion, ids_by_date)
