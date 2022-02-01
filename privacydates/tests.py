from random import randint
import time
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .models import OrderingContext, VanishingDateTime, VanishingOrderingContext
from .precision import reduce_precision
from .vanish import vanishingdatetime_creator, make_policy
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
            self.assertEqual(x, instance.get_and_increment())

        # Test creation of ordering dates with similarity_distance =1
        OrderingContext.objects.create(context_key="testcase2-ordering",
                                       similarity_distance=1)
        instance = OrderingContext.objects.get(context_key="testcase2-ordering")
        first = instance.get_and_increment()
        second = instance.get_and_increment()
        third = instance.get_and_increment()
        time.sleep(1)
        fourth = instance.get_and_increment()
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
        policy1 = {
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
        now = timezone.now()
        v_policy = make_policy(policy=policy1)
        dta1 = VanishingDateTime.objects.create(dt=now, vanishing_policy=v_policy)
        dta2 = vanishingdatetime_creator(dt=now, vanishing_policy=v_policy)
        self.assertEqual(dta1.dt, dta2.dt)
        self.assertEqual(dta1.vanishing_policy, dta2.vanishing_policy)

        policy2 = {
            "events": [
                {
                    "offset": 0,
                    "reduction": 5
                },
            ],
        }

        v_policy2 = make_policy(policy=policy2)
        dta3 = VanishingDateTime.objects.create(dt=now, vanishing_policy=v_policy2)
        dta4 = vanishingdatetime_creator(dt=now, vanishing_policy=v_policy2)
        self.assertEqual(dta3.dt, dta4.dt)
        self.assertEqual(dta3.vanishing_policy, dta4.vanishing_policy)

        policy3 = {
            "events": [
                {
                    "offset": 550000,
                    "reduction": 120
                },
            ],
        }

        v_policy3 = make_policy(policy=policy3)
        dta5 = VanishingDateTime.objects.create(dt=now, vanishing_policy=v_policy3)
        dta6 = vanishingdatetime_creator(dt=now, vanishing_policy=v_policy3)
        self.assertEqual(dta5.dt, dta6.dt)
        self.assertEqual(dta5.vanishing_policy, dta6.vanishing_policy)

        policy4 = {
            "events": [
                {
                    "offset": 1,
                    "reduction": 5
                },
                {
                    "offset": 60,
                    "reduction": 30
                },
                {
                    "offset": 550000,
                    "reduction": 86400
                },
                {
                    "offset": 1110000,
                    "reduction": 604800
                },
            ],
        }

        v_policy4 = make_policy(policy=policy4)
        dta7 = VanishingDateTime.objects.create(dt=now, vanishing_policy=v_policy4)
        dta8 = vanishingdatetime_creator(dt=now, vanishing_policy=v_policy4)
        self.assertEqual(dta7.dt, dta8.dt)
        self.assertEqual(dta7.vanishing_policy, dta8.vanishing_policy)
        self.assertEqual(dta7.vanishing_policy.policy, policy4)

    def test_faulty_vanishing_policies(self):
        now = timezone.now()
        # Test empty dict for VanishingPolicy
        with self.assertRaises(ValueError):
            VanishingDateTime.objects.create(dt=now,
                                             vanishing_policy=
                                             make_policy(policy={}))

        # Test empty list in dict for VanishingPolicy
        with self.assertRaises(ValueError):
            VanishingDateTime.objects.create(dt=now,
                                             vanishing_policy=
                                             make_policy(
                                                    policy={"events": []})
                                             )

        # Test empty list in dict for VanishingPolicy
        faulty_policy = {
            "events": [
                {
                    "offset": 1,
                    "reduction": 5
                },
                {
                },
            ],
        }
        with self.assertRaises(ValueError):
            VanishingDateTime.objects.create(dt=now,
                                             vanishing_policy=
                                             make_policy(policy=faulty_policy))


class VanishingOrderingContextTestCase(TestCase):

    def test_vanishing_ordering_context_allinsamecontext(self):
        # All dates are created within the same 30sec max reduction window and
        # should thus have incresing ordering counts
        VanishingOrderingContext.objects.create(context_key="testcase1-an-enum")
        policy1 = {
            "events": [
                { "offset": 1, "reduction": 5 },
                { "offset": 2, "reduction": 30 },
            ],
        }
        an_policy = make_policy(policy=policy1,
                                ordering_key="testcase1-an-enum")
        instance = VanishingOrderingContext.objects.get(context_key="testcase1-an-enum")
        for x in range(0, 15):
            self.assertEqual(x, instance.get_and_increment(policy=an_policy))

    def test_vanishing_ordering_context_withreset(self):
        # Between third and fourth the 1 sec sleep causes a reset of the
        # counter because dates differ at max reduction level
        instance = VanishingOrderingContext.objects.create(
            context_key="testcase2-an-enum")
        policy2 = {
            "events": [
                { "offset": 1, "reduction": 1 },
            ],
        }
        an_policy = make_policy(policy=policy2,
                                ordering_key="testcase2-an-enum")
        first = instance.get_and_increment(policy=an_policy)
        second = instance.get_and_increment(policy=an_policy)
        third = instance.get_and_increment(policy=an_policy)
        time.sleep(1)
        fourth = instance.get_and_increment(policy=an_policy)
        # at least two counts happend within the same second
        self.assertEqual(first, 0)
        self.assertTrue(first != second or second != third)
        self.assertEqual(fourth, 0)
        self.assertTrue(third >= fourth)
