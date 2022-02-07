from random import randint
import time
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .models import OrderingContext, VanishingDateTime, VanishingOrderingContext
from .precision import Precision, reduce_precision
from .vanish import VanishingFactory, make_policy
from .order import ordering_key_gen


class RoughDateTestCase(TestCase):
    def test_roughdate_datetime(self):
        # Test if rough date is commutative
        time_offset = timedelta(days=50)
        reduction_value = 60*60  # 1 hours
        now = timezone.now()
        rough_now = reduce_precision(
            now, reduction_value)
        rough_then = reduce_precision(
            now + time_offset,
            reduction_value,
        )
        rough_double = reduce_precision(
            reduce_precision(now, 60) + time_offset,
            reduction_value,
        )
        self.assertEqual(rough_then, rough_now + time_offset)
        self.assertEqual(rough_then, rough_double)

        # Type tests
        with self.assertRaises(ValueError):
            reduce_precision(timezone.now(), -1)
        with self.assertRaises(ValueError):
            reduce_precision(timezone.now(), 0)
        with self.assertRaises(TypeError):
            reduce_precision(0, 0)
        with self.assertRaises(TypeError):
            reduce_precision(0, timezone.now())

        # Test if two different timestamps are roughend
        # evenly with random reduction_value
        # It cant be expected to be similar.
        for x in range(0, 10):
            reduction_value = randint(1, 9999999)
            rough_now_r = reduce_precision(timezone.now(), reduction_value)
            rough_then_r = reduce_precision(timezone.now() + time_offset,
                                            reduction_value)
            r_diff = abs(rough_then_r - (rough_now_r + time_offset))
            self.assertLessEqual(r_diff, timedelta(seconds=reduction_value))


class OrderingContextTestCase(TestCase):

    def test_ordering_context(self):
        # Test creation of ordering dates without similarity_distance
        OrderingContext.objects.create(context_key="testcase1-ordering")
        for x in range(1, 15):
            instance = OrderingContext.objects.get(context_key="testcase1-ordering")
            self.assertEqual(x, instance.next())

        # Test creation of ordering dates with similarity_distance =1
        OrderingContext.objects.create(context_key="testcase2-ordering",
                                       similarity_distance=1)
        instance = OrderingContext.objects.get(context_key="testcase2-ordering")
        first = instance.next()
        second = instance.next()
        third = instance.next()
        time.sleep(1)
        fourth = instance.next()
        self.assertTrue(first == second or second == third)
        self.assertNotEqual(third, fourth)

    def test_ordering_key_gen(self):
        key_string = "this-is-a-test"
        key1 = ordering_key_gen(key_string)
        self.assertEqual(type(key1), str)
        self.assertEqual(key1, ordering_key_gen(key_string))

        ec = OrderingContext.objects.create(context_key=key1)
        ec.save()
        self.assertEqual(ec.context_key, OrderingContext.objects.get(context_key=key1).context_key)
        self.assertNotEqual(ec, OrderingContext.objects.get_or_create(context_key=key1[:-1]))
        self.assertNotEqual(ec, OrderingContext.objects.get_or_create(context_key=key1 + "1"))


class VanishingDateTimeTestCase(TestCase):

    def test_vanishingdatetime_creation(self):
        policy1 = make_policy([
            Precision(seconds=5).after(seconds=1),
            Precision(seconds=30).after(seconds=2),
        ])
        now = timezone.now()
        dta1 = VanishingDateTime.objects.create(dt=now, vanishing_policy=policy1)
        dta2 = VanishingFactory().create(now, policy=policy1)
        self.assertEqual(now, dta1.dt)
        self.assertEqual(dta1.dt, dta2.dt)
        self.assertEqual(dta1.vanishing_policy, dta2.vanishing_policy)
        self.assertEqual(dta1.events.count(), 1)

        # reduction should be applied immediately and no events created
        policy2 = make_policy([
            Precision(seconds=5).after(seconds=0),
        ])
        dta3 = VanishingDateTime.objects.create(dt=now, vanishing_policy=policy2)
        dta4 = VanishingFactory().create(now, policy=policy2)
        self.assertNotEqual(now, dta3.dt)
        self.assertEqual(dta3.dt, dta4.dt)
        self.assertEqual(dta3.vanishing_policy, dta4.vanishing_policy)
        self.assertEqual(dta3.events.count(), 0)
        self.assertEqual(dta4.events.count(), 0)

        policy3 = make_policy([
            Precision(seconds=120).after(seconds=550000),
        ])
        dta5 = VanishingDateTime.objects.create(dt=now, vanishing_policy=policy3)
        dta6 = VanishingFactory().create(now, policy=policy3)
        self.assertEqual(dta5.dt, dta6.dt)
        self.assertEqual(dta5.vanishing_policy, dta6.vanishing_policy)

        policy4 = make_policy([
            Precision(seconds=5).after(seconds=1),
            Precision(seconds=30).after(seconds=60),
            Precision(seconds=86400).after(seconds=550000),
            Precision(seconds=604800).after(seconds=1110000),
        ])
        dta7 = VanishingDateTime.objects.create(dt=now, vanishing_policy=policy4)
        dta8 = VanishingFactory().create(now, policy=policy4)
        self.assertEqual(dta7.dt, dta8.dt)
        self.assertEqual(dta7.vanishing_policy, dta8.vanishing_policy)
        self.assertEqual(dta7.vanishing_policy.policy, policy4.policy)
        self.assertEqual(dta8.events.count(), 1)

    def test_faulty_vanishing_policies(self):
        now = timezone.now()
        # Test empty dict for VanishingPolicy
        with self.assertRaises(ValueError):
            VanishingDateTime.objects.create(dt=now,
                                             vanishing_policy=
                                             make_policy(policy=[]))


class VanishingOrderingContextTestCase(TestCase):

    def test_vanishing_ordering_context_allinsamecontext(self):
        # All dates are created within the same 30sec max reduction window and
        # should thus have incresing ordering counts
        VanishingOrderingContext.objects.create(context_key="testcase1-an-enum")
        policy = make_policy([
            Precision(seconds=5).after(seconds=1),
            Precision(seconds=30).after(seconds=2),
        ], ordering_key="testcase1-an-enum")
        instance = VanishingOrderingContext.objects.get(context_key="testcase1-an-enum")
        for i in range(0, 15):
            self.assertEqual(i, instance.next(policy=policy))

    def test_vanishing_ordering_context_withreset(self):
        # Between third and fourth the 1 sec sleep causes a reset of the
        # counter because dates differ at max reduction level
        instance = VanishingOrderingContext.objects.create(
            context_key="testcase2-an-enum")
        policy = make_policy([
            Precision(seconds=1).after(seconds=1),
        ], ordering_key="testcase2-an-enum")
        first = instance.next(policy=policy)
        second = instance.next(policy=policy)
        third = instance.next(policy=policy)
        time.sleep(1)
        fourth = instance.next(policy=policy)
        # at least two counts happend within the same second
        self.assertEqual(first, 0)
        self.assertTrue(first != second or second != third)
        self.assertEqual(fourth, 0)
        self.assertTrue(third >= fourth)
