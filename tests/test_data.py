from pathlib import Path
import hashlib,json
import duckdb
import pandas as pd
import pytest
from bankpulse.pipeline import prepare
ROOT=Path(__file__).resolve().parents[1]

def test_frozen_source_and_partition_counts():
    lock=json.loads((ROOT/'data/source_lock.json').read_text())
    assert hashlib.sha256((ROOT/'data/source/complaints.csv.gz').read_bytes()).hexdigest()==lock['snapshot_sha256']
    assert sum(p['api_count'] for p in lock['partitions'])==lock['export_rows']
def test_source_to_marts_reconciliation():
    lock=json.loads((ROOT/'data/source_lock.json').read_text());raw=pd.read_csv(ROOT/'data/source/complaints.csv.gz',dtype=str,keep_default_na=False)
    frame,_=prepare(raw,lock);complete=frame.loc[frame.is_complete_month]
    assert len(frame)==len(raw)
    monthly=pd.read_parquet(ROOT/'data/processed/monthly_product.parquet')
    assert len(monthly)==48 and monthly.complaints.sum()==len(complete)
    assert monthly.timely_yes.sum()==complete.is_timely.sum()
    assert monthly.known.sum()==complete.is_known.sum()
    assert monthly.unknown.sum()==len(complete)-complete.is_known.sum()
    con=duckdb.connect();con.register('complaints',frame);con.execute((ROOT/'sql/marts.sql').read_text())
    pd.testing.assert_frame_equal(con.table('monthly_product').df(),monthly)
    change=pd.read_csv(ROOT/'data/processed/latest_issue_changes.csv')
    assert change.change.sum()==monthly.loc[monthly.month.eq(monthly.month.max()),'complaints'].sum()-monthly.loc[monthly.month.eq(monthly.month.max()-pd.DateOffset(months=1)),'complaints'].sum()
@pytest.mark.parametrize('field,value,error',[('Complaint ID','bad','identifier'),('Product','Mortgage','product'),('Timely response?','Maybe','timeliness')])
def test_contract_rejections(field,value,error):
    lock=json.loads((ROOT/'data/source_lock.json').read_text());raw=pd.read_csv(ROOT/'data/source/complaints.csv.gz',dtype=str,keep_default_na=False,nrows=2)
    raw.loc[0,field]=value
    with pytest.raises(AssertionError,match=error):prepare(raw,lock)
def test_duplicate_id_rejected():
    lock=json.loads((ROOT/'data/source_lock.json').read_text());raw=pd.read_csv(ROOT/'data/source/complaints.csv.gz',dtype=str,keep_default_na=False,nrows=1)
    with pytest.raises(AssertionError,match='Duplicate'):prepare(pd.concat([raw,raw]),lock)
