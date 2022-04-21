from parse_utils import *


if __name__ == '__main__':

    import argparse
    prsr = argparse.ArgumentParser()

    prsr.add_argument('-t','--text',default='Аналитик',help='Название вакансии')
    prsr.add_argument('-np','--num_pages',default=5,type=int,help='Кол-во страниц сайта для парсинга')
    prsr.add_argument('-u','--user',default='ALL',help='Юзер для кого парсятся данные')

    args = prsr.parse_args()

    params['text'] = args.text

    vacancy_list = get_hh_pages(params,n_pages=args.num_pages)

    uniq_vacancy_list = check_doppelgangers(vacancy_list,args.user)

    batch_load_to_db(uniq_vacancy_list,args.user)
