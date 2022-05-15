
from utils.parse_utils import *
from dagster import ScheduleDefinition, DefaultScheduleStatus, job, op, repository

with open('utils/dagster_params.yaml') as w:
    config = yaml.safe_load(w)
    
@op
def parse_pages(context)->list:
    return get_hh_pages(context.op_config['search_params'])

@op
def check_duplicates(context,vacancy_list:list)->list:
    return check_doppelgangers(vacancy_list,context.op_config['search_params']['user'])

@op
def load_data(context,uniq_vacancy_list:list):
    return batch_load_to_db(uniq_vacancy_list,context.op_config['search_params']['user'],
                            query=context.op_config['search_params']['text'])


@job(config= config) 
def hh_parse_job():
    load_data(check_duplicates(parse_pages()))

basic_schedule = ScheduleDefinition(job=hh_parse_job,
                                    cron_schedule=reporting['schedule_time'],
                                    execution_timezone="Europe/Moscow",
                                    default_status=DefaultScheduleStatus.RUNNING)

@repository
def hh_dagster_parse():
    return [ hh_parse_job, basic_schedule ]