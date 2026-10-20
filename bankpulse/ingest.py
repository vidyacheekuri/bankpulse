"""Fetch a complete scoped CFPB CSV export and retain only analytical fields."""
from pathlib import Path
import argparse, gzip, hashlib, io, json, time
from datetime import datetime, timezone
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT=Path(__file__).resolve().parents[1]
API='https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/'
PRODUCTS=['Credit card','Checking or savings account']
KEEP=['Complaint ID','Date received','Product','Sub-product','Issue','Sub-issue','Company','State','Submitted via','Date sent to company','Company response to consumer','Timely response?']

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--as-of',default=datetime.now(timezone.utc).date().isoformat());args=parser.parse_args()
    asof=pd.Timestamp(args.as_of);end=asof.replace(day=1);start=end-pd.DateOffset(months=24)
    session=requests.Session();session.mount('https://',HTTPAdapter(max_retries=Retry(total=5,backoff_factor=15,status_forcelist=[429,500,502,503,504],respect_retry_after_header=True)))
    frames=[];partitions=[];raw=ROOT/'data/raw';raw.mkdir(exist_ok=True)
    for month in pd.date_range(start,end,freq='MS'):
        upper=min(month+pd.offsets.MonthEnd(0),asof)
        params=[('date_received_min',str(month.date())),('date_received_max',str(upper.date())),('no_aggs','true')]+[('product',p) for p in PRODUCTS]
        path=raw/f'{month:%Y-%m}.csv';meta_path=raw/f'{month:%Y-%m}.json'
        if path.exists() and meta_path.exists():
            part=json.loads(meta_path.read_text())
        else:
            response=session.get(API,params=params+[('size',1)],timeout=120);response.raise_for_status()
            expected=response.json()['hits']['total'];assert expected['relation']=='eq',expected
            time.sleep(3)
            result=session.get(API,params=params+[('format','csv')],timeout=(30,300));result.raise_for_status()
            path.write_bytes(result.content)
            part={'month':f'{month:%Y-%m}','min':str(month.date()),'max':str(upper.date()),'url':result.url,'api_count':expected['value'],'sha256':hashlib.sha256(result.content).hexdigest()}
            meta_path.write_text(json.dumps(part,indent=2))
            time.sleep(7)
        frame=pd.read_csv(path,dtype=str,keep_default_na=False)
        assert len(frame)==part['api_count'],f'{month}: export count mismatch'
        assert hashlib.sha256(path.read_bytes()).hexdigest()==part['sha256']
        dates=pd.to_datetime(frame['Date received'],utc=True).dt.tz_localize(None).dt.normalize()
        assert dates.between(month,upper).all(),'Unexpected export date boundary'
        frames.append(frame);partitions.append(part)
        print(f'{month:%Y-%m}: {len(frame):,} records verified',flush=True)
    df=pd.concat(frames,ignore_index=True)
    assert not df['Complaint ID'].duplicated().any(),'Overlapping export partitions'
    absent=set(KEEP)-set(df.columns);assert not absent,absent
    # Exclude narratives, ZIP codes, tags and consent fields from the distributed case study.
    selected=df[KEEP].sort_values('Complaint ID',key=lambda x:x.astype('int64'))
    buf=io.BytesIO()
    with gzip.GzipFile(fileobj=buf,mode='wb',mtime=0) as z:z.write(selected.to_csv(index=False).encode())
    source=ROOT/'data/source/complaints.csv.gz';source.write_bytes(buf.getvalue())
    lock={'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'as_of':args.as_of,'complete_start':str(start.date()),'complete_end_exclusive':str(end.date()),'products':PRODUCTS,'partitions':partitions,'api_reported_count':sum(p['api_count'] for p in partitions),'export_rows':len(df),'snapshot_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'retained_fields':KEEP,'discarded_fields':[c for c in df if c not in KEEP],'source':'https://www.consumerfinance.gov/data-research/consumer-complaints/','date_policy':'Date received, UTC calendar date; exported date bounds verified inclusive by partition. Complete-month analysis uses a half-open window. Recent months may backfill.'}
    (ROOT/'data/source_lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    print(json.dumps({k:lock[k] for k in ['export_rows','complete_start','complete_end_exclusive','snapshot_sha256']}),flush=True)

if __name__=='__main__':main()
