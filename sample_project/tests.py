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

    def test_vdtorder(self):
        events = []
        for _ in range(50):
            e = VDEvent(
                date=VanishingFactory().create(
                    timezone.now(),
                    policy=self.policy1,
                ),
            )
            e.save()
            e.refresh_from_db()
            events.append(e)
        vdts = list(VanishingDateTime.objects.order_by("dt").all())
        # TODO orders by insertion order if all values are the same
        e_vdts = [e.date for e in events]
        def uuid_list(dts):
            return [vd.pk for vd in dts]
        ids_fetched = uuid_list(vdts)
        ids_inserted = uuid_list(e_vdts)
        self.assertEqual(len(set(vd.dt for vd in vdts)), 1)
        self.assertEqual(len(set(ids_inserted)), len(set(ids_fetched)))
        self.assertEqual(set(ids_inserted), set(ids_fetched))
        self.assertEqual(ids_inserted, ids_fetched)
