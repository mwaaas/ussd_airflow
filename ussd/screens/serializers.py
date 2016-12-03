from rest_framework import serializers


class UssdBaseSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=50)

    def validate_type(self, value):
        # to avoid cyclic import
        from ussd.core import _registered_ussd_handlers
        if value not in _registered_ussd_handlers.keys():
            raise serializers.ValidationError("Invalid screen "
                                              "type not supported")
        return value in _registered_ussd_handlers.keys()


class UssdTextSerializer(serializers.Serializer):

    text = serializers.DictField(child=serializers.CharField(max_length=250))

    def validate_text(self, value):
        if not value['default'] in value.keys():
            raise serializers.ValidationError(
                "Text for language {} is missing".format(value['default'])
            )
        return value

class UssdContentBaseSerializer(UssdBaseSerializer, UssdTextSerializer):
    pass

class NextUssdScreenSerializer(serializers.Serializer):
    next_screen = serializers.CharField(max_length=50)

    def validate_next_screen(self, value):
        return value in self.context.keys()