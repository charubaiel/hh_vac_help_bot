
from utils.parse_utils import *
from dagster import DefaultScheduleStatus, job, op, repository, schedule

    
@op(description='download hh data')
def parse_pages(context)->dict:
    return {'vacancy_list':get_hh_pages(context.op_config['search_params']),
            'vacancy_name':context.op_config['search_params']['text']}



@op(description='check duplicates and load to local db')
def load_data(context,vacancy_info:dict)->None:

    uniq_vacancy_list = check_doppelgangers(vacancy_info['vacancy_list'],
                                            user = context.op_config['user'])
    context.log.info(f'Got {len(uniq_vacancy_list)} uniq vacancys from parse')
    if len(uniq_vacancy_list)>0:  

        batch_load_to_db(uniq_vacancy_list,
                        user = context.op_config['user'],
                        query = vacancy_info['vacancy_name'])

    return context.op_config['user']



@op(description='report updates in tg channel')
def report(context,user:str)->None:
    if context.op_config['report_updates']:
        report_updates(chat_id = context.op_config['user_chat_id'],
                        user_table = user,
                        bot_token=context.op_config['bot_token'])
    context.log.info('Done')



@job(config = config) 
def hh_parse_job():
    report(load_data(parse_pages()))

@schedule(job=hh_parse_job,
            cron_schedule=config['ops']['report']['config']['schedule_time'],
            execution_timezone="Europe/Moscow",
            default_status=DefaultScheduleStatus.RUNNING)
def hh_parse_schedule(context):
    return {}


@repository
def hh_dagster_parse():
    return [ hh_parse_job, hh_parse_schedule ]