from fastcrud import FastCRUD

from ..models.timelog import TimeLog, TimeLogCreateInternal, TimeLogDelete, TimeLogUpdate, TimeLogUpdateInternal, TimeLogRead

CRUDTimelog = FastCRUD[TimeLog, TimeLogCreateInternal, TimeLogUpdate, TimeLogUpdateInternal, TimeLogDelete, TimeLogRead]
crud_timelogs = CRUDTimelog(TimeLog)
