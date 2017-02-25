from rest_framework import serializers


class UssdBaseSerializer(serializers.Serializer):
    """
    Each screen as a field "type" to determine which screen
    to display.

    type should be the supported only.
    for those that are not supported will get this message
       "Invalid screen type not supported"
    """
    type = serializers.CharField(max_length=50)

    def validate_type(self, value):
        # to avoid cyclic import
        from ussd.core import _registered_ussd_handlers
        if value not in _registered_ussd_handlers.keys():
            raise serializers.ValidationError("Invalid screen "
                                              "type not supported")
        return value


class UssdTextField(serializers.DictField):
    """
    Ussd text that's going to be displayed to the user.
    example

    text: This is the text that is going to be shown

    To display multi language

    text:
        en: This the text in english
        sw: this the text in swahili
        default: en
    """

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            data = {
                'en': data,
                'default': 'en'}
        return super(UssdTextField, self).to_internal_value(data)

class UssdTextSerializer(serializers.Serializer):

    text = UssdTextField(child=serializers.CharField(max_length=500,
                                                     allow_blank=True))


class UssdContentBaseSerializer(UssdBaseSerializer, UssdTextSerializer):
    pass


class NextUssdScreenSerializer(serializers.Serializer):
    next_screen = serializers.CharField(max_length=50)

    def validate_next_screen(self, value):
        if value not in self.context.keys():
            raise serializers.ValidationError(
                "{screen} is missing in ussd journey".format(screen=value)
            )
        return value


class MenuOptionSerializer(UssdTextSerializer, NextUssdScreenSerializer):
    input_value = serializers.CharField(required=False, max_length=5,
                                        allow_blank=True)
    input_display = serializers.CharField(required=False, max_length=5)


class MenuSerializer(serializers.Serializer):
    options = serializers.ListField(
        child=MenuOptionSerializer(),
        required=True
    )