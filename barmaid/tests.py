import datetime

date = "2022-8-26 17:45:00"
format_from = "%Y-%m-%d %H:%M:%S"
format_to = "%Y-%m-%dT%H:%M:%S"

a = datetime.datetime.strptime(date, format_from).strftime(format_to)
print(a)
