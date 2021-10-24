from random import randint
import time
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone


from .models import EnumerationContext, DateTimeAnnihilation, AnnihilationEnumContext
from .generalization import generalize_datetime
from .annihilation import datetimeannihilation_creator, annihilation_policy_creator
from .enumeration import enumeration_key_gen


# Create your tests here.
class GeneralizationTestCase(TestCase):
    def test_generalize_datetime(self):
        # Test if two different timestamps are generalized evenly
        time_offset = timedelta(days=50)
        reduction_value = 10800
        generalized_now = generalize_datetime(timezone.now(),
                                              reduction_value=reduction_value)
        generalized_then = generalize_datetime(timezone.now()
                                               + time_offset,
                                               reduction_value=reduction_value)
        generalized_double = generalize_datetime(generalize_datetime(timezone.now(),
                                                                     60)
                                                 + time_offset,
                                                 reduction_value=reduction_value)
        self.assertEqual(generalized_then, generalized_now + time_offset)
        self.assertEqual(generalized_then, generalized_double)

        # Type tests
        with self.assertRaises(ValueError):
            generalize_datetime(timezone.now(), -1)
        with self.assertRaises(ValueError):
            generalize_datetime(timezone.now(), 0)
        with self.assertRaises(TypeError):
            generalize_datetime(0, 0)
        with self.assertRaises(TypeError):
            generalize_datetime(0, timezone.now())

        # Test if two different timestamps are generalized
        # evenly with random reduction_value
        # It cant be expected to be similar.
        for x in range(0, 10):
            reduction_value = randint(1, 9999999)
            generalized_now_r = generalize_datetime(timezone.now(),
                                                    reduction_value=reduction_value)
            generalized_then_r = generalize_datetime(timezone.now()
                                                     + time_offset,
                                                     reduction_value=reduction_value)
            r_diff = abs(generalized_then_r - (generalized_now_r + time_offset))
            self.assertLessEqual(r_diff, timedelta(seconds=reduction_value))


class EnumerationContextTestCase(TestCase):

    def test_enumeration_context(self):
        # Test creation of enumeration without similarity_distance
        EnumerationContext.objects.create(context_key="testcase1-enumeration")
        for x in range(1, 15):
            instance = EnumerationContext.objects.get(context_key="testcase1-enumeration")
            self.assertEqual(x, instance.get_and_increment())

        # Test creation of enumeration with similarity_distance =1
        EnumerationContext.objects.create(context_key="testcase2-enumeration",
                                          similarity_distance=1)
        instance = EnumerationContext.objects.get(context_key="testcase2-enumeration")
        first = instance.get_and_increment()
        second = instance.get_and_increment()
        third = instance.get_and_increment()
        time.sleep(1)
        fourth = instance.get_and_increment()
        self.assertTrue(first == second or second == third)
        self.assertNotEqual(third, fourth)

    def test_enumeration_key_gen(self):
        key_string = "this-is-a-test"
        key1 = enumeration_key_gen(key_string)
        self.assertEqual(type(key1), str)
        self.assertEqual(key1, enumeration_key_gen(key_string))

        ec = EnumerationContext.objects.create(context_key=key1)
        ec.save()
        self.assertEqual(ec.context_key, EnumerationContext.objects.get(context_key=key1).context_key)
        self.assertNotEqual(ec, EnumerationContext.objects.get_or_create(context_key=key1[:-1]))
        self.assertNotEqual(ec, EnumerationContext.objects.get_or_create(context_key=key1 + "1"))


class DateTimeAnnihilationTestCase(TestCase):

    def test_datetimeannihilation_creation(self):
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
        an_policy = annihilation_policy_creator(policy=policy1)
        dta1 = DateTimeAnnihilation.objects.create(dt=now,annihilation_policy=an_policy)
        dta2 = datetimeannihilation_creator(dt=now, annihilation_policy=an_policy)
        self.assertEqual(dta1.dt, dta2.dt)
        self.assertEqual(dta1.annihilation_policy, dta2.annihilation_policy)

        policy2 = {
            "events": [
                {
                    "offset": 0,
                    "reduction": 5
                },
            ],
        }

        an_policy2 = annihilation_policy_creator(policy=policy2)
        dta3 = DateTimeAnnihilation.objects.create(dt=now, annihilation_policy=an_policy2)
        dta4 = datetimeannihilation_creator(dt=now, annihilation_policy=an_policy2)
        self.assertEqual(dta3.dt, dta4.dt)
        self.assertEqual(dta3.annihilation_policy, dta4.annihilation_policy)

        policy3 = {
            "events": [
                {
                    "offset": 550000,
                    "reduction": 120
                },
            ],
        }

        an_policy3 = annihilation_policy_creator(policy=policy3)
        dta5 = DateTimeAnnihilation.objects.create(dt=now, annihilation_policy=an_policy3)
        dta6 = datetimeannihilation_creator(dt=now, annihilation_policy=an_policy3)
        self.assertEqual(dta5.dt, dta6.dt)
        self.assertEqual(dta5.annihilation_policy, dta6.annihilation_policy)

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

        an_policy4 = annihilation_policy_creator(policy=policy4)
        dta7 = DateTimeAnnihilation.objects.create(dt=now, annihilation_policy=an_policy4)
        dta8 = datetimeannihilation_creator(dt=now, annihilation_policy=an_policy4)
        self.assertEqual(dta7.dt, dta8.dt)
        self.assertEqual(dta7.annihilation_policy, dta8.annihilation_policy)
        self.assertEqual(dta7.annihilation_policy.policy, policy4)



    def test_faulty_annihilation_policies(self):
        now = timezone.now()
        # Test empty dict for AnnihilationPolicy
        with self.assertRaises(ValueError):
            DateTimeAnnihilation.objects.create(dt=now,
                                                annihilation_policy=
                                                annihilation_policy_creator(policy={}))

        # Test empty list in dict for AnnihilationPolicy
        with self.assertRaises(ValueError):
            DateTimeAnnihilation.objects.create(dt=now,
                                                annihilation_policy=
                                                annihilation_policy_creator(
                                                    policy={"events": []})
                                                )

        # Test empty list in dict for AnnihilationPolicy
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
            DateTimeAnnihilation.objects.create(dt=now,
                                                annihilation_policy=
                                                annihilation_policy_creator(policy=faulty_policy))


class AnnihilationEnumContextTestCase(TestCase):

    def test_annihilation_enumeration_context(self):
        # Test creation of enumeration without similarity_distance
        AnnihilationEnumContext.objects.create(context_key="testcase1-an-enum")
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
        an_policy = annihilation_policy_creator(policy=policy1,
                                                enumeration_key="testcase1-an-enum")

        for x in range(0, 15):
            instance = AnnihilationEnumContext.objects.get(context_key="testcase1-an-enum")
            self.assertEqual(x, instance.get_and_increment(policy=an_policy))

        AnnihilationEnumContext.objects.create(context_key="testcase2-an-enum")
        policy2 = {
                 "events": [
                    {
                        "offset": 1,
                        "reduction": 1
                    },
                    ],
                }
        an_policy = annihilation_policy_creator(policy=policy2,
                                                enumeration_key="testcase2-an-enum")
        first = instance.get_and_increment(policy=an_policy)
        second = instance.get_and_increment(policy=an_policy)
        third = instance.get_and_increment(policy=an_policy)
        time.sleep(1)
        fourth = instance.get_and_increment(policy=an_policy)
        self.assertTrue(first != second or second != third)
        self.assertEqual(first, fourth)
        self.assertTrue(third >= fourth)
