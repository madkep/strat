# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement

# --- Do not remove these libs ---
from functools import reduce
from typing import Any, Callable, Dict, List

import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from skopt.space import Categorical, Dimension, Integer, Real  # noqa

from freqtrade.optimize.hyperopt_interface import IHyperOpt

# --------------------------------
# Add your lib to import here
import talib.abstract as ta  # noqa
import freqtrade.vendor.qtpylib.indicators as qtpylib


class ADXDIOPT(IHyperOpt):

    @staticmethod
    def buy_strategy_generator(params: Dict[str, Any]) -> Callable:
        """
        Define the buy strategy parameters to be used by Hyperopt.
        """

        def populate_buy_trend(dataframe: DataFrame, metadata: dict) -> DataFrame:
            """
            Buy strategy Hyperopt will build and use.
            """
            conditions = []

            # GUARDS AND TRENDS
            if params.get('adx-enabled'):
                conditions.append(dataframe['adx'] > params['adx-value'])

            if params.get('minus-enabled'):
                conditions.append(dataframe['minus_di'] > params['minus_di-value'])

            if params.get('plus-enabled'):
                conditions.append(dataframe['plus_di'] > params['plus_di-value'])

            # TRIGGERS
            if 'trigger' in params:
                if params['trigger'] == 'buy_signal':
                    conditions.append(qtpylib.crossed_above(dataframe['plus_di'],dataframe['minus_di']))

            # Check that the candle had volume
            conditions.append(dataframe['volume'] > 0)

            if conditions:
                dataframe.loc[
                    reduce(lambda x, y: x & y, conditions),
                    'buy'] = 1

            return dataframe

        return populate_buy_trend

    @staticmethod
    def indicator_space() -> List[Dimension]:
        """
        Define your Hyperopt space for searching buy strategy parameters.
        """
        return [
            Integer(0, 100, name='adx-value'),
            Integer(0, 100, name='minus_di-value'),
            Integer(0, 100, name='plus_di-value'),
            Categorical([True, False], name='adx-enabled'),
            Categorical([True, False], name='minus_di-enabled'),
            Categorical([True, False], name='plus_di-enabled'),
            Categorical(['buy_signal'], name='trigger')
        ]

    @staticmethod
    def sell_strategy_generator(params: Dict[str, Any]) -> Callable:
        """
        Define the sell strategy parameters to be used by Hyperopt.
        """

        def populate_sell_trend(dataframe: DataFrame, metadata: dict) -> DataFrame:
            """
            Sell strategy Hyperopt will build and use.
            """
            conditions = []

            # GUARDS AND TRENDS
            if params.get('sell-adx-enabled'):
                conditions.append(dataframe['sell-adx'] > params['sell-adx-value'])

            if params.get('sell-minus-enabled'):
                conditions.append(dataframe['sell-minus_di'] > params['sell-minus_di-value'])

            if params.get('sell-plus-enabled'):
                conditions.append(dataframe['sell-plus_di'] > params['sell-plus_di-value'])

            # TRIGGERS
            if 'sell-trigger' in params:

                if params['sell-trigger'] == 'sell_signal':
                    conditions.append(qtpylib.crossed_above(dataframe['sell-minus_di'], dataframe['sell-plus_di']))

            # Check that the candle had volume
            conditions.append(dataframe['volume'] > 0)

            if conditions:
                dataframe.loc[
                    reduce(lambda x, y: x & y, conditions),
                    'sell'] = 1

            return dataframe

        return populate_sell_trend

    @staticmethod
    def sell_indicator_space() -> List[Dimension]:
        """
        Define your Hyperopt space for searching sell strategy parameters.
        """
        return [
            Integer(0, 100, name='sell-adx-value'),
            Integer(0, 100, name='sell-minus_di-value'),
            Integer(0, 100, name='sell-plus_di-value'),
            Categorical([True, False], name='sell-adx-enabled'),
            Categorical([True, False], name='sell-minus_di-enabled'),
            Categorical([True, False], name='sell-plus_di-enabled'),
            Categorical(['sell_signal'], name='sell-trigger')
        ]

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                    (dataframe['adx'] > 16) &
                    (dataframe['minus_di'] > 4) &
                    (dataframe['plus_di'] > 20) &
                    (qtpylib.crossed_above(dataframe['plus_di'],dataframe['minus_di']))
 
            ),
            'buy'] = 1
        return dataframe
 
    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                    (dataframe['adx'] > 43) &
                    (dataframe['minus_di'] > 22) &
                    (dataframe['plus_di'] > 20) &
                    (qtpylib.crossed_above(dataframe['sell-minus_di'], dataframe['sell-plus_di']))
 
            ),
            'sell'] = 1
        return dataframe