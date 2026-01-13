from datetime import datetime
import inspect
import pprint
import re
from typing import Union, List, Dict, Tuple, Optional
import uuid

class Model:
    openapi_types = {}

    attribute_map = {}

    def __init__(self, *args, **kwargs):
        self._check_type = kwargs.pop('_check_type', True)
        for key, value in kwargs.items():
            self.setattr(key, value)

    @classmethod
    def from_dict(cls, dikt):
        return util.deserialize_model(dikt, cls)

    def setattr(self, key, value):
        value = self._validate_value(key, value)
        self.__dict__[key] = value

    def _validate_value(self, key, value):
        if key in self.attribute_map:
            attr_type = self.openapi_types.get(key, None)
            if attr_type is None:
                return value
            
            if isinstance(value, list) and not value:
                return value
            
            if isinstance(value, dict):
                return value
            
            if issubclass(attr_type, list):
                if not isinstance(value, list):
                    return [value]
                return value
            
            if issubclass(attr_type, dict):
                if not isinstance(value, dict):
                    return {key: value}
                return value
            
            if not isinstance(value, attr_type):
                return attr_type(value)
        return value

    def to_dict(self):
        result = {}
        for attr_name, json_key in self.attribute_map.items():
            underscore_attr_name = f"_{attr_name}"
            if underscore_attr_name in self.__dict__:
                result[json_key] = self._format_value(self.__dict__[underscore_attr_name])
        return result

    def _format_value(self, value):
        if isinstance(value, list):
            return [self._format_value(item) for item in value]
        elif isinstance(value, Model):
            return value.to_dict()
        elif isinstance(value, datetime):
            return value.isoformat()
        return value

    def to_str(self):
        return str(pprint.pformat(self.to_dict()))

    def __repr__(self):
        return f"<{self.__class__.__name__}> {self.to_str()}"

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

class util:
    @staticmethod
    def deserialize_model(dikt, class_name):
        if not isinstance(dikt, dict):
            return None
        
        if not class_name.openapi_types:
            return None
        
        kwargs = {}
        for attr_name in class_name.openapi_types:
            if attr_name in dikt:
                attr_type = class_name.openapi_types[attr_name]
                value = dikt[attr_name]
                
                if value is None:
                    continue
                
                if issubclass(attr_type, list):
                    if not isinstance(value, list):
                        value = [value]
                    kwargs[attr_name] = [util.deserialize_model(item, attr_type.__args__[0]) if hasattr(attr_type, '__args__') else item for item in value]
                elif issubclass(attr_type, dict):
                    if not isinstance(value, dict):
                        value = {attr_name: value}
                    kwargs[attr_name] = {k: util.deserialize_model(v, attr_type.__args__[1]) if hasattr(attr_type, '__args__') else v for k, v in value.items()}
                elif hasattr(attr_type, 'from_dict'):
                    kwargs[attr_name] = attr_type.from_dict(value)
                else:
                    kwargs[attr_name] = value
        
        return class_name(**kwargs)

    @staticmethod
    def convert_to_date(value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                pass
        return value

    @staticmethod
    def convert_to_bool(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)
