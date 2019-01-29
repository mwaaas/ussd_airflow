"""
Customer journey are stored in a document store.
Any engine that implements this interface can be integrated with journey store.
"""
from ussd.core import UssdView
from django.core.exceptions import ValidationError
import abc


class JourneyStore(object, metaclass=abc.ABCMeta):

    edit_mode_version = "edit_mode"

    @abc.abstractmethod
    def _get(self, name, version, screen_name, **kwargs):
        pass

    @abc.abstractmethod
    def _all(self, name):
        pass

    @abc.abstractmethod
    def _save(self, name, journey, version):
        pass

    @abc.abstractmethod
    def _delete(self, name, version=None):
        pass

    @abc.abstractmethod
    def flush(self):
        pass

    def get(self, name: str, version=None, screen_name=None, edit_mode=False, propagate_error=True):
        if edit_mode:
            version = self.edit_mode_version
        return self._get(name, version, screen_name)

    def all(self, name: str):
        return self._all(name)

    def save(self, name: str, journey: dict, version=None, edit_mode=False):

        # version and editor mode should not be false
        if not (version or edit_mode):
            raise TypeError("version is required if its not in editor mode")

        if edit_mode:
            version = self.edit_mode_version

        # check if this version already exists
        if self.get(name, version, propagate_error=False) is not None:
            if not edit_mode:
                raise ValidationError("journey already exists")

        # validate if its not in editing mode.
        if not edit_mode:
            is_valid, errors = UssdView.validate_ussd_journey(journey)
            if not is_valid:
                raise ValidationError("invalid journey")

        # now create journey
        return self._save(name, journey, version)

    def delete(self, name, version=None):
        return self._delete(name, version)


