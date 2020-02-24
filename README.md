# 将BUPT校园日历转化为ics文件
## 使用方法:
```shell script
python request_calendar.py --username <你的学号> --password <用户密码> --semester <学期 形如2019-2020-2> --startdate <开课第一周的星期一的日期,形如2019-10-01> --weeks <要导入的周数,形如2019-02-09> --output 输出文件位置
```
## 依赖
`requests` `execjs` `re` `iCalendar` `BeautifulSoup4`

## 注意事项
需要处于校园网环境中或者连接校园vpn