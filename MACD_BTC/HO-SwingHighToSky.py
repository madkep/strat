# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement

import talib.abstract as ta
from pandas import DataFrame
from typing import Dict, Any, Callable, List
from functools import reduce

import numpy as np
from skopt.space import Categorical, Dimension, Integer, Real
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.optimize.hyperopt_interface import IHyperOpt

__author__      = "Kevin Ossenbrück"
__copyright__   = "Free For Use"
__credits__     = ["Bloom Trading, Mohsen Hassan"]
__license__     = "MIT"
__version__     = "1.0"
__maintainer__  = "Kevin Ossenbrück"
__email__       = "kevin.ossenbrueck@pm.de"
__status__      = "Live"

cciTimeMin = 10
cciTimeMax = 100
cciValueMin = -400
cciValueMax = 400
cciTimeRange = range(cciTimeMin, cciTimeMax)

class_name = 'HOSwingHighToSky'
class HOSwingHighToSky(IHyperOpt):

    @staticmethod
    def populate_indicators(dataframe: DataFrame, metadata: dict) -> DataFrame:

        macd = ta.MACD(dataframe, fastperiod=24, slowperiod=56, signalperiod=11)
        dataframe['macdhist'] = macd['macdhist']
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        
        for cciTime in cciTimeRange:
        
            cciName = "cci-" + str(cciTime) 
            dataframe[cciName] = ta.CCI(dataframe, timeperiod = cciTime)
            
        return dataframe

    @staticmethod
    def trailing_space() -> List[Dimension]:
        """
        Create a trailing stoploss space.
        You may override it in your custom Hyperopt class.
        """
        return [
            # It was decided to always set trailing_stop is to True if the 'trailing' hyperspace
            # is used. Otherwise hyperopt will vary other parameters that won't have effect if
            # trailing_stop is set False.
            # This parameter is included into the hyperspace dimensions rather than assigning
            # it explicitly in the code in order to have it printed in the results along with
            # other 'trailing' hyperspace parameters.
            Categorical([True], name='trailing_stop'),

            Real(0.01, 0.35, name='trailing_stop_positive'),

            # 'trailing_stop_positive_offset' should be greater than 'trailing_stop_positive',
            # so this intermediate parameter is used as the value of the difference between
            # them. The value of the 'trailing_stop_positive_offset' is constructed in the
            # generate_trailing_params() method.
            # This is similar to the hyperspace dimensions used for constructing the ROI tables.
            Real(0.001, 0.1, name='trailing_stop_positive_offset_p1'),

            Categorical([True, False], name='trailing_only_offset_is_reached'),
        ]

    @staticmethod
    def buy_strategy_generator(params: Dict[str, Any]) -> Callable:
   
        def populate_buy_trend(dataframe: DataFrame, metadata: dict) -> DataFrame:
        
            conditions = []
                
            # TRIGGERS & GUARDS
            if 'trigger' in params:
            
                for cciTime in cciTimeRange:
                
                    cciName = "cci-" + str(cciTime)
            
                    if params['trigger'] == cciName:
                        conditions.append(dataframe[cciName] < params["buy-cci-value"])
                        conditions.append(dataframe['macd'] > dataframe['macdsignal'])
                        conditions.append(dataframe['volume'] > 0)
                
            if conditions:
                dataframe.loc[reduce(lambda x, y: x & y, conditions), 'buy'] = 1

            return dataframe

        return populate_buy_trend

    @staticmethod
    def indicator_space() -> List[Dimension]:
        
        buyTriggerList = []
        
        for cciTime in cciTimeRange:
        
            cciName = "cci-" + str(cciTime)
            buyTriggerList.append(cciName)
        
        return [
            Integer(cciValueMin, cciValueMax, name='buy-cci-value'),
            Categorical(buyTriggerList, name='trigger')
        ]

    @staticmethod
    def sell_strategy_generator(params: Dict[str, Any]) -> Callable:

        def populate_sell_trend(dataframe: DataFrame, metadata: dict) -> DataFrame:
           
            conditions = []
                 
            # TRIGGERS & GUARDS
            if 'sell-trigger' in params:
            
                for cciTime in cciTimeRange:
                
                    cciName = "cci-" + str(cciTime)
            
                    if params['sell-trigger'] == cciName:
                        conditions.append(dataframe[cciName] > params["sell-cci-value"])
                        conditions.append(dataframe['macd'] < dataframe['macdsignal'])
                
            if conditions:
                dataframe.loc[reduce(lambda x, y: x & y, conditions), 'sell'] = 1

            return dataframe

        return populate_sell_trend

    @staticmethod
    def sell_indicator_space() -> List[Dimension]:
       
        sellTriggerList = []
        
        for cciTime in cciTimeRange:
        
            cciName = "cci-" + str(cciTime)
            sellTriggerList.append(cciName)
            
        return [
            Integer(cciValueMin, cciValueMax, name='sell-cci-value'),
            Categorical(sellTriggerList, name='sell-trigger')
        ]