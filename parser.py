from utils.parse_utils import *


if __name__ == '__main__':

    vacancy_list = get_hh_pages(params,n_pages=params['n_pages'])

    uniq_vacancy_list = check_doppelgangers(vacancy_list,params['user'])

    batch_load_to_db(uniq_vacancy_list,params['user'],query=params['text'])

    if reporting['report_updates']:
        report_updates(chat_id=reporting['user_chat_id'],user_table=params['user'])