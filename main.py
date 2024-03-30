import os
from flask import Flask, render_template, request, redirect, url_for, make_response, session, send_file, jsonify
import requests as rq
import io
from copy import deepcopy as dc
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timezone
import freecurrencyapi

app = Flask('QWK')
app.secret_key = os.environ.get('app')

links = {
	'_': 'https://qwkdev.github.io/',
	'nogameshere': 'https://qwkdev.github.io/nogh/home',
	'mods': 'https://qwkdev.github.io/x',
	'sfx': 'https://qwkdev.github.io/sfx',
	'gen': 'https://qwkdev.github.io/inspects/basic',
	'csapi': 'https://raw.githubusercontent.com/qwkdev/csapi/main/data.json'
}
ltv = {i: n for n, i in enumerate(links.keys())}

with open('visits.txt') as f:
	visits = [int(i) for i in f.read().split('\n')]

def savev():
	with open('visits.txt', 'w') as f:
		f.write('\n'.join([str(i) for i in visits]))

@app.route('/')
def landing():
	return redirect('https://;url;/l/_')

@app.route('/l')
def l_view():
	resp = "// | I{} | L{} | V{} |".format(' '*((int(len(max(links, key=len))))-1), ' '*((len(max([i for i in list(links.values())], key=len)))-1), ' '*((len(max([str(i) for i in visits], key=len)))-1))
	for i in links:
		resp += "// | {}{} | {}{} | {}{} |".format(i, ' '*((int(len(max(links, key=len))))-len(i)), links[i], ' '*((len(max(list(links.values()), key=len)))-len(links[i])), visits[ltv[i]], ' '*((len(max([str(v) for v in visits], key=len)))-len(str(visits[ltv[i]]))))
	return f'<body style="margin: 0; color: #ffffff; background: #000000; font-family: monospace; font-size: 4vh;">{resp}</body>'
		

@app.route('/l/<n>', methods=['GET'])
def l(n='nogameshere'):
	global visits
	visits[ltv[n]] += 1
	rq.get('http://xdroid.net/api/message', params={
		'k': os.environ.get('XDROID'),
		't': '{}'.format(n.upper()),
		'c': '{}'.format(visits[ltv[n]]),
		'u': 'https://qwk.glitch.me/l/v/{}'.format(n)
	})
	save()
	return redirect(links[n])

@app.route('/l/v/<n>')
def l_v(n):
	return '<body style="background:#080808;color:white;font-family:monospace"><h1>Link: <a href="https://qwk.glitch.me/l/{}">qwk.glitch.me/l/{}</a><br>URL: <a href="{}">{}</a><br>Visits: {}</h1>'.format(n, n, links[n], links[n], visits[ltv[n]])

@app.route('/i/<n>')
def img(n):
	return send_file('img/{}'.format(n), mimetype='image/png')

def update_data(year):
	soup = BeautifulSoup(rq.get('https://www.eastdunbarton.gov.uk/residents/schools-and-learning/school-holidays').content, 'html.parser')

	sdata = [[[k.text.replace('\xa0', '').replace(' (Teachers)', '').replace('**', ' (May be subject to change)') for k in j.find_all('p')] for j in i.find_all('tr') if j.find_all('td') != []] for i in soup.find_all('table')]
	rdata, data = sdata[0], {'year': year, 'data': []}
	days, months = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],  ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

	def get_dates(text):
		dates = [[None, None, None]]

		if ' to ' in text:
			text = text.split(' to ')
			dates.append(dc(dates[0]))
			for n, t in enumerate(text):
				for i in days:
					if i in t: dates[n][0] = i
				for i in months:
					if i in t: dates[n][2] = i
				if dates[n][0] is not None and dates[n][2] is not None:
					dates[n][1] = int(t.replace(dates[n][0], '').replace(dates[n][2], '').replace(' ', ''))
		else:
			for i in days:
				if i in text: dates[0][0] = i
			for i in months:
				if i in text: dates[0][2] = i
			if dates[0][0] is not None and dates[0][2] is not None:
				dates[0][1] = int(text.replace(dates[0][0], '').replace(dates[0][2], '').replace(' ', ''))
			dates.append(dates[0])

		return dates

	sh_start, sh_end = None, None
	for i in sdata[0]:
		if 'last day of school' in i[0].lower():
			sh_start = i[1]; break
	for i in sdata[1]:
		if 'pupils return' in i[0].lower():
			sh_end = i[1]; break

	sh_start, sh_end = get_dates(sh_start)[0], get_dates(sh_end)[0]
	sh_start, sh_end = ' '.join([days[days.index(sh_start[0])+1], str(sh_start[1]+1), sh_start[2]]), ' '.join([days[days.index(sh_end[0])-1], str(sh_end[1]-1), sh_end[2]])

	rdata.append(['Summer Holidays', f'{sh_start} to {sh_end}'])
	rdata.extend(sdata[1])
	
	got_year = year-1
	def get_year(month):
		nonlocal got_year
		if month == 0:
			got_year += 1
		return got_year
	
	def dsuffix(dayn):
		if 10 <= dayn <= 20:
			return 'th'
		elif dayn % 10 == 1:
			return 'st'
		elif dayn % 10 == 2:
			return 'nd'
		elif dayn % 10 == 3:
			return 'rd'
		else:
			return 'th'

	for n, i in enumerate(rdata):
		if 'pupils return' not in i[0].lower() and 'pupils and teachers return' not in i[0].lower() and 'last day' not in i[0].lower():
			dates = get_dates(i[1])
			seutc = [time.mktime(datetime.strptime('-'.join([str(i[1]), str(months.index(i[2])+1), str(get_year(months.index(i[2])))]), '%d-%m-%Y').timetuple()) for i in dates]
			seutc = [seutc[0], seutc[1]+86399]
			pdates = [datetime.fromtimestamp(seutc[i]).strftime('%A %d %B') for i in range(2)]
			pdates = [f"{i.split(' ')[0]} {int(i.split(' ')[1])}{dsuffix(int(i.split(' ')[1]))} {i.split(' ')[2]}" for i in pdates]
			data['data'].append({'name': i[0], 'time': seutc, 'date': pdates})

	with open('data.json', 'w') as f:
		json.dump(data, f, indent=4)

with open('data.json') as f:
	data = json.load(f)

@app.route('/')
def index():
	now = datetime.now(timezone.utc)
	utc = now.timestamp()
	if now.year != data['year']:
		update_data(now.year)
	cur_holiday = None
	for i in data['data']:
		if i['time'][0] <= utc <= i['time'][1]:
			cur_holiday = dc(i); break
	next_holiday = [i for i in data['data'] if i['time'][0] > utc][0]
	nht2 = f"on {next_holiday['date'][0]}" if next_holiday['date'][0] == next_holiday['date'][1] else f"from {next_holiday['date'][0]} to {next_holiday['date'][1]}"
	nht = f"Next holiday is: {next_holiday['name']}, {nht2}" if next_holiday is not None else 'No upcoming holidays.'
	return f"{cur_holiday['name'] if cur_holiday is not None else 'No current holiday'}, {nht}"

@app.route('/update/<key>')
def update(key):
  if key == os.environ['key']:
	update_data(datetime.now(timezone.utc).year)
	return 'Updated.'
  return 'Wrong/No key.'

app = Flask('RATESAPI')
app.secret_key = os.environ['app']

with open('data.json') as f:
	x = json.load(f)

@app.route('/')
def index():
	return x

@app.route('/update/<key>')
def updateapi(key):
	if key == os.environ['key']:
		x = freecurrencyapi.Client(os.environ['api']).latest('GBP', 'AUD,BGN,BRL,CAD,CHF,CNY,CZK,DKK,EUR,GBP,HKD,HRK,HUF,IDR,ILS,INR,ISK,JPY,KRW,MXN,MYR,NOK,NZD,PHP,PLN,RON,RUB,SEK,SGD,THB,TRY,USD,ZAR'.split(','))['data']
		with open('data.json', 'w') as f:
			json.dump(x, f)
		return 'DONE!'
	return 'INVALID KEY.'

app.run()
