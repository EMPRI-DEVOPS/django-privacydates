import json

from .precision import Precision


class PolicyEncoder(json.JSONEncoder):
    """Encode policy lists"""
    def default(self, obj):
        if isinstance(obj, Precision):
                return obj.to_dict()
        return super().default(obj)


class PolicyDecoder(json.JSONDecoder):
    """Decode policy lists"""
    def __init__(self, object_hook=None, *args, **kwargs):
        return super().__init__(object_hook=self.as_precision, *args, **kwargs)

    def as_precision(self, dct):
        if 'seconds' in dct:
            return Precision.from_dict(dct)
        return dct
