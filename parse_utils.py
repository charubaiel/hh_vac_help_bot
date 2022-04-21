import time
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
import requests as r
import numpy as np
from tqdm import tqdm
import logging

logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)

FAKE_HISTORY = ['http://google.com','http://hh.ru','https://hh.ru/search/vacancy?area=&fromSearchLine=true&text=']
HEADERS = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36'}


params = {'schedule':'',
            'area':1,
            'order_by':'publication_time',
            'employment':'full',
            'experience':'doesNotMatter',
            'excluded_text':'',
            'text':'DevOps',
            'search_field':'name',
            'items_on_page':20,
            'no_magic':'true',
            'page':0,
            'hhtmFrom':'vacancy_search_list'}



def generate_query(params):
    base_url = 'https://hh.ru/search/vacancy?'
    query_params = '&'.join([ f'{i}={params[i]}' for i in params])
    return base_url+query_params


def parse_vacancy_pages(page):
    soup = BeautifulSoup(page.text,'lxml')
    vacancys = []
    for i in soup.findAll('a',{'data-qa':'vacancy-serp__vacancy-title'}):
        vacancys.append(i['href'].split('?')[0])
    # logging.info(f'Get {len(vacancys)} vacancy urls')
    return vacancys


def get_hh_pages(params,n_pages=5):
    pages = []
    with r.Session() as s:

        s.headers.update(HEADERS)
        [s.get(i) for i in FAKE_HISTORY];

        for _ in tqdm(range(n_pages)):

            time.sleep(np.random.poisson(5))

            response = s.get(generate_query(params=params))

            if response.status_code == 200:
                
                pages.append(parse_vacancy_pages(response))

            params['page'] +=1
    logging.info(f'Get {len(sum(pages,[]))} vacancy urls total')    
    return sum(pages,[])



def parse_vaс(response):
    assert response.status_code == 200
    vac_soup = BeautifulSoup(response.text,'lxml')
    vac_dict = {}

    vac_dict['Name'] = vac_soup.find('h1',{'data-qa':'vacancy-title'}).text
    vac_dict['Company'] = vac_soup.find('a',{'data-qa':'vacancy-company-name'}).text
    vac_dict['Salary'] = vac_soup.find('div',{'data-qa':'vacancy-salary'}).text

    vac_dict['Exp'] = vac_soup.find('span',{'data-qa':'vacancy-experience'}).text
    vac_dict['Type'] = vac_soup.find('p',{'data-qa':'vacancy-view-employment-mode'}).text

    try:
        vac_dict['Description'] = vac_soup.find('div',{'class':'vacancy-branded-user-content'}).text
    except:
        vac_dict['Description'] = vac_soup.find('div',{'class':'g-user-content'}).text
    try:    
        vac_dict['Tags'] = vac_soup.find('div',{'class':'bloko-tag-list'}).text
    except:
        vac_dict['Tags'] = ''

    return vac_dict



def collect_vacancys(vacs_url_list):
    
    vac_data_list = []
    with r.Session() as ses:
        ses.headers.update(HEADERS)
        ses.get('http://google.com')
        ses.get('http://hh.ru')
        for vac in tqdm(vacs_url_list):

            time.sleep(np.random.poisson(3))

            vac_data_list.append(
                parse_vaс(
                    ses.get(vac)
                    )
                )

    return pd.DataFrame(vac_data_list).assign(url = vacs_url_list,date = pd.to_datetime('now').date())
    
    
def batch_load_to_db(ttl_vac_list,user = 'ALL',query=''):

    conn = sqlite3.connect('HH_vacancy.db')   

    batch_size = 27
    batch_count = len(ttl_vac_list) // batch_size +1
    logging.info(f'Total batch count : {batch_count}' )
    for idx in range(batch_count):

        idx_start = batch_size*idx
        idx_end = batch_size*(idx+1)

        batch_data = collect_vacancys(ttl_vac_list[idx_start:idx_end])

        batch_data.assign(Query=query).to_sql(name = user,con=conn,if_exists='append',index=False)

    logging.info(f'Total urls in {user} db after : {pd.read_sql(f"select count(distinct url) as uniq from {user}",con=conn).values[0]}' )    
    conn.commit()
    conn.close()
    



def check_doppelgangers(vacancy_list,user='ALL'):
    try:
        conn = sqlite3.connect('HH_vacancy.db')
        db_urls = pd.read_sql(f'select url from {user}',con=conn)['url'].tolist()
        conn.close()
        uniq = list(set(vacancy_list) - set(db_urls))
        logging.info(f'Got {len(uniq) / len(vacancy_list):.2%} uniq vacancys from parse' )
        return uniq
    except:
        logging.info(f'No uniq vacancys from parse' )
        return vacancy_list