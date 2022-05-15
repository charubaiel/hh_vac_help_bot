
from utils.parse_utils import *
from dagster import ScheduleDefinition, DefaultScheduleStatus, job, op, repository

    
@op
def parse_pages()->list:
    return get_hh_pages(params,n_pages=params['n_pages'])

@op
def check_duplicates(vacancy_list:list)->list:
    return check_doppelgangers(vacancy_list,params['user'])

@op
def load_data(uniq_vacancy_list:list):
    return batch_load_to_db(uniq_vacancy_list,params['user'],query=params['text'])


@job
def hh_parse_job():
    load_data(check_duplicates(parse_pages()))

basic_schedule = ScheduleDefinition(job=hh_parse_job, cron_schedule=reporting['schedule_time'],execution_timezone="Europe/Moscow",default_status=DefaultScheduleStatus.RUNNING)

@repository
def hh_dagster_parse():
    return [ hh_parse_job, basic_schedule ]