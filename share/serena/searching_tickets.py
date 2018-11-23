for ticket in d8757_1.serena.ticket.find({'datetime': re.compile('2017-02-10.*')}):
	for sku in items_sku:
		for item in ticket['items']:
			if item['sku'] == sku:
				if sku == items_sku[-1]:
					tickets.append(ticket)
				break
		else:
			break