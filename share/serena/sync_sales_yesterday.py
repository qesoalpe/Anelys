from serena.sync_sales import sync_sales_daily

from datetime import date, timedelta

sync_sales_daily(date.today() - timedelta(days=1))
print('done')
