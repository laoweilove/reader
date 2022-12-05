from requests import get, post
from os import system, name
from lxml.etree import HTML
from yaml import load, Loader
import sqlite3
from urllib.parse import quote
from sys import exit as exit_
from time import time


db = sqlite3.connect('reader.db')
courser = db.cursor()
configs = load(open('config.yaml'), Loader=Loader)
full_config = configs['config']['sites']

update_config = '''update settings  set defaultconfig = '%s' where id = 1 '''
update_bookname = '''update settings set lastbookname = '%s' where id = 1 '''
update_bookpath = '''update settings set lastbook = '%s' where id = 1 '''
update_chapter = '''update settings set lastchapter = '%s' where id = 1 '''


LOGO = '''
    
                                      
                                          _           
                         ___  ___  ___  _| | ___  ___ 
                        |  _|| -_|| .'|| . || -_||  _|
                        |_|  |___||__,||___||___||_|  
                                                      
        
                                                              by laowei
1、 search(s)   2、 setting(t)   3、 continue(c)    4、 history(h)    5、 exit(e)                                                                          
'''


class Reader(object):
    def __init__(self):
        self.settings = courser.execute('''select * from settings where id = 1 ''').fetchall()[0]
        self.default = self.settings[1]
        self.last_book = self.settings[2]
        self.last_book_name = self.settings[4]
        self.last_chapter = self.settings[3]
        self.config = full_config[self.default]
        self.chapter_url = self.last_book
        self.proxies = self.config['proxies']
        self.verify = self.config['verify']
        self.cookie = self.config['cookie']
        self.dic = {}
        self.h = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.53',
            'Cookie': self.cookie
        }

    def add_history(self, bookname):
        ts = int(time())
        x = courser.execute('''select * from history  where bookname = '%s' ''' % bookname).fetchall()

        if x:
            courser.execute(
                '''update history set lastchapter = '%d',date = '%d',config = '%s', chapterpath ='%s'  where bookname = '%s' ''' % (
                    self.last_chapter, ts, self.default, self.last_book, bookname))
            db.commit()
        else:
            courser.execute(
                '''insert into history(bookname ,chapterpath ,lastchapter ,config ,date) values('%s','%s','%d','%s','%d')''' % (
                    bookname, self.last_book, self.last_chapter, self.default, ts))
            db.commit()

    def search(self, page):

        keyword = input('search ')
        if self.config['url']['search']['method'] == 'GET' or self.config['url']['content']['method'] == 'get':
            url = self.config['url']['search']['url'].replace('{k}', quote(keyword)).replace('{p}', str(page))

            s = get(url, headers=self.h, proxies=self.proxies, verify=self.verify)
        else:
            url = self.config['url']['search']['url']
            d = self.config['url']['search']['data'].replace('{k}', quote(keyword)).replace('{p}', str(page))
            s = post(url, d, headers=self.h, proxies=self.proxies, verify=self.verify)
        s.encoding = self.config['url']['search']['encoding']
        paths = HTML(s.text).xpath(self.config['xpath']['search_path'])
        names = HTML(s.text).xpath(self.config['xpath']['search_name'])
        for i, j in enumerate(names):
            print(i, j)
        choice = input()
        book_url = paths[int(choice)]
        book_name = names[int(choice)]
        print(book_name)
        self.last_book = book_url
        self.last_book_name = book_name
        courser.execute(update_bookpath % book_url)
        courser.execute(update_bookname % book_name)
        db.commit()
        self.get_chapters(self.last_book)
        choices = [i for i in self.dic.keys()]
        for i, j in enumerate(choices):
            print(i, j)
        self.read(choices, self.last_chapter)

    @staticmethod
    def exit_e():
        system('cls' if name == 'nt' else 'clear')
        exit_()

    def setting(self):
        selections = [i for i in full_config.keys()]
        for i, j in enumerate(selections):
            print(i, full_config[j]['name'])
        selection = input('Select')
        self.default = selections[int(selection)]
        self.config = full_config[self.default]
        courser.execute(update_config % self.default)
        db.commit()
        main()

    def continue_e(self):
        self.get_chapters(self.last_book)
        choices = sorted(self.dic.keys())
        print(f'上次看到第{self.last_chapter}章，可输入{self.last_chapter}进入或回车键进入下一章')
        self.read(choices, self.last_chapter)

    def get_chapters(self, book_url):
        self.dic = {}
        if self.config['url']['chapter']['method'] == 'GET' or self.config['url']['content']['method'] == 'get':
            url = self.config['url']['chapter']['url'].replace('{c}', book_url)
            s = get(url, headers=self.h, proxies=self.proxies, verify=self.verify)
        else:
            url = self.config['url']['chapter']['url']
            d = self.config['url']['chapter']['data'].replace('{c}', book_url)
            s = post(url, d, headers=self.h, proxies=self.proxies, verify=self.verify)
        s.encoding = self.config['url']['chapter']['encoding']
        chapter_urls = HTML(s.text).xpath(self.config['xpath']['chapter_path'])
        chapter_names = HTML(s.text).xpath(self.config['xpath']['chapter_name'])
        for i, j in enumerate(chapter_names):
            self.dic.update({j: chapter_urls[i]})

    def read(self, choices, page):
        choice = input(
            '\n\n\n--------------------------------\n\n\n 上一章（previous/p/P） 下一章（next/n/N/enter） 搜书 (search/s/S) 主界面 (back/b/B)  清屏（clear/c/C） 退出（exit/e/E）\n\n\n--------------------------------\n\n\n')

        while choice is not None:
            if choice == 'clear' or choice == 'c' or choice == 'C':
                system('cls' if name == 'nt' else 'clear')
            elif choice == 'e' or choice == 'exit' or choice == 'E':
                self.exit_e()
            elif choice == 'b' or choice == 'B' or choice == 'back':
                main()
            elif choice == 's' or choice == 'S' or choice == 'search':
                self.search(0)
            else:
                if choice == 'n' or choice == 'N' or choice == 'next' or choice == '':
                    page = page + 1
                elif choice == 'p' or choice == 'previous' or choice == 'P':
                    page = page - 1
                else:
                    try:
                        page = int(choice)

                    except Exception as error_info:
                        print(error_info)
                        self.exit_e()
                self.last_chapter = page
                courser.execute(update_chapter % page)
                db.commit()
                self.add_history(self.last_book_name)
                cc = self.dic[choices[self.last_chapter]]
                if self.config['url']['content']['method'] == 'GET' or self.config['url']['content']['method'] == 'get':
                    url = self.config['url']['content']['url'].replace('{o}', cc)
                    s = get(url, headers=self.h, proxies=self.proxies, verify=self.verify)
                else:
                    url = self.config['url']['content']['url']
                    d = self.config['url']['content']['data'].replace('{o}', cc)
                    s = post(url, d, headers=self.h, proxies=self.proxies, verify=self.verify)
                s.encoding = self.config['url']['content']['encoding']
                x = HTML(s.text).xpath(self.config['xpath']['content'])
                print('\n'.join(x))
                print(
                    '\n\n\n----------------------------------------------------------------------------------------------------------------\n\n\n'
                    ' 上一章（previous/p/P） 下一章（next/n/N/enter） 搜书 (search/s/S) 主界面 (back/b/B)  清屏（clear/c/C） 退出（exit/e/E）\n\n\n'
                    '----------------------------------------------------------------------------------------------------------------\n\n\n')
            choice = input()

    def history_e(self):
        x = courser.execute('''select * from history  order by date desc''').fetchall()
        for i, j in enumerate(x):
            print(i, j[1], j[3], j[4])

        choice = int(input('Choose'))
        history = x[choice]
        self.default = history[4]
        self.last_book = history[2]
        self.last_book_name = history[1]
        self.last_chapter = history[3]
        self.config = full_config[self.default]
        self.chapter_url = self.last_book
        self.continue_e()


def main():
    print(LOGO)
    m = Reader()
    choice = input('')
    if choice == '1' or choice == 'search' or choice == 's':
        m.search(1)
    elif choice == '2' or choice == 'setting' or choice == 't':
        m.setting()
    elif choice == '3' or choice == 'continue' or choice == 'c' or choice == '':
        m.continue_e()
    elif choice == '4' or choice == 'history' or choice == 'h':
        m.history_e()
    elif choice == '5' or choice == 'exit' or choice == 'e':
        m.exit_e()


if __name__ == '__main__':
    main()
