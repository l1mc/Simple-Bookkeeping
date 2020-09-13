# -*- coding: utf-8 -*-
"""
Created on Fri Jun 12 21:10:21 2020

@author: Mingcong Li
西财老师打分：90/100
"""


import pandas as pd
import numpy as np
import threading
import datetime
import copy  #用来深度复制

# 提示信息放在最上面是为了让代码更加简洁
intro1 = """
1. 类别编码和类别名称的对应关系如下：
    ①收入类：a1-生活费，a2-奖学金，a3-实习津贴，a4-补助，a5-其他
    ②支出类：b1-学习用品，b2-伙食，b3-交通，b4-衣服，b5-其他

2. 请逐笔输入类别编码、发生日期、金额、备注（各数据用英文逗号分隔,直接输入回车表示结束）：
例如：输入收支明细：a1,2020-1-26,2000.0,1月生活费
     输入收支明细：b1,2020-3-9,52.5,买书
"""

intro2 = """请输入对收入类别数据进行汇总的月份
（例如：2020-3，直接输入回车键退出）："""


def import_data():
    #如果有记录则导入记录。如果没有记录说明是第一次用，则生成一个空dataframe，以备添加数据
    try:
        global Df
        Df = pd.read_csv('record.csv', header=None, dtype={'0': np.str})  # 全局变量要首字母大写
    except:
        #Df = pd.DataFrame(columns=['type','date','amount','content'])
        Df = pd.DataFrame() #这里不用再global声明了，因为try里面的global一定会执行。和if不一样。

# 不在读取csv的时候使用parse_dates = ['1']是因为，这会导致读取的速度减慢。考虑到查询的次数一定是小于等于读取的，转换格式的步骤放在查询时进行。
def process_data():
    global Df
    global Temp
    df_temp = pd.DataFrame(Temp) #创建临时df，整理数据类型
    df_temp.iloc[:, 1] = pd.to_datetime(df_temp.iloc[:, 1]).dt.date #把日期列的格式转为日期格式，.dt.date表示去掉时间仅保留日期
    df_temp.iloc[:, 2] = pd.to_numeric(df_temp.iloc[:, 2]) #把金额转成浮点类型
    df_temp.iloc[:, [0, 3]] = df_temp.iloc[:, [0, 3]].astype(str)  # 字符串类型。
    # 统一规定数据类型，可以给用户输入带来更大的容错空间。例如输入时间的时候，有时候会写"2020-1-9"，有时候会写"2020-01-09"。如果保存成字符串，那么会很不统一，处理起来也麻烦。这里强制保存成datetime类型，随便用户怎么输入，储存起来都很统一。
    Df = Df.append(df_temp) #把多次的输入一次性添加到Df中
    Df.index=range(Df.shape[0]) #给行号重新排序


def save_data():
    Df.to_csv('record.csv',sep=',',index=False,header=False) #保存到CSV文件中
    print()
    print('------输入结束，数据已保存------')


def keep_accounts():
    global Df
    print(intro1) # 显示提示信息
    global Temp
    Temp = list() #用来收集所有输入的收支
    while True: #录入信息
        choice = input("请输入收支明细:")
        if choice == "": #输入回车结束
            break
        choice_list = choice.split(",")
        """在下面的if里还要多添加几个，判断是否输入的格式不对"""
        Temp.append(choice_list)
    if len(Temp)!=0: #如果一条新的账目都没有输入，那么不需要处理并保存数据
        process_data() #处理数据
        save_data() # 保存数据


def see_group():
    # 输入要查询的月份
    print()
    month = input(intro2)
    if month == "":  #提供退出的选项，防止用户是因为选错了才进入“分类汇总”功能的
        return
    df_see = copy.deepcopy(Df)  #这里需要一个深度复制，保持Df是不变的。否则如果运行一次程序要连着查好几次，就会出问题。因为我们要对Df的格式整个进行改变。
    df_see.iloc[:, 1] = pd.to_datetime(df_see.iloc[:, 1])
    df_see.iloc[:, 1] = df_see.iloc[:, 1].dt.year.map(str) + "-" + df_see.iloc[:, 1].dt.month.map(str) + "-" + df_see.iloc[:, 1].dt.day.map(str)  #转换成月份,DataFrame的一列就是一个Series, 可以通过map来对一列进行操作.
    df_see.columns=['类型', '日期', '金额', '备注']  # 修改列名
    df_see = df_see[df_see["日期"].apply(lambda x: x.startswith(month))]
    group_selected = df_see.groupby('类型')
    df_group = group_selected['金额'].sum().to_frame()
    df_group['收入/支出'] = np.nan
    df_group.reset_index(inplace=True)
    df_group.columns=['明细类别', '金额', '收入/支出']
    order = ['收入/支出','明细类别','金额']
    df_group = df_group[order]  # 调整列的顺序
    df_group['收入/支出'] = df_group['明细类别'].apply(lambda x:'收入' if x.startswith('a') else '支出')
    type_mapping = {'a1': '生活费', 'a2': '奖学金', 'a3': '实习津贴', 'a4': '补助', 'a5': '其他','b1': '学习用品', 'b2': '伙食', 'b3': '交通', 'b4': '衣服', 'b5': '其他',}
    df_group['明细类别'] = df_group['明细类别'].map(type_mapping)
    print(df_group)
    sum = df_group.groupby("收入/支出")["金额"].sum()
    global year_month
    year_month = month.split("-")  # 把年和月分到列表里。这种用“-”划分的好处是，月份是一位数还是两位数都能处理。
    try:
        expenses = sum['支出']
    except:
        expenses = 0
    try:
        income = sum['收入']
    except:
        income = 0
# 上面的处理方式是因为，如果某个月没有支出或者收入，有可能会报错。
    print(f"{year_month[0]}年{year_month[1]}月的总收入为{income}，总支出为{expenses}。")  # f-string用大括号 {} 表示被替换字段，其中直接填入替换内容。字符串后面的[0:4]表示提取其中的第1-4个字符
# 查询明细
    Y_N = input('是否输出该月的各笔明细（y为输出，其他为不输出）：')
    if Y_N == 'y':
        df_see['收入/支出'] = np.nan
        df_see['收入/支出'] = df_see['类型'].apply(lambda x:'收入' if x.startswith('a') else '支出')
        df_see.iloc[:, 1] = pd.to_datetime(df_see.iloc[:, 1]).dt.date
        df_see = df_see.sort_values(by = ['日期','收入/支出', '类型']) # 根据收入支出类型，和明细类型排序。明细信息优先按照日期排序。在把类型编码改成字符之前排序，可以将常用类型排在前面，把“其他”类型排在最后。
        type_mapping = {'a1': '生活费', 'a2': '奖学金', 'a3': '实习津贴', 'a4': '补助', 'a5': '其他','b1': '学习用品', 'b2': '伙食', 'b3': '交通', 'b4': '衣服', 'b5': '其他',}
        df_see['类型'] = df_see['类型'].map(type_mapping)
        order = ['类型', '收入/支出', '日期', '金额', '备注']

        df_see = df_see[order]  # 调整列的顺序
        df_see.index=range(df_see.shape[0])  # 重新编行号
        print()
        print(f"--------{year_month[0]}年{year_month[1]}月收支类别数据的明细--------")
        print(df_see)


def see_biggest():
    print()
    month = input('请输入要查询的月份：')
    if month == "":
        return
    df_biggest = copy.deepcopy(Df)
    df_biggest.columns=['类型', '日期', '金额', '备注']
    df_biggest.iloc[:, 1] = pd.to_datetime(df_biggest.iloc[:, 1])
    df_biggest.iloc[:, 1] = df_biggest.iloc[:, 1].dt.year.map(str) + "-" + df_biggest.iloc[:, 1].dt.month.map(str) + "-" + df_biggest.iloc[:, 1].dt.day.map(str)  #转换成月份,DataFrame的一列就是一个Series, 可以通过map来对一列进行操作.
    df_biggest = df_biggest[df_biggest["日期"].apply(lambda x: x.startswith(month))]
    df_biggest['收入/支出'] = np.nan
    df_biggest['收入/支出'] = df_biggest['类型'].apply(lambda x:'收入' if x.startswith('a') else '支出')
    df_biggest.iloc[:, 1] = pd.to_datetime(df_biggest.iloc[:, 1]).dt.date
    type_mapping = {'a1': '生活费', 'a2': '奖学金', 'a3': '实习津贴', 'a4': '补助', 'a5': '其他','b1': '学习用品', 'b2': '伙食', 'b3': '交通', 'b4': '衣服', 'b5': '其他',}
    df_biggest['类型'] = df_biggest['类型'].map(type_mapping)
    order = ['类型', '收入/支出', '日期', '金额', '备注']
    df_biggest = df_biggest[order]  # 调整列的顺序
    df_biggest_in = df_biggest[df_biggest["收入/支出"].apply(lambda x: x.startswith('收'))]
    df_biggest_out = df_biggest[df_biggest["收入/支出"].apply(lambda x: x.startswith('支'))]
    # 提取最大收入
    df_biggest_in = df_biggest_in.sort_values(by=['金额'], ascending=False)
    # df_biggest_in.index=range(df_biggest_in.shape[0])  # 重新编行号
    if df_biggest_in.shape[0] > 3:
        df_biggest_temp = df_biggest_in.iloc[0:3,:]
    else:
        df_biggest_temp = df_biggest_in
    # 提取最大支出
    df_biggest_out = df_biggest_out.sort_values(by=['金额'], ascending=False)
    # df_biggest_out.index=range(df_biggest_out.shape[0])  # 重新编行号
    if df_biggest_out.shape[0] > 3:
        df_biggest_temp = df_biggest_temp.append(df_biggest_out.iloc[0:3,:])
    else:
        df_biggest_temp = df_biggest_temp.append(df_biggest_out)
    print()
    year_month = month.split("-")
    print(f"--------{year_month[0]}年{year_month[1]}月金额最大的3笔收入和支出--------")
    df_biggest_temp.index=range(df_biggest_temp.shape[0])
    print(df_biggest_temp)


def main():
    t1 = threading.Thread(target=import_data) #启用多线程。经过长年累月的记账，在数据量较大地时候，如果用户边录入，程序边导入，可以减少等待时间（尤其是对机械硬盘的用户）。
    t1.start()  #导入历史数据
    prompt = '''
    1.记账
    2.分类汇总
    3.查看金额最大的3笔收入和支出
    4.退出
'''
    while True:
        CMDs={'1':keep_accounts,'2':see_group,'3':see_biggest}
        choice = input('请输入序号进行对应操作： %s: '%prompt)
        if choice not in '123':
            break
        CMDs[choice]()


if __name__=='__main__':
    main()
