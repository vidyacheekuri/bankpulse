import pandas as pd
import pytest
from bankpulse.analytics import filter_records,kpis,monthly,issue_changes,capacity_plan,review_queue,safe_csv

@pytest.fixture
def facts():
    return pd.DataFrame({'complaint_id':['01','02','03','04'],'received':pd.to_datetime(['2026-01-01','2026-01-31','2026-03-01','2026-03-31']),'month':pd.to_datetime(['2026-01-01','2026-01-01','2026-03-01','2026-03-01']),'product':['Credit card']*4,'company':['A','A','B','B'],'state':['NY','Unknown','CA','CA'],'timely':['Yes','No','Unknown','Yes'],'is_timely':[1,0,0,1],'is_known':[1,1,0,1],'issue':['Fees','Fees','Fraud','Fraud']})

def test_rate_excludes_unknown(facts):
    assert kpis(facts)=={'complaints':4,'timely_yes':2,'timely_no':1,'known':3,'unknown':1,'timely_rate':2/3}
def test_empty_rate_is_unavailable(facts):assert kpis(facts.iloc[:0])['timely_rate'] is None
def test_all_unknown_rate_is_unavailable(facts):assert kpis(facts.loc[facts.timely.eq('Unknown')])['timely_rate'] is None
def test_inclusive_dates(facts):assert len(filter_records(facts,'2026-01-01','2026-01-31'))==2
def test_empty_product_selection(facts):assert filter_records(facts,'2026-01-01','2026-03-31',products=[]).empty
def test_intersecting_filters(facts):assert filter_records(facts,'2026-01-01','2026-03-31',companies=['A'],states=['NY']).complaint_id.tolist()==['01']
def test_unknown_state_filter(facts):assert filter_records(facts,'2026-01-01','2026-03-31',states=['Unknown']).complaint_id.tolist()==['02']
def test_reversed_dates(facts):
    with pytest.raises(ValueError):filter_records(facts,'2026-03-01','2026-01-01')
def test_missing_month_and_zero_baseline(facts):
    trend=monthly(facts,'2026-01-01','2026-03-31')
    assert trend.complaints.tolist()==[2,0,2]
    assert pd.isna(trend.iloc[2].mom_pct)
    assert trend.iloc[2].rolling_3m==pytest.approx(4/3)
def test_new_and_disappearing_issues(facts):
    changes=issue_changes(facts,'2026-01-01','2026-03-01',1,10).set_index('issue')
    assert changes.loc['Fees','change']==-2 and changes.loc['Fraud','change']==2
    assert pd.isna(changes.loc['Fraud','change_pct']) and changes.change.sum()==0
    assert not changes.review_flag.any()
def test_flag_threshold_inclusive(facts):
    frame=pd.DataFrame({'month':pd.to_datetime(['2026-01-01']*4+['2026-02-01']*5),'issue':['Fees']*9})
    assert issue_changes(frame,'2026-01-01','2026-02-01',4,25).review_flag.iloc[0]
    assert not issue_changes(frame,'2026-01-01','2026-02-01',5,25).review_flag.iloc[0]
@pytest.mark.parametrize('queue,staff,hours,minutes,util,capacity,remaining',[(100,2,20,30,.75,60,40),(20,2,20,30,.75,60,0),(20,0,20,30,.75,0,20),(20,2,0,30,.75,0,20),(0,1,1,20,.5,1,0),(10,1,1,40,1,1,9)])
def test_capacity_boundaries(queue,staff,hours,minutes,util,capacity,remaining):
    result=capacity_plan(queue,staff,hours,minutes,util)
    assert result['capacity']==capacity and result['remaining']==remaining
@pytest.mark.parametrize('args',[(-1,1,1,1,1),(1,-1,1,1,1),(1,1,-1,1,1),(1,1,1,0,1),(1,1,1,1,0),(1,1,1,1,1.1)])
def test_invalid_capacity(args):
    with pytest.raises(ValueError):capacity_plan(*args)
def test_queue_explicit_no_only(facts):assert review_queue(facts).complaint_id.tolist()==['02']
def test_csv_formula_injection():
    result=safe_csv(pd.DataFrame({'text':['=1+1',' +cmd','@SUM(1)','normal']})).decode('utf-8-sig')
    assert "'=1+1" in result and "' +cmd" in result and "'@SUM(1)" in result
