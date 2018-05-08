import re
import weakref
from typing import List, Pattern, TypeVar, Union

import itertools

from pyrogram import Filters, InlineKeyboardButton, KeyboardButton
from pyrogram.api.types import Message
from pyrogram.client.filters.filter import Filter
from ..awaitableaction import AwaitableAction

InteractionClient = TypeVar('InteractionClient')
Response = TypeVar('Response')


class ReplyKeyboard:
    def __init__(
            self,
            client: InteractionClient,
            chat_id: int,
            message_id: int,
            button_rows: List[List[KeyboardButton]]
    ):
        self._client = weakref.proxy(client)
        self._message_id = message_id
        self._peer_id = chat_id
        self.rows = button_rows

    def _find_button(self, pattern: Pattern) -> Union[KeyboardButton, None]:
        compiled = re.compile(pattern)
        for row in self.rows:
            for button_text in row:
                if compiled.match(button_text):
                    return button_text
        raise NoButtonFound

    def press_button(self, pattern: Pattern, quote=False) -> Message:
        button = self._find_button(pattern)

        return self._client.send_message(
            self._peer_id,
            button,
            reply_to_message_id=self._message_id if quote else None
        )

    def press_button_await(
            self,
            pattern: Pattern,
            filters: Filter = None,
            num_expected: int = None,
            raise_: bool = True,
            quote=False,
    ) -> Response:
        button = self._find_button(pattern)

        if filters:
            filters = filters & Filters.chat(self._peer_id)
        else:
            filters = Filters.chat(self._peer_id)

        filters = filters & (Filters.text | Filters.edited)

        action = AwaitableAction(
            func=self._client.send_message,
            args=(self._peer_id, button),
            kwargs=dict(
                reply_to_message_id=self._message_id if quote else None
            ),
            filters=filters,
            num_expected=num_expected,
        )
        return self._client.act_await_response(action, raise_=raise_)


class InlineKeyboard:
    def __init__(
            self,
            client: InteractionClient,
            chat_id: int,
            message_id: int,
            button_rows: List[List[InlineKeyboardButton]]
    ):
        self._client = weakref.proxy(client)
        self._message_id = message_id
        self._peer_id = chat_id
        self.rows = button_rows

    def _find_button(self, pattern: Pattern = None, index: int = None) -> Union[InlineKeyboardButton, None]:
        if not any((pattern, index)) or all((pattern, index)):
            raise ValueError("Exactly one of the `pattern` or `index` arguments must be provided.")

        if pattern:
            compiled = re.compile(pattern)
            for row in self.rows:
                for button in row:
                    if compiled.match(button.text):
                        return button
            raise NoButtonFound
        elif index:
            try:
                return next(itertools.islice(itertools.chain.from_iterable(self.rows), index, index + 1))
            except StopIteration:
                raise NoButtonFound

    def press_button(self, pattern: Pattern = None, index: int = None):

        button = self._find_button(pattern, index)

        return self._client.press_inline_button(
            chat_id=self._peer_id,
            on_message=self._message_id,
            callback_data=button.callback_data
        )

    def press_button_await(
            self,
            pattern: Pattern = None,
            index: int = None,
            num_expected: int = None,
            max_wait=8,
            min_wait_consecutive=1.5,
            raise_: bool = True,
    ) -> Response:

        button = self._find_button(pattern, index)

        action = AwaitableAction(
            func=self._client.press_inline_button,
            args=(self._peer_id, self._message_id, button.callback_data),
            filters=Filters.chat(self._peer_id),
            num_expected=num_expected,
            max_wait=max_wait,
            min_wait_consecutive=min_wait_consecutive
        )
        return self._client.act_await_response(action, raise_=raise_)


class NoButtonFound(Exception):
    pass
