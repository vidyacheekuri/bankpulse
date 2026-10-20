"""Shared metric definitions used by the dashboard and regression tests."""
import math
import pandas as pd

def filter_records(df, start, end, products=None, companies=None, states=None, timely=None):
    """Both selected dates inclusive; all dates are normalized UTC calendar days."""
    if pd.Timestamp(start)>pd.Timestamp(end):raise ValueError('Start date must not follow end date')
    mask=df.received.between(pd.Timestamp(start),pd.Timestamp(end))
    for col,values in [('product',products),('company',companies),('state',states)]:
        if values is not None:mask &= df[col].isin(values)
    if timely is not None:mask &= df.timely.eq(timely)
    return df.loc[mask].copy()

def kpis(df):
    yes=int(df.timely.eq('Yes').sum());no=int(df.timely.eq('No').sum())
    return {'complaints':len(df),'timely_yes':yes,'timely_no':no,'known':yes+no,'unknown':len(df)-yes-no,'timely_rate':yes/(yes+no) if yes+no else None}

def monthly(df,start,end):
    calendar=pd.date_range(pd.Timestamp(start).replace(day=1),pd.Timestamp(end).replace(day=1),freq='MS')
    grouped=df.groupby('month').agg(complaints=('complaint_id','size'),timely_yes=('is_timely','sum'),known=('is_known','sum'))
    out=grouped.reindex(calendar,fill_value=0).rename_axis('month').reset_index()
    out['timely_rate']=out.timely_yes.div(out.known.where(out.known.ne(0)))
    out['rolling_3m']=out.complaints.rolling(3,min_periods=3).mean()
    out['mom_pct']=out.complaints.pct_change(fill_method=None).where(out.complaints.shift().gt(0))*100
    return out

def issue_changes(df,previous,current,min_count=30,threshold=25):
    """Dense endpoints; disappearing issues remain visible. New issues have no % baseline."""
    a=df.loc[df.month.eq(pd.Timestamp(previous))].groupby('issue').size()
    b=df.loc[df.month.eq(pd.Timestamp(current))].groupby('issue').size()
    out=pd.concat([a.rename('previous'),b.rename('current')],axis=1).fillna(0).astype(int).reset_index()
    out['change']=out.current-out.previous
    out['change_pct']=out.change.div(out.previous.where(out.previous.gt(0)))*100
    out['review_flag']=(out.current.ge(min_count)&out.previous.ge(min_count)&out.change_pct.ge(threshold))
    out['baseline_status']=out.previous.map(lambda n:'No prior complaints' if n==0 else 'Observed baseline')
    return out.sort_values(['change','issue'],ascending=[False,True]).reset_index(drop=True)

def capacity_plan(queue,staff,hours,minutes,utilization):
    if queue<0 or staff<0 or hours<0 or minutes<=0 or not 0<utilization<=1:raise ValueError('Invalid capacity inputs')
    capacity=math.floor(staff*hours*60*utilization/minutes)
    return {'capacity':capacity,'reviewed':min(queue,capacity),'remaining':max(0,queue-capacity),'hours_required':queue*minutes/60,'staff_required':math.ceil(queue*minutes/(hours*60*utilization)) if hours>0 else None}

def review_queue(df,limit=100):
    return df.loc[df.timely.eq('No')].sort_values(['received','complaint_id'],ascending=[False,True]).head(limit)

def safe_csv(df):
    out=df.copy()
    for col in out.select_dtypes(include=['object','string']):
        out[col]=out[col].map(lambda x:"'"+x if isinstance(x,str) and x.lstrip().startswith(('=','+','-','@')) else x)
    return out.to_csv(index=False).encode('utf-8-sig')
