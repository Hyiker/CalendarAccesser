#!/usr/bin/python
# -*- coding: utf-8 -*-
from requests import *
import execjs
import re
import datetime
from icalendar import Event
from icalendar import Calendar
from uuid import uuid1
from bs4 import BeautifulSoup
import argparse

cal = Calendar()
cal['version'] = '2.0'
cal['prodid'] = '-//CQUT//Syllabus//CN'  # *mandatory elements* where the prodid can be changed, see RFC 5445

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) ' \
             'Chrome/80.0.3987.116 Safari/537.36 '
# js加密方法
ctx = execjs.compile('''
    var keyStr = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='; 
    function encodeInp(input) {
    var output = "";
    var chr1, chr2, chr3 = "";
    var enc1, enc2, enc3,
        enc4 = "";
    var i = 0;
    do {
        chr1 = input.charCodeAt(i++);
        chr2 = input.charCodeAt(i++);
        chr3 = input.charCodeAt(
            i++);
        enc1 = chr1 >> 2;
        enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
        enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
        enc4 = chr3 & 63;
        if (isNaN(chr2)) {
            enc3 = enc4 = 64
        } else if (isNaN(chr3)) {
            enc4 = 64
        }
        output = output + keyStr.charAt(enc1) + keyStr.charAt(enc2) + keyStr.charAt(
            enc3) + keyStr.charAt(enc4);
        chr1 = chr2 = chr3 = "";
        enc1 = enc2 = enc3 = enc4 = ""
    } while (i < input.length);
    return output
    }
    ''')


def do_login(sess, username, password):
    sess.headers = {
        'User-Agent': user_agent
    }
    login_url = 'http://jwgl.bupt.edu.cn/jsxsd/xk/LoginToXk'
    data = {
        'userAccount': username,
        'encoded': ctx.call('encodeInp', username) + '%%%' + ctx.call('encodeInp', password),
        'userPassword': (None, "")
    }
    sess.post(
        url=login_url,
        data=data
    )
    return sess


def parse_html(soup, start_date, week):
    global cal
    table = soup.select_one('#kbtable')
    # 默认十五节课 别问为什么 问就是懒
    main_course = table.select('tr')[1:15]

    for block in main_course:
        time = re.findall(r'\d{1,2}:\d{1,2}-\d{1,2}:\d{1,2}', block.select_one('th').text)[0]
        tds = block.select('td')
        for i in range(0, len(tds)):
            if len(tds[i].text) < 10:
                continue
            title = tds[i].select_one('.kbcontent').contents[0]
            teacher = tds[i].select('font[title="老师"]')[0].text
            classroom = tds[i].select('font[title="教室"]')[0].text
            event = Event()
            event.add('uid', str(uuid1()) + '@CQUT')
            event.add('summary', title + " " + teacher)
            event.add('dtstamp', datetime.datetime.now())
            event.add('dtstart',
                      datetime.datetime.strptime(start_date + " %s:00" % time.split('-')[0],
                                                 '%Y-%m-%d %H:%M:%S') + datetime.timedelta(days=i + week * 7))
            event.add('dtend',
                      datetime.datetime.strptime(start_date + " %s:00" % time.split('-')[1],
                                                 '%Y-%m-%d %H:%M:%S') + datetime.timedelta(days=i + week * 7))
            event.add('location', classroom)
            cal.add_component(event)


def display(cal):
    return cal.to_ical().decode('utf-8').replace('\r\n', '\n').strip()


def print_cal(cal):
    print(display(cal))


def get_course_list(sess, semester, start_date, week_count):
    # 访问课程表页面
    url = 'http://jwgl.bupt.edu.cn/jsxsd/xskb/xskb_list.do'
    data = {
        'xnxq01id': semester,
        'sfFD': 1,
        'kbjcmsid': '9475847A3F3033D1E05377B5030AA94D',
        'zc': (None, '')
    }
    for i in range(week_count):
        data['zc'] = i + 1
        resp = sess.post(
            url=url,
            data=data
        )
        parse_html(BeautifulSoup(resp.text, features="html.parser"), start_date, i)


parser = argparse.ArgumentParser()

parser.add_argument('--username', required=True, help="学号")
parser.add_argument('--password', required=True, help="密码")
parser.add_argument('--semester', required=True, help="学期,形如2019-2020-2")
parser.add_argument('--startdate', required=True, help="开课第一周的星期一的日期,形如2019-10-01")
parser.add_argument('--weeks', required=True, help="要导入的周数", type=int)
parser.add_argument('--output', required=True, help="输出文件位置")
args = parser.parse_args()

s = Session()

s = do_login(s, args.username, args.password)
get_course_list(s, args.semester, args.startdate, args.weeks)
txt = display(cal)
with open('/Users/sidhch/aa.ics', 'w+') as foo:
    foo.write(txt)
    foo.close()
