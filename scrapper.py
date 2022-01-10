#!/usr/bin/python
# -*- coding: utf-8 -*-

# python scrapper.py -more="4.0" -less="6.0"

import argparse
import cookielib
import sys
import urllib2
import zlib
from HTMLParser import HTMLParser
from random import randint
from time import sleep

import datetime
import xlsxwriter
from bs4 import BeautifulSoup
from datetime import timedelta

parser = argparse.ArgumentParser(description="")
parser.add_argument('-more')
parser.add_argument('-less')
parser.add_argument('-day')
args = parser.parse_args()

TOMORROW = str((datetime.datetime.now() + timedelta(1)).strftime("%d/%m/%Y"))
TODAY = str(datetime.datetime.now().strftime("%d/%m/%Y"))

# more_than = float(args.more)
# less_than = float(args.less)

try:
    more_than = float(args.more)
    less_than = float(args.less)
except:
    more_than = float('1.0')
    less_than = float('4.75')

try:
    day = str(args.day).upper()
    if day not in ('TODAY', 'TOMORROW'):
        raise Exception('INVALID_DAY_PARAM')
except:
    day = 'TODAY'

xls_file_name = str(datetime.datetime.now().strftime("%Y%m%d_%H%M%S.xlsx"))

reload(sys)
sys.setdefaultencoding('utf-8')

HOST = 'www.soccerstats.com'
COOKIE_URI = 'soccerstats.cookie'

cookies = cookielib.LWPCookieJar(COOKIE_URI)
handlers = [
    urllib2.HTTPHandler(),
    urllib2.HTTPCookieProcessor(cookies)
]

# cookies.load()


cookies.save(COOKIE_URI)

opener = urllib2.build_opener(*handlers)
urllib2.install_opener(opener)

h = HTMLParser()


def str_encode(str):
    return str.encode('utf-8').replace('&#39;', "'").replace('&AMP;', '&').replace('&amp;', '&')


def dump():
    for cookie in cookies:
        print cookie


def get_coockie(url):
    buff = []
    for c in cookies:
        if c.domain == url:
            buff.append(c.name + '=' + c.value)

    return '; '.join(buff)


def gzip_decode(data):
    return zlib.decompress(data, 16 + zlib.MAX_WBITS)


def get_html_content(url):
    request_cookie = get_coockie(HOST)

    req = urllib2.Request(url, None, {'Host': HOST,
                                      'Connection': 'keep-alive',
                                      'Pragma': 'no-cache',
                                      'Cache-Control': 'no-cache',
                                      'Upgrade-Insecure-Requests': 1,
                                      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
                                      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                                      'Accept-Encoding': 'gzip, deflate',
                                      'Accept-Language': 'tr,en-US;q=0.8,en;q=0.6,ru;q=0.4',
                                      'Cookie': request_cookie})

    sleep(randint(5, 300) / 100)
    response = urllib2.urlopen(req)
    cookies.save(COOKIE_URI)

    return response.read().decode('utf-8', 'ignore')


def percentiles_to_fractional(value):
    if value:
        value = value.replace('%', '').strip()
        value = float(value) / 100

    return value


def get_league_status(url):
    content = BeautifulSoup(get_html_content(url))
    tables = content.find('div', {'id': 'container'}).find('div', {'id': 'content'}).findAll('div', {'class': 'row'},
                                                                                             recursive=False)[2].find(
        'div', {'class': 'seven columns'}).findAll('table', recursive=False)

    matches = h.unescape(tables[10].find('tr').findAll('td', recursive=False)[1]).text
    matches = matches.split(':')[1]

    matches_played = int(matches.split('matches')[0])
    total_matches = int(matches.split('/')[1])

    over_25_goals = percentiles_to_fractional(
        h.unescape(tables[11].findAll('tr', recursive=False)[1].findAll('td', recursive=False)[4]).text)
    over_p_match = float(
        h.unescape(tables[11].findAll('tr', recursive=False)[4].findAll('td', recursive=False)[1]).text)
    over_p_match_away = float(
        h.unescape(tables[11].findAll('tr', recursive=False)[4].findAll('td', recursive=False)[4]).text)
    over_p_match_home = float(
        h.unescape(tables[11].findAll('tr', recursive=False)[3].findAll('td', recursive=False)[4]).text)

    return {'matches_played': matches_played, 'total_matches': total_matches, 'over_25_goals': over_25_goals,
            'over_p_match': over_p_match,
            'over_p_match_home': over_p_match_home, 'over_p_match_away': over_p_match_away}


def get_goals(content):
    result = [0, 0, 0, 0]

    favor = 0
    against = 0
    team_name = h.unescape(content[0].findAll("td", recursive=False)[1].find("b")).text.strip()

    for rec in content:
        td_list = rec.findAll("td", recursive=False)
        teams = str_encode(h.unescape(td_list[1]).text.replace('&nbsp;', '')).replace(' -', '#').replace('- ',
                                                                                                         '#').split('#')

        teams[0] = teams[0].strip().encode('ascii','ignore')
        teams[1] = teams[1].strip().encode('ascii','ignore')

        scores = h.unescape(td_list[2]).text.split('-')
        scores[0] = scores[0].strip()
        scores[1] = scores[1].strip()

        if str(teams[0]) == str(team_name):
            favor += int(scores[0])
            against += int(scores[1])
        elif str(teams[1]) == str(team_name):
            favor += int(scores[1])
            against += int(scores[0])
        else:
            print td_list
            raise Exception("An error occured on goals")

    result[0] = favor
    result[1] = against

    # ------------------------

    favor = 0
    against = 0
    team_name = h.unescape(content[0].findAll("td", recursive=False)[5].find("b")).text.strip()

    for rec in content:
        td_list = rec.findAll("td", recursive=False)
        teams = str_encode(h.unescape(td_list[5]).text.replace('&nbsp;', '')).replace(' -', '#').replace('- ',
                                                                                                         '#').split('#')
        teams[0] = teams[0].strip().encode('ascii','ignore')
        teams[1] = teams[1].strip().encode('ascii','ignore')

        scores = h.unescape(td_list[4]).text.split('-')
        scores[0] = scores[0].strip()
        scores[1] = scores[1].strip()

        if str(teams[0]) == str(team_name):
            favor += int(scores[0])
            against += int(scores[1])
        elif str(teams[1]) == str(team_name):
            favor += int(scores[1])
            against += int(scores[0])
        else:
            print td_list
            raise Exception("An error occured on goals")

    result[2] = favor
    result[3] = against

    return result


def try_to_get_league(content):
    td_list = content.findAll("td", recursive=False)
    if len(td_list) == 2:
        font_elem = td_list[0].find("font", recursive=False)
        return str_encode(h.unescape(font_elem).text.replace(' -', ' - '))
    raise Exception('Invalid league content')


def try_to_get_stats_url(content):
    td_list = content.findAll("td", recursive=False)
    if len(td_list) == 2:
        url = 'http://' + HOST + '/' + td_list[1].find('a')['href']
        return url
    raise Exception('Invalid stats url content')


def get_statics(url, date_text):
    all_data = []
    content = BeautifulSoup(get_html_content(url))
    match_lines = content.findAll("tr")

    league = ''
    for match_line in match_lines:
        # print match_line

        try:
            class_val = match_line['class']
            if type(class_val).__name__ == 'list':
                class_val = class_val[0]
        except:
            class_val = 'trow-1'

        if str(class_val) == 'trow2' and len(match_line.findAll("td", recursive=False)) == 2:
            try:
                league = try_to_get_league(match_line)
                stats_url = try_to_get_stats_url(match_line)
                league_stats = get_league_status(stats_url)
            except:
                pass

            continue

        if str(class_val) != 'trow8':
            continue

        td_list = match_line.findAll("td", recursive=False)

        try:
            team1_tg = float(h.unescape(td_list[5]).text)
            team2_tg = float(h.unescape(td_list[13]).text)
        except:
            team1_tg, team2_tg = None, None

        if not team1_tg or not team2_tg:
            continue

        if not (more_than < (team1_tg + team2_tg)):
            continue

        if not (less_than > (team1_tg + team2_tg)):
            continue

        try:
            stats_url = 'http://' + HOST + '/' + str(match_line.findAll("a")[0]['href'])
        except:
            stats_url = None

        if not stats_url:
            continue

        if not (stats_url.split('?')[0] == 'http://www.soccerstats.com/pmatch.asp'):
            continue

        try:
            stats_content = BeautifulSoup(get_html_content(stats_url))
        except:
            stats_content = None

        if not stats_content:
            continue

        team1 = str_encode(h.unescape(td_list[8]).text).upper()
        team2 = str_encode(h.unescape(td_list[10]).text).upper()

        # print team1 + ' - ' + team2
        # print stats_url

        # league = str_encode(h.unescape(stats_content.find("select", {"name": "countryLeague"}).find("option")).text)
        # print league

        try:
            content_columns = \
                stats_content.find("body").find("div", {"id": "container"}).find("div", {"id": "content"}).findAll(
                    "div", recursive=False)[2].find("div", {"class": "row"}).findAll("div", recursive=False)
        except:
            content_columns = None
            # Second try
            try:
                content_columns = \
                    stats_content.find("body").findAll("div", recursive=False)[2].find("div", {"class": "row"}).findAll(
                        "div", recursive=False)
            except:
                content_columns = None

        if not content_columns:
            continue

        table4_content = content_columns[0].findAll("table", recursive=False)[2]
        table5_content = content_columns[1].findAll("table", recursive=False)[6]

        # --- table4
        table4_content = table4_content.findAll("tr", recursive=False)
        if len(table4_content) != 8:
            continue

        try:
            goals = get_goals(table4_content)
        except:
            goals = None

        if not goals:
            continue
        # --- table4


        # --- table5
        # Goals scored per match
        try:
            table5_line1_content = table5_content.findAll("tr", recursive=False)[3].findAll("td", recursive=False)
            t1_hm_gl_scrd_pr_mtch = h.unescape(table5_line1_content[0].find("b")).text
            t1_tll_gl_scrd_pr_mtch = h.unescape(table5_line1_content[1]).text
            t2_tll_gl_scrd_pr_mtch = h.unescape(table5_line1_content[3]).text
            t2_wy_gl_scrd_pr_mtch = h.unescape(table5_line1_content[4].find("b")).text
        except:
            continue



        # print t1_hm_gl_scrd_pr_mtch + '-' + t1_tll_gl_scrd_pr_mtch + '-' + t2_tll_gl_scrd_pr_mtch + '-' + t2_wy_gl_scrd_pr_mtch

        # Goals conceded per match
        table5_line2_content = table5_content.findAll("tr", recursive=False)[4].findAll("td", recursive=False)

        t1_hm_gl_cncd_pr_mtch = h.unescape(table5_line2_content[0].find("b")).text
        t1_tll_gl_cncd_pr_mtch = h.unescape(table5_line2_content[1]).text
        t2_tll_gl_cncd_pr_mtch = h.unescape(table5_line2_content[3]).text
        t2_wy_gl_cncd_pr_mtch = h.unescape(table5_line2_content[4].find("b")).text

        # print t1_hm_gl_cncd_pr_mtch + '-' + t1_tll_gl_cncd_pr_mtch + '-' + t2_tll_gl_cncd_pr_mtch + '-' + t2_wy_gl_cncd_pr_mtch

        # Matches over 2.5 goals
        for rec in table5_content.findAll("font"):
            rec.decompose()
        table5_line3_content = table5_content.findAll("tr", recursive=False)[7].findAll("td", recursive=False)

        t1_hm_mtch_vr = percentiles_to_fractional(h.unescape(table5_line3_content[0].find("b")).text)
        t1_tll_mtch_vr = percentiles_to_fractional(h.unescape(table5_line3_content[1]).text.replace('&nbsp;', ''))
        t2_tll_mtch_vr = percentiles_to_fractional(h.unescape(table5_line3_content[3]).text.replace('&nbsp;', ''))
        t2_wy_mtch_vr = percentiles_to_fractional(h.unescape(table5_line3_content[4].find("b")).text)

        # print t1_hm_mtch_vr + '-' + t1_tll_mtch_vr + '-' + t2_tll_mtch_vr + '-' + t2_wy_mtch_vr

        # ---table5


        data = [str(date_text), str(league), team1, team2,
                goals[0], goals[1], goals[2], goals[3],
                float(t1_hm_gl_scrd_pr_mtch),
                float(t1_tll_gl_scrd_pr_mtch),
                float(t2_tll_gl_scrd_pr_mtch),
                float(t2_wy_gl_scrd_pr_mtch),
                float(t1_hm_gl_cncd_pr_mtch),
                float(t1_tll_gl_cncd_pr_mtch),
                float(t2_tll_gl_cncd_pr_mtch),
                float(t2_wy_gl_cncd_pr_mtch),
                t1_hm_mtch_vr,
                t1_tll_mtch_vr,
                t2_tll_mtch_vr,
                t2_wy_mtch_vr,
                league_stats['matches_played'],
                league_stats['total_matches'],
                league_stats['over_25_goals'],
                league_stats['over_p_match'],
                league_stats['over_p_match_home'],
                league_stats['over_p_match_away']
                ]

        print data
        all_data.append(data)
    return all_data


# Create a workbook and add a worksheet.
workbook = xlsxwriter.Workbook('outputs/' + xls_file_name)

if day == 'TODAY':
    worksheet = workbook.add_worksheet(
        name=str(datetime.datetime.now().strftime("%Y%m%d")) + ' ' + str(more_than) + '-' + str(less_than))

    row_index = 0

    worksheet.write(row_index, 0, 'DATE')
    worksheet.write(row_index, 1, 'LEAGUE')
    worksheet.write(row_index, 2, 'TEAM 1')
    worksheet.write(row_index, 3, 'TEAM 2')
    worksheet.write(row_index, 4, 'TEAM 1 GOALS IN FAVOR')
    worksheet.write(row_index, 5, 'TEAM 1 GOALS IN AGAINST')
    worksheet.write(row_index, 6, 'TEAM 2 GOALS IN FAVOR')
    worksheet.write(row_index, 7, 'TEAM 2 GOALS IN AGAINST')
    worksheet.write(row_index, 8, 'TEAM 1 (Home) Goals scored per match')
    worksheet.write(row_index, 9, 'TEAM 1 (Total) Goals scored per match')
    worksheet.write(row_index, 10, 'TEAM 2 (Total) Goals scored per match')
    worksheet.write(row_index, 11, 'TEAM 2 (Away) Goals scored per match')
    worksheet.write(row_index, 12, 'TEAM 1 (Home) Goals conceded per match')
    worksheet.write(row_index, 13, 'TEAM 1 (Total) Goals conceded per match')
    worksheet.write(row_index, 14, 'TEAM 2 (Total) Goals conceded per match')
    worksheet.write(row_index, 15, 'TEAM 2 (Away) Goals conceded per match')
    worksheet.write(row_index, 16, 'TEAM 1 (Home) Matches over 2.5 goals')
    worksheet.write(row_index, 17, 'TEAM 1 (Total) Matches over 2.5 goals')
    worksheet.write(row_index, 18, 'TEAM 2 (Total) Matches over 2.5 goals')
    worksheet.write(row_index, 19, 'TEAM 2 (Away) Matches over 2.5 goals')

    worksheet.write(row_index, 20, 'MATCHES PLAYED')
    worksheet.write(row_index, 21, 'TOTAL MATCHES')
    worksheet.write(row_index, 22, 'OVER 2,5 GOALS')
    worksheet.write(row_index, 23, 'GOALS P. MATCH')
    worksheet.write(row_index, 24, 'GOALS P. MATCH (HOME)')
    worksheet.write(row_index, 25, 'GOALS P. MATCH (AWAY)')

    row_index = 1

    today_data = get_statics('http://www.soccerstats.com/matches.asp', TODAY)
    for data in today_data:
        for i in range(0, len(data)):
            worksheet.write(row_index, i, data[i])

        row_index += 1

if day == 'TOMORROW':
    content = BeautifulSoup(get_html_content('http://www.soccerstats.com/matches.asp'))
    tomorrow_url = 'http://' + HOST + '/' + str(content.find("body")
                                                .find("div", {"id": "container"})
                                                .find("div", {"id": "content"})
                                                .find("div", {"class": "row"})
                                                .find("div", {"class": "twelve columns"})
                                                .findAll("table", recursive=False)[0].findAll("tr", recursive=False)[
                                                    0].find("tr", {"class": "trow2"}).findAll("td", recursive=False)[
                                                    4].find("a")['href'])

    worksheet2 = workbook.add_worksheet(
        name=str((datetime.datetime.now() + timedelta(1)).strftime("%Y%m%d")) + ' ' + str(more_than) + '-' + str(
            less_than))

    row_index = 0

    worksheet2.write(row_index, 0, 'DATE')
    worksheet2.write(row_index, 1, 'LEAGUE')
    worksheet2.write(row_index, 2, 'TEAM 1')
    worksheet2.write(row_index, 3, 'TEAM 2')
    worksheet2.write(row_index, 4, 'TEAM 1 GOALS IN FAVOR')
    worksheet2.write(row_index, 5, 'TEAM 1 GOALS IN AGAINST')
    worksheet2.write(row_index, 6, 'TEAM 2 GOALS IN FAVOR')
    worksheet2.write(row_index, 7, 'TEAM 2 GOALS IN AGAINST')
    worksheet2.write(row_index, 8, 'TEAM 1 (Home) Goals scored per match')
    worksheet2.write(row_index, 9, 'TEAM 1 (Total) Goals scored per match')
    worksheet2.write(row_index, 10, 'TEAM 2 (Total) Goals scored per match')
    worksheet2.write(row_index, 11, 'TEAM 2 (Away) Goals scored per match')
    worksheet2.write(row_index, 12, 'TEAM 1 (Home) Goals conceded per match')
    worksheet2.write(row_index, 13, 'TEAM 1 (Total) Goals conceded per match')
    worksheet2.write(row_index, 14, 'TEAM 2 (Total) Goals conceded per match')
    worksheet2.write(row_index, 15, 'TEAM 2 (Away) Goals conceded per match')
    worksheet2.write(row_index, 16, 'TEAM 1 (Home) Matches over 2.5 goals')
    worksheet2.write(row_index, 17, 'TEAM 1 (Total) Matches over 2.5 goals')
    worksheet2.write(row_index, 18, 'TEAM 2 (Total) Matches over 2.5 goals')
    worksheet2.write(row_index, 19, 'TEAM 2 (Away) Matches over 2.5 goals')

    worksheet2.write(row_index, 20, 'MATCHES PLAYED')
    worksheet2.write(row_index, 21, 'TOTAL MATCHES')
    worksheet2.write(row_index, 22, 'OVER 2,5 GOALS')
    worksheet2.write(row_index, 23, 'GOALS P. MATCH')
    worksheet2.write(row_index, 24, 'GOALS P. MATCH (HOME)')
    worksheet2.write(row_index, 25, 'GOALS P. MATCH (AWAY)')

    row_index = 1

    tomorrow_data = get_statics(tomorrow_url, TOMORROW)
    for data in tomorrow_data:
        for i in range(0, len(data)):
            worksheet2.write(row_index, i, data[i])

        row_index += 1

workbook.close()
