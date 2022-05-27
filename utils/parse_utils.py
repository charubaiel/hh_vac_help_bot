import time
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
import requests as r
import numpy as np
from tqdm import tqdm
import logging
import os
import yaml


logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)

FAKE_HISTORY = ['http://google.com','http://hh.ru','https://hh.ru/search/vacancy?area=&fromSearchLine=true&text=']
HEADERS = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36'}


with open('utils/params.yaml') as w:
    config = yaml.safe_load(w)
    params = config['ops']['parse_pages']['config']['search_params']
    DB_PATH = config['ops']['load_data']['config']['db_path']


def generate_query(params:dict)->str:
    base_url = 'https://hh.ru/search/vacancy?'
    query_params = '&'.join([ f'{i}={params[i]}' for i in params])
    return base_url+query_params


def parse_vacancy_pages(page)->list:
    soup = BeautifulSoup(page.text,'lxml')
    vacancys = []
    for i in soup.findAll('a',{'data-qa':'vacancy-serp__vacancy-title'}):
        vacancys.append(i['href'].split('?')[0])
    # logging.info(f'Get {len(vacancys)} vacancy urls')
    return vacancys


def get_hh_pages(params:dict)->list:
    pages = []
    with r.Session() as s:

        s.headers.update(HEADERS)
        [s.get(i) for i in FAKE_HISTORY];

        for _ in tqdm(range(params['n_pages'])):

            time.sleep(np.random.poisson(5))

            response = s.get(generate_query(params=params))

            if response.status_code == 200:
                
                pages.append(parse_vacancy_pages(response))

            params['page'] +=1
    logging.info(f'Get {len(sum(pages,[]))} vacancy urls total')    
    return sum(pages,[])



def parse_vaс(response)->dict:
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



def collect_vacancys(vacs_url_list:list)->pd.DataFrame:
    
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
    
    
def batch_load_to_db(ttl_vac_list:list,db_path = DB_PATH, user = 'ALL',query=''):
    
    conn = sqlite3.connect(db_path)   

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
    



def check_doppelgangers(vacancy_list:list,db_path = DB_PATH,user='ALL')->list:
    try:
        conn = sqlite3.connect(db_path)
        db_urls = pd.read_sql(f'select url from {user}',con=conn)['url'].tolist()
        conn.close()
        uniq = list(set(vacancy_list) - set(db_urls))
        logging.info(f'Got {len(uniq) / len(vacancy_list):.2%} uniq vacancys from parse' )
        return uniq
    except:
        logging.info(f'No uniq vacancys from parse' )
        return vacancy_list


def report_updates(chat_id,user_table,db_path=DB_PATH,bot_token = None):
    today = pd.to_datetime('now').date()
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(f'select * from {user_table} where date = "{today}"',con=conn)
    conn.close()

    df['Exp'] = df['Exp'].str.findall('\d').apply(lambda x: min(x) if x!=[] else 0).astype(int)
    df['Stack'] = df['Description'].str.findall('([A-Z][A-z]{2,})').apply(lambda x: list(set(x)))
    df['Salary'] = df['Salary'].str.replace('\xa0','').str.extract('(\d+)').astype('float')
    df['Salary'] = df['Salary'].apply(lambda x: x*80 if x < 10000 else x)

    df = df.query('Exp<3')
    jun_data = df[df.Description.str.contains('[J|j]un') | df.Name.str.contains('[J|j]un')]
    
    if jun_data.shape[0]>0:
        sorted_data = jun_data.iloc[:5].append(df.sort_values(by=['Exp','Salary'],ascending=[True,False]).head(5 - jun_data.shape[0]))
    else:
        sorted_data = df.sort_values(by=['Exp','Salary'],ascending=[True,False]).head(5)

    txt = '\n\n'.join(sorted_data.apply(lambda x:f'''Date : {x["date"]}\n\
                                                    Name : {x["Name"]}\n\
                                                        Company : {x["Company"]}\n\
                                                            Salary : {x["Salary"] / 1000:.0f}\n\
                                                                Url : {x["url"]}\n\
                                                                     Stack : {" | ".join(x["Stack"])}
                                                                        '''
                                                                    ,axis=1))

    upd = r.post(f'https://api.telegram.org/bot{bot_token}/sendMessage',data={'chat_id':chat_id,
            'text':f'''`{txt}`''',
            'parse_mode':'MarkdownV2'})
    print(upd.text)
    return txt

