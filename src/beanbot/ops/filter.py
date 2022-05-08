#!/usr/bin/env python3
# coding=utf-8
# Filtering the transactions

from abc import ABC, abstractmethod
from typing import FrozenSet, List, Set
from beancount.core import data, interpolate
import regex as re

from beanbot.ops.conditions import is_balanced, is_predicted


class BaseFilter:
    """Base filter class that filters beancount entries according to criterions.

    This base class will pass through everything, as a default design.

    For children of `BaseFilter` class, in most cases you just need to implement
    the `_cond_impl` method. When calling filter, the implementation will automatically pass the
    entries through the filters of parent classes before calling the object's own filter implementation.
    In this way, the implementation effort of each filter can be kept minimum.
    """

    def __init__(self) -> None:
        self._inverse_condition = False

    def filter(self, entries: data.Entries) -> data.Entries:
        if self.__class__ == BaseFilter:
            return entries
        if hasattr(super(), 'filter'):
            entries = super().filter()
        return self._filter_impl(entries)

    def _filter_impl(self, entries: data.Entries) -> data.Entries:
        return [entry for entry in entries if self._test_condition(entry)]

    def _test_condition(self, entry: data.Directive) -> bool:
        condition = self._cond_impl(entry)
        if self._inverse_condition:
            condition = not condition
        return condition

    def _cond_impl(self, entry: data.Directive) -> bool:
        return True


class TransactionFilter(BaseFilter):
    """Filter that only passes transactions"""
    def _cond_impl(self, entry: data.Directive) -> bool:
        return isinstance(entry, data.Transaction)


class BalancedTransactionFilter(TransactionFilter):
    """Transaction filter to remove all unbalanced transactions"""

    def __init__(self, options_map) -> None:
        super().__init__()
        self._options_map = options_map

    def _cond_impl(self, entry: data.Directive) -> bool:
        return is_balanced(entry, self._options_map)


class UnbalancedTransactionFilter(BalancedTransactionFilter):
    """The unbalanced twin of the balanced transaction filter. Leave only the unbalanced transactions in this case."""

    def __init__(self, options_map) -> None:
        super().__init__(options_map)
        self._inverse_condition = True


# class MostRecentTransactionFilter(TransactionFilter):
#     """If more than one transaction has the same description, keep the one with the most recent date.

#     The results are expected to have a stable ordering, i.e. the order of output always respect the order of the original input."""

#     def __init__(self, extractor: AbstractTransactionExtractor):
#         super().__init__()
#         self._extractor = extractor

#     def filter(self, transactions: List[data.Transaction]) -> List[data.Transaction]:

#         descriptions = self._extractor.extract(transactions)
#         desc_to_idx = {}

#         for txn_idx, (txn, desc) in enumerate(zip(transactions, descriptions)):
#             date_txn = txn.date
#             if desc in desc_to_idx:
#                 date_prev = transactions[desc_to_idx[desc]].date
#                 if date_txn > date_prev:
#                     desc_to_idx[desc] = txn_idx
#             else:
#                 desc_to_idx[desc] = txn_idx

#         indices_latest = sorted(desc_to_idx.values())
#         transactions_latest = [transactions[idx] for idx in indices_latest]

        return transactions_latest


class PredictedTransactionFilter(TransactionFilter):
    """Return transactions that have a posting predicted by the automatic classifier"""

    def _cond_impl(self, entry: data.Directive) -> bool:
        return is_predicted(entry)
