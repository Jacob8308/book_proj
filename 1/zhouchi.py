'''
本程序用于自动预约同济大学羽毛球场
url=https://gym.tongji.edu.cn

tips：
1、终止预约程序快捷键
    Ctrl+C

#todo
1、加入自动查询预约结果以决定是否需要启动再预约
2、多线程进行羽毛球与网球场的多重身份预约
'''

# 引入库
import datetime
import time
import requests
import bs4 as bs
from threading import Timer

global flag  # 定义全局记录变量监测预约是否开始
flag = 0  # 一开始时预约肯定未开始
#######################*可修改参数begin*#######################
script_mode = 'cd'  # 预约脚本的模式，'cd' for count down（等待下周一八点预约），'it' for instant（立即开始预约）
#######################*可修改参数end*#######################
# 主函数


def main():
    global flag
    flag = 1  # 无需继续print倒计时数据了
    print('预约启动')
    start_time = datetime.datetime.now()

    #######################*可修改参数begin*#######################
    # 输入参数
    book_num_limit = 2  # 本次限制程序成功预约的次数
    fellow_id = '2032418'  # 同行者学号
    selected_weekdays = [1]  # 选择预约的日期，数字代表星期几
    # 输入想预约场地的开始时间（请保持格式相同，list中元素数量可改）
    selected_start_time = ['19:00', '18:00', '20:00']
    # 自己登录预约网站任意请求头中的Authorization键值（一次登录，之后无需变动）
    Authorization_code = '1e3fd33bd170541221da4114a73529c6'

    # *以下输入参数非必要无需更改！！！
    # 初始化各个场地项目编号
    campus_id = '1'  # 代表四平校区
    stadium_item_id = '2'  # 1代表羽毛球项目 2代表乒乓球 3代表网球
    stadium_id = {'panyanguan': '2'}  # 代表项目的场馆编号，用dict储存
    stadium_location_id = {'panyanguan': ['41', '42', '43', '44', '45', '46', '47', '48', '49']}  # 分别代表129的1~4号场，攀岩馆的1~4号场（5号场被嫌弃了。。。）
    #######################*可修改参数end*#######################

    # 得到可以预约的日期
    ava_date = get_available_date(selected_weekdays)

    # 查询场地预约情况，如果未被预约则发送预约post
    count = 0  # 用于记录已经成功预约了几次
    for sta_id in stadium_id:
        for date in ava_date:
            for sta_loca_id in stadium_location_id[sta_id]:
                payload = {'stadium_location_id': sta_loca_id,
                           'date_start': date}
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
                    # 这个authorization必不可少，及时重新登录选字以后也不会改变，应该是按照学号分发的密匙
                    'Authorization': Authorization_code,
                    'Connection': 'keep-alive'
                }
                ask_site = requests.post(
                    "https://gym.tongji.edu.cn/forwarding/stadiumApi/pc/checkStadiumLocationTime", headers=headers, data=payload, timeout=40)
                site_dict = ask_site.json()
                site_list = site_dict['data']['data']
                for each in site_list:
                    if (each['time_start'] in selected_start_time):
                        if each['is_check'] == 1:
                            order_count = 0   # 同一个场地尝试预约一定的次数，增加容错率
                            while order_count <= 3:
                                result_status, result = post_order(
                                    campus_id, stadium_id[sta_id], stadium_item_id, sta_loca_id, date, each['time_start'], each['time_end'], fellow_id, headers)
                                if result_status == 200:
                                    order_count = order_count+1
                                    result = result.json()['msg']
                                    if result == 'ok':
                                        count = count+1
                                        print('\n成功预约！\n次数=%s\n' % count)
                                        if count >= book_num_limit:
                                            print('已经成功完成两次预约，请登录平台进行结果查询！\n')
                                            end_time = datetime.datetime.now()
                                            print('预约结束\n预约所用时间: %s' %
                                                  (end_time-start_time))
                                            exit()
                                        break  # 还没预约完特定次数则跳出该场地预约进行下个场地的预约
                                    else:
                                        print(result)

                                else:
                                    print(result_status)
                                    break  # 如果status code不是200则是预约平台的问题，需要跳过这个场地的预约

    print('本次运行成功预约 %s 次\n未成功预约满两次！\n仍然建议上平台进行结果查询！' % count)
    end_time = datetime.datetime.now()
    print('预约结束\n预约所用时间: %s' % (end_time-start_time))
    exit()
# main主函数结束

# 本函数用于基于目前日期计算返回可以预约的日期，以便后续post查询场地情况


def get_available_date(selected_weekdays):
    ava_weekdays = []
    ava_date = []
    for i in selected_weekdays:
        if i-(datetime.datetime.now().weekday()+1) >= 0:
            ava_weekdays.append(i)
    for i in ava_weekdays:
        time_del = i-(datetime.datetime.now().weekday()+1)
        ava_datetime = datetime.datetime.now() + datetime.timedelta(days=time_del)
        ava_date.append(datetime.datetime.strftime(ava_datetime, "%Y/%m/%d"))
    return ava_date

# 本函数用于发送预约post，返回预约响应message


def post_order(cam_id, sta_id, sta_item_id, sta_loca_id, date_start, time_start, time_end, fellow_id, headers):
    payload = {
        'campus_id': cam_id,
        'stadium_id': sta_id,
        'stadium_item_id': sta_item_id,
        'stadium_location_id': sta_loca_id,
        'date_start': date_start,
        'time_start': time_start,
        'time_end': time_end,
        'together_arr[0][person_sid]': fellow_id
    }
    order = requests.post(
        "https://gym.tongji.edu.cn/forwarding/stadiumApi/pc/AppointmentLocation", headers=headers, data=payload, timeout=40)
    return order.status_code, order

# 本函数用于计算离下周一早八点的秒数，一并返回目标预约时间


def sec_del():
    day_del = 1 - (datetime.datetime.now().weekday()+1)
    if day_del < 0:  # 当已经过了周一时，预约时间在下周一
        day_del = day_del+7
    elif day_del == 0 and datetime.datetime.now().hour >= 8:  # 过了周一的八点也要将预约时间推迟到下周一
        day_del = day_del+7
    order_datetime = datetime.datetime.now()+datetime.timedelta(days=day_del)
    order_datetime = datetime.datetime(
        order_datetime.year, order_datetime.month, order_datetime.day, 8, 0)  # 得到预定场地的时间（下周一早上八点整）
    return order_datetime


#########################################################################################################

# 程序主体————根据脚本模式决定main函数运行时间
if script_mode == 'cd':
    order_datetime = sec_del()
    while flag == 0:
        time_remain = order_datetime-datetime.datetime.now()
        days = time_remain.days
        hours = time_remain.seconds//3600
        mins = (time_remain.seconds % 3600)//60
        secs = time_remain.seconds % 60
        print('离预约还有 %s天 %s小时 %s分钟 %s秒…………' % (days, hours, mins, secs), end='\r')
        time_remain = order_datetime-datetime.datetime.now()
        de_sec = time_remain.total_seconds()
        if de_sec >= 10 and de_sec < 20:  # 最后20s倒计时时开始main函数倒计时，保证倒计时的准确性
            tictoc = Timer(de_sec+60, main, ())  # 多一定时间确保系统开启预约再运行主函数
            tictoc.start()
            print('开始预约倒计时~')
        if hours>1:
            time.sleep(3600)  # 每隔1h显示倒计时
        elif mins>10:
            time.sleep(60) #  每隔1min显示倒计时
        else:
            time.sleep(1) # 每隔1s显示倒计时
elif script_mode == 'it':
    main()
else:
    print('script_mode参数错误，请见相关注释！')
