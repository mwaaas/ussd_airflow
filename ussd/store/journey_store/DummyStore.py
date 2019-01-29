from ..journey_store import JourneyStore
from collections import OrderedDict

store = OrderedDict()


class DummyStore(JourneyStore):
    """
    This store should not be used in production only meant to test the interface
    """

    def _get(self, name, version, screen_name, **kwargs):
        if version == 'edit_mode':
            return store.get('edit_mode', {}).get(name)
        if store.get(name):
            if version is None:  # get the latest journey created
                journey = store[name][next(reversed(store[name]))]
            else:
                journey = store[name].get(version)
            if screen_name is not None:
                return journey.get(screen_name)
            return journey
        return None

    def _all(self, name):
        return store.get(name, {})

    def _save(self, name, journey, version):
        if version == self.edit_mode_version:
            store['edit_mode'] = {name: journey}
        else:
            if store.get(name):
                store[name][version] = journey
            else:
                store[name] = OrderedDict({version: journey})
        return journey

    def _delete(self, name, version=None):
        if store.get(name):
            if store[name].get(version):
                del store[name][version]
            else:
                del store[name]

    def flush(self):
        pass

