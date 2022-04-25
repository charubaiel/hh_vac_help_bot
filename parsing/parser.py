from parse_utils import *


if __name__ == '__main__':

    import argparse
    prsr = argparse.ArgumentParser()

    prsr.add_argument('-t','--text',default='Analyst',type=str,help='Vacancy name')
    prsr.add_argument('-np','--num_pages',default=5,type=int,help='Num pages for parsing')
    prsr.add_argument('--chat_id',type=int,help='chat_id to report')
    prsr.add_argument('-u','--user',default='ALL',type=str,help='Searching user')
    prsr.add_argument('--report_updates',action='store_true',help='Flag to call telegram report')

    args = prsr.parse_args()

    params['text'] = args.text

    vacancy_list = get_hh_pages(params,n_pages=args.num_pages)

    uniq_vacancy_list = check_doppelgangers(vacancy_list,args.user)

    batch_load_to_db(uniq_vacancy_list,args.user)

    if args.report_updates:
        report_updates(chat_id=args.chat_id,user_table=args.user)