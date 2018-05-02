# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

import hashlib
import logging

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError
from sawtooth_sdk.processor.core import TransactionProcessor

LOGGER = logging.getLogger(__name__)

FAMILY_NAME = "simplewallet"


def _hash(data):
    return hashlib.sha512(data).hexdigest()


sw_namespace = _hash(FAMILY_NAME.encode('utf-8'))[0:6]


class SWTransactionHandler(TransactionHandler):
    def __init__(self, namespace_prefix):
        self._namespace_prefix = namespace_prefix

    @property
    def family_name(self):
        return 'simplewallet'

    @property
    def family_versions(self):
        return ['1.0']

    @property
    def namespaces(self):
        return [self._namespace_prefix]

    def apply(self, transaction, context):

        header = transaction.header

        payload_list = transaction.payload.decode().split(",")

        operation = payload_list[0]
        amount = payload_list[1]
        to_key = payload_list[2]
        from_key = header.signer_public_key

        if operation == "deposit":
            self._make_deposit(context, amount, from_key)

        if operation == "withdraw":
            self._make_withdraw(context, amount, from_key)

        if operation == "transfer":
            self._make_transfer(context, amount, to_key, from_key)

    def _make_deposit(self, context, amount, from_key):

        wallet_key = self._get_wallet_key(from_key)
        LOGGER.info('Got the key {} and the wallet key {} '.format(from_key, wallet_key))

        current_entry = context.get_state(wallet_key)
        balance = str(current_entry)
        new_balance = 0

        if balance == "":
            LOGGER.info('No previous deposits, creating new deposit {} '.format(from_key))
            new_balance = amount
        else:
            new_balance = amount + balance

        state_data = new_balance.encode()

        addresses = context.set_state(
            {self._get_wallet_key(from_key): state_data})

        if len(addresses) < 1:
            raise InternalError("State Error")

    def _make_withdraw(self, context, amount, from_key):

        wallet_key = self._get_wallet_key(from_key)
        LOGGER.info('Got the key {} and the wallet key {} '.format(from_key, wallet_key))

        current_entry = context.get_state(wallet_key)
        balance = str(current_entry)
        new_balance = 0

        if balance == "":
            LOGGER.info('No user with the key {} '.format(from_key))
        else:
            value = int(balance)
            if value < amount:
                LOGGER.info('Not enough money. Tha amount should be lesser or equal to {} '.format(value))
            else:
                new_balance = value - amount

        LOGGER.info('Withdrawing {} '.format(amount))
        state_data = new_balance.encode()

        addresses = context.set_state(
            {self._get_wallet_key(from_key): state_data})

        if len(addresses) < 1:
            raise InternalError("State Error")

    def _make_transfer(self, context, amount, to_key, from_key):
        pass

    def _get_wallet_key(self, from_key):
        return _hash(sw_namespace.encode('utf-8'))[0:6] + _hash(from_key.encode('utf-8'))[0:64]


def main():
    processor = TransactionProcessor(url='tcp://localhost:4004')

    handler = SWTransactionHandler(sw_namespace)

    processor.add_handler(handler)

    processor.start()


if __name__ == "__main__":
    main()