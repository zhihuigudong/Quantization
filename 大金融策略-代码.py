import statsmodels.api as sm
from statsmodels import regression
import numpy as np
import pandas as pd
import time
from datetime import date
from jqdata import *
import datetime
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from six import StringIO


#总体回测前要做的事情

def initialize(context):
   #context.zeshixinhao = ['2015-04-08']  # 择时空仓信号时间

   #set_option('futures_margin_rate', 1)
   set_params()
   set_backtest()

   # 获得所有股票
   run_monthly(handle_group, 1,'before_open')

   set_order_cost(OrderCost(open_tax=0, close_tax=0, open_commission=0.0003, close_commission=0.0013, close_today_commission=0, min_commission=0), type='stock')

#1

#设置策参数

def set_params():

    g.banknum = 5
    g.secnum = 6
    g.insnum = 4
#2

#设置回测条件

def set_backtest():

   set_option('use_real_price', True) #用真实价格交易

   log.set_level('order', 'error')

   set_benchmark('510230.XSHG')

   set_slippage(FixedSlippage(0.02))     #将滑点设置为0

#6
def handle_group(context):

    buylist_bank,bank_r = bank_stock(context)
    buylist_sec,sec_r = sec_stock(context)
    buylist_ins,ins_r = ins_stock(context)
    buylist = buylist_bank+buylist_sec+buylist_ins
    rlist = list(bank_r)+list(sec_r)+list(ins_r)

    #权重计算-市值加权
    q = query(indicator.code,valuation.circulating_market_cap).filter(indicator.code.in_(buylist))
    df = get_fundamentals(q, context.previous_date.strftime('%Y-%m-%d')).set_index('code')
    weight = df['circulating_market_cap']/df['circulating_market_cap'].sum()
    '''
    #权重计算-r值加权
    weight = rlist/sum(rlist)
    log.info(weight)
    '''
    for  stock in context.portfolio.positions:
        if stock not in buylist:
            order_target_value(stock, 0)

    for stock,w in zip(buylist,weight):
        order_target_value(stock, context.portfolio.total_value*w)


def bank_stock(context):

    stock_list = get_industry_stocks('801192')
    stock_list = filter_specials(stock_list,context)
    df=pd.DataFrame(index =stock_list, columns =['ROE','PB','growth_rate'])
    for stk1 in stock_list:
        P = get_fundamentals(query(indicator.code, valuation.pb_ratio,indicator.inc_operation_profit_year_on_year).filter(indicator.code==stk1))
        RO = get_fundamentals_continuously(query(indicator.code, indicator.roe).filter(indicator.code == stk1),count=250)
        df['PB'][stk1]=P['pb_ratio'].values
        df['ROE'][stk1] = RO['roe'].values.mean()/100
        df['growth_rate'][stk1] = P['inc_operation_profit_year_on_year'].values/100

    df = df[(df['ROE'] > -1)&(df['growth_rate'] > -1)&(df['PB'] > 0)]



    df["double_time"] =  df.apply(lambda row: round(math.log(2.0 * row['PB']/(1+row['growth_rate']) , (1.0+row['ROE'])),2), axis=1)
    #翻倍期最小的银行股
    df = df.sort("double_time")

    #输出r值
    r_list = df["double_time"][:g.banknum].values
    #r_list = ZscoreNormalization(r_list)

    print context.current_dt.strftime('%Y-%m-%d') +' 银行选股为 '+ str(df.index[:5].values)[1:-1]
    return df.index[:g.banknum],r_list#这里的数字表示买入的标的 数量，默认是5

def sec_stock(context):

    stock_list = get_industry_stocks('801193')
    stock_list = filter_specials(stock_list,context)
    df=pd.DataFrame(index =stock_list, columns =['ROE','PS','growth_rate'])
    for stk1 in stock_list:
        P = get_fundamentals(query(indicator.code, valuation.ps_ratio,indicator.inc_revenue_year_on_year).filter(valuation.code==stk1))
        RO = get_fundamentals_continuously(query(indicator.code, indicator.roe).filter(valuation.code==stk1),count=250)
        df['PS'][stk1]=P['ps_ratio'].values
        df['ROE'][stk1] = RO['roe'].values.mean()/100
        df['growth_rate'][stk1] = P['inc_revenue_year_on_year'].values/100

    df = df[(df['ROE'] > -1)&(df['growth_rate'] > -1)&(df['PS'] > 0)]


    df["double_time"] =  df.apply(lambda row: round(math.log(2.0 * row['PS']/(1+row['growth_rate']) , (1.0+row['ROE'])),2), axis=1)
    #翻倍期最小的银行股
    df = df.sort("double_time")

    #输出r值
    r_list = df["double_time"][:g.secnum].values
    #r_list = ZscoreNormalization(r_list)

    print context.current_dt.strftime('%Y-%m-%d') +' 券商选股为 '+ str(df.index[:5].values)[1:-1]
    return df.index[:g.secnum],r_list#这里的数字表示买入的标的 数量，默认是5

def ins_stock(context):

    stock_list = get_industry_stocks('801194')
    stock_list = filter_specials(stock_list,context)
    df=pd.DataFrame(index =stock_list, columns =['ROE','PS','growth_rate'])
    for stk1 in stock_list:
        P = get_fundamentals(query(indicator.code, valuation.ps_ratio,indicator.inc_operation_profit_year_on_year).filter(valuation.code==stk1))
        RO = get_fundamentals_continuously(query(indicator.code, indicator.roe).filter(valuation.code==stk1),count=250)
        df['PS'][stk1]=P['ps_ratio'].values
        df['ROE'][stk1] = RO['roe'].values.mean()/100
        df['growth_rate'][stk1] = P['inc_operation_profit_year_on_year'].values/100

    df = df[(df['ROE'] > -1)&(df['growth_rate'] > -1)&(df['PS'] > 0)]


    df["double_time"] =  df.apply(lambda row: round(math.log(2.0 * row['PS']/(1+row['growth_rate']) , (1.0+row['ROE'])),2), axis=1)
    #翻倍期最小的银行股
    df = df.sort("double_time")

    #输出r值
    r_list = df["double_time"][:g.insnum].values
    #r_list = ZscoreNormalization(r_list)

    print context.current_dt.strftime('%Y-%m-%d') +' 保险选股为 '+ str(df.index[:5].values)[1:-1]
    return df.index[:g.insnum],r_list#这里的数字表示买入的标的 数量，默认是5



#过滤退市，停牌，ST
def filter_specials(stock_list,context):
    curr_data = get_current_data()
    stock_list = [stock for stock in stock_list if \
                  (not curr_data[stock].paused)  # 未停牌
                  and (not curr_data[stock].is_st)  # 非ST
                  and ('ST' not in curr_data[stock].name)
                  and ('*' not in curr_data[stock].name)
                  and ('退' not in curr_data[stock].name)
                  and (curr_data[stock].low_limit < curr_data[stock].day_open < curr_data[stock].high_limit)                   ]
    return stock_list

def ZscoreNormalization(x):
    """Z-score normaliaztion"""
    x = (x - np.mean(x)) / np.std(x)
    return x

'''
def GrahamStockSelect(context):

   stocks = list(get_all_securities(['stock']).index) # 全部上市A股

    #调用函数获取股票代码、eps、营业利润增长率存入df

   q = query(indicator.code,indicator.eps,indicator.inc_operation_profit_year_on_year,valuation.circulating_market_cap).filter(indicator.code.in_(stocks))

   df = get_fundamentals(q, context.previous_date.strftime('%Y-%m-%d')).set_index('code')
   #调用函数获取前一交易日收盘价

   df1 = history(1, unit='1d', field='close', security_list=stocks)

   df1 = df1.T #因为得到的df1是以股票为列索引，所以将数组转置

   df1.columns=['close'] #收盘价那一列重命名为close

   df = df.join(df1) #两个数组合并



   #格氏成长股公式

   df['value'] = df['eps']*(8.5+2*df['inc_operation_profit_year_on_year'])

   df['outvalue_ratio'] = df['value']/df['close']



   #将结果从大到小排序，最后选前30只股票

   df.sort("outvalue_ratio",inplace = True, ascending = False)

   df = df[:100]



   df.sort("circulating_market_cap",inplace=True,ascending=True)

   df = df[:30]

   g.buylist = df.index

   for  stock in context.portfolio.positions:
        if stock not in g.buylist:
            order_target_value(stock, 0)
   for stock in g.buylist:
        order_target_value(stock, g.ratio_inbank*context.portfolio.total_value/len(g.buylist))

'''
