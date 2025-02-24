from fastcrud import FastCRUD

from ..models.timelog import TimeLog, TimeLogCreateInternal, TimeLogDelete, TimeLogUpdate, TimeLogUpdateInternal

CRUDTimelog = FastCRUD[TimeLog, TimeLogCreateInternal, TimeLogUpdate, TimeLogUpdateInternal, TimeLogDelete]
crud_timelogs = CRUDTimelog(TimeLog)
