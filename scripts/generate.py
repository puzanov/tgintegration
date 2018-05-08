import inspect

from tgintegration import InteractionClient, AwaitableAction

for name, method in inspect.getmembers(InteractionClient, predicate=inspect.ismethod):
    if 'send_' in name and '_await' not in name:
        self._make_awaitable_method(name, method)


def _make_awaitable_method(self, name, method):
    """
    Injects `*_await` versions of all `send_*` methods.
    """

    def f(*args, filters=None, num_expected=None, **kwargs):
        action = AwaitableAction(
            func=method,
            args=(self.peer_id, *args),
            kwargs=kwargs,
            num_expected=num_expected,
            filters=self.get_default_filters(filters),
            max_wait=self.max_wait_response,
            min_wait_consecutive=self.min_wait_consecutive
        )
        return self.act_await_response(action)

    method_name = name + '_await'
    setattr(self, method_name, f)
