from bs4 import BeautifulSoup
import requests
import json

###############################################################
#                                                             #
# https://github.com/manpages/virtuslib                       #
# Лицензия: MIT                                               #
#                                                             #
# Я не питон-гуру, так что библиотека virtuslib               #
# распространяется в виде одного .py скрипта                  #
#                                                             #
# Если кому-то не в лом завернуть её в setuptools             #
# и Makefile (пример: https://github.com/manpages/pycoin)     #
# милости просим :)                                           #
#                                                             #
# Алсо, было бы няшно переделать комменты к функциям          #
# в pydoc-совместимый формат. Опять же, если есть             #
# люди, которые этим хотят заняться — инициатива              #
# приветствуется                                              #
#                                                             #
# Библиотека на данный момент умеет фетчить самые важные      #
# данные с сайта virtus.pro и возвращать корявый              #
# виртуспрошный HTML.                                         #
#                                                             #
# Было бы неплохо иметь возможность возвращать Python         #
# объекты, этим тоже кто-нибудь может заняться.               #
#                                                             #
# Любите старкрафт.                                           #
#                                                             #
#                                                   MagBo_    #
#                                                             #
###############################################################

##
## utility functions for DOM extraction
##

# find_first(DOM tree parsed with Soup, 
#            HTML element type, 
#            HTML element attribute,
#            Desired attribute value) => element
#
# Function works in O(n) time, be careful.
def find_first(soup, element, attribute, value):
    for e in soup.find_all(element):
        if e.get(attribute) == value:
            return e
    return false

def str_between(s, left_needle, right_needle):
    seek0 = s.find(left_needle) + len(left_needle)
    s = s[seek0:]
    seek1 = s.find(right_needle)
    return s[:seek1]

##
## "constants"
##

def base_url():
     return 'http://virtus.pro'
 
def ajax_api_path():
    return '/AJAX/cached2'

def forum_path():
    return '/participate/forum'

##
## fetching remote html
##

def get_ajax_api_response(path):
    url = base_url() + ajax_api_path() + path
    return (requests.get(url)).text

def get_news():
    soup = BeautifulSoup(get_ajax_api_response('/index_news_list.php?game_news=23677&hot_news=0'))
    def is_headline(a):
        if a.get('class') == ['vp-news-header']:
            return True
        else:
            return False
    def to_object(a):
        return {'url': base_url() + a.get('href'), 'headline': a.string}
    return map(to_object, filter(is_headline, soup.find_all('a')))

def get_streams():
    done = False
    page = 0
    live = 0
    streams_per_page = 8
    buff = '<ul id="streams">'
    # 23677: game id of StarCraft II
    # 31238: some kind of weird magic number, no idea what does it do
    path = '/streams_list.php?active=Y&GAME=23677&TYPE=31238&PAGEN_1='
    def is_live(e):
        for span in e.find_all('span'):
            if span.get('class') == ['item__info']:
                for img in span.find_all('img'):
                    return True #uglyhack. Should be a better way to find an image in the span
                return False #uglyhack. If the termination wasn't ended by find_all('img') return False
    while not(done):
        page += 1
        soup = BeautifulSoup(get_ajax_api_response(path + str(page)))
        # Getting live streams from the current page
        for li in soup.find_all('li'):
            if is_live(li):
                live += 1
                buff += str(li)
        if live == streams_per_page:
            live = 0
        else:
            done = True
    return buff + '</ul>'

def get_calendar():
    page = 1
    resp = get_ajax_api_response('/calendar_list.php?page=' + str(page))
    buff = '<ul id="calendar">'
    sc2thumb = '/bitrix/cache/s1/virtus/image.show/19w_19h_clipBOTH/upload/iblock/0df/sc2_39x39.png'
    def is_starcraft_event(event):
        if event['game'] == sc2thumb:
            return True
        else:
            return False
    while resp:
        try:
            data = json.loads(resp)
        except:
            break
        page += 1
        for event in data['items']:
            if is_starcraft_event(event):
                buff += '<li>' + event['date'] + event['name'] + '</li>'
        resp = get_ajax_api_response('calendar_list.php?page=' + str(page))
    return buff + '</ul>'


def get_reports():
    return get_ajax_api_response('/reports_list.php?active=Y&active_elems=active&TM_NAME=&GAME=23677&from=&to=')

def get_forum_group(n):
    html = (requests.get(base_url() + forum_path() + "/group" + str(n) + "/")).text
    def is_forum(div):
        if div.get('class') == ['forum']:
            return True
        else:
            return False
    def to_object(div):
        def get_info(div):
            seek_for = '/forum/forum'
            div = find_first(div, 'div', 'class', ['info'])
            a = find_first(div, 'p', 'class', ['name']).find('a')
            name = a.string
            forum = str_between(a.get('href'), seek_for, '/')
            return {'name': name, 'forum': forum}
        def get_last(div):
            seek_for = '/topic'
            div = find_first(div, 'div', 'class', ['last'])
            a = find_first(div, 'p', 'class', ['name']).find('a')
            user = a.string
            topic = str_between(a.get('href'), seek_for, '/')
            return {'user': user, 'topic': topic}
        return(dict(get_info(div), last=(get_last(div))))
    return map(to_object, filter(is_forum,
                                 find_first(BeautifulSoup(html), 'div', 'class', ['forums']).find_all('div')))

def get_forum(n):
    html = (requests.get(base_url() + forum_path() + "/forum" + str(n) + "/")).text
    def is_topic(div):
        if div.get('class') == ['forum']:
            return True
        else:
            return False
    def to_object(div):
        seek_for = '/topic'
        div = find_first(div, 'div', 'class', ['info'])
        a = div.find('a')
        name = a.string
        topic = str_between(a.get('href'), seek_for, '/')
        author = find_first(div, 'p', 'class', ['author']).find('a').string
        return {'name': name, 'topic': topic, 'user': author}
    return map(to_object, filter(is_topic,
                                 find_first(BeautifulSoup(html), 'div', 'class', ['forums']).find_all('div')))

def get_topic(n,m,page):
    html = (requests.get(base_url() + forum_path() + "/forum" + str(n) +
                                                     "/topic" + str(m) + 
                                                    "/?PAGEN_1=" + str(page))).text
    soup = BeautifulSoup(html)
    mess = ''
    for container in soup.find_all(['p', 'div']):
        c = container.get('class')
        if c == ['name', 'mesLeft'] or c == ['theMessage', 'mesRight']:
            # todo: replace links to user profiles with target _blank'ed
            #       links to virtus.pro profile pages.
            mess += str(container)
    return mess

##
## login and post to a forum
##

#
# login(usr, pwd) -> session
#
def login(user, password):
    session = requests.Session()
    url = base_url() + '/auth/'
    session.get(url)
    #headers = {'cookie': req.headers['set-cookie'], 'referer': 'http://virtus.pro/auth/'}
    payload = {'AUTH_FORM': 'Y', 'TYPE': 'AUTH', 'backurl': '/auth/', 'USER_LOGIN': user, 'USER_PASSWORD': password}
    session.post(url + '?login=yes', data=payload)
    return session

def forum_post(session, forum, topic, text):
    url = base_url() + forum_path() + '/forum' + str(forum) + '/topic' + str(topic)
    req = (session.get(url)).text
    session_field="'bitrix_sessid':'"
    session_len=len('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
    x = req.find(session_field)+len(session_field)
    forum_session = req[x:x+session_len]
    payload = {'PAGE_NAME': 'read', 'FID': forum, 'TID': topic, 'MESSAGE_TYPE': 'REPLY', 'AUTHOR_ID': '',
               'forum_post_action': 'save', 'MESSAGE_MODE': 'normal', 'jsObjName': 'oLHE', 
               'sessid': forum_session, 
               'autosave_id': '251d258606ce5ab6832674c4bcf533db6',
               'POST_MESSAGE': text,
               'hidden_focus': '',
               'USE_SMILES': 'N'}
    req = session.post(base_url() + forum_path() + '/forum' + str(forum) +
                                                   '/topic' + str(topic) +
                                                   '/#postform',
                       files=None, data=payload)
    print(req.text)
    return session


if __name__ == "__main__":
    #for forum in get_forum_group('5'):
    #    print(forum)
    #for topic in get_forum(44):
    #    print(topic)
    for headline in get_news():
        print(headline)
    #print(get_calendar())
    #forum_post(login('user', 'password'), 44, 323, 'Привет из консоли!')
