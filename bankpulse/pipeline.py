"""Offline build of validated CFPB facts and SQL analytics marts."""
from pathlib import Path
import hashlib,json
import duckdb
import pandas as pd
from .analytics import kpis,issue_changes

ROOT=Path(__file__).resolve().parents[1]
RENAME={'Complaint ID':'complaint_id','Date received':'received','Product':'product','Sub-product':'sub_product','Issue':'issue','Sub-issue':'sub_issue','Company':'company','State':'state','Submitted via':'channel','Date sent to company':'sent','Company response to consumer':'response','Timely response?':'timely'}

def prepare(raw,lock):
    assert not (set(RENAME)-set(raw)), 'Missing required source fields'
    df=raw.rename(columns=RENAME).replace('None','').copy()
    assert df.complaint_id.str.fullmatch(r'\d+').all(),'Invalid complaint identifier'
    assert not df.complaint_id.duplicated().any(),'Duplicate complaint identifiers'
    for col in ['received','sent']:df[col]=pd.to_datetime(df[col],utc=True,errors='raise').dt.tz_localize(None).dt.normalize()
    assert df.received.notna().all(),'Missing received date'
    assert df['product'].isin(lock['products']).all(),'Unexpected product'
    assert not df[['issue','company']].eq('').any().any(),'Missing required category'
    assert df.timely.isin(['Yes','No','']).all(),'Unknown timeliness encoding'
    excluded=int((~df.received.between(pd.Timestamp(lock['complete_start']),pd.Timestamp(lock['as_of']))).sum())
    df=df.loc[df.received.between(pd.Timestamp(lock['complete_start']),pd.Timestamp(lock['as_of']))].copy()
    for col in ['state','sub_product','sub_issue','response','channel','timely']:df[col]=df[col].replace('','Unknown')
    df['month']=df.received.dt.to_period('M').dt.to_timestamp()
    df['is_complete_month']=df.received.lt(pd.Timestamp(lock['complete_end_exclusive']))
    df['is_timely']=df.timely.eq('Yes').astype(int);df['is_known']=df.timely.isin(['Yes','No']).astype(int)
    df['is_not_timely']=df.timely.eq('No').astype(int)
    return df.sort_values(['received','complaint_id']).reset_index(drop=True),excluded

def main():
    lock=json.loads((ROOT/'data/source_lock.json').read_text());source=ROOT/'data/source/complaints.csv.gz'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==lock['snapshot_sha256'],'Source hash mismatch'
    raw=pd.read_csv(source,dtype=str,keep_default_na=False);assert len(raw)==lock['export_rows']
    df,excluded=prepare(raw,lock);out=ROOT/'data/processed';out.mkdir(exist_ok=True)
    df.to_parquet(out/'complaints.parquet',index=False)
    con=duckdb.connect(str(ROOT/'data/warehouse.duckdb'));con.register('source_frame',df)
    con.execute('CREATE OR REPLACE TABLE complaints AS SELECT * FROM source_frame')
    con.execute((ROOT/'sql/marts.sql').read_text())
    for name in ['monthly_product','issue_monthly','company_summary']:
        table=con.table(name).df();table.to_parquet(out/f'{name}.parquet',index=False);table.to_csv(out/f'{name}.csv',index=False)
    full=df.loc[df.is_complete_month];months=pd.date_range(lock['complete_start'],pd.Timestamp(lock['complete_end_exclusive'])-pd.Timedelta(days=1),freq='MS')
    assert len(months)==24
    assert full.month.nunique()==24,'Incomplete source month coverage'
    monthly=con.table('monthly_product').df()
    assert int(monthly.complaints.sum())==len(full),'SQL total does not reconcile'
    assert int(monthly.timely_yes.sum())==int(full.is_timely.sum())
    sample=full.sort_values(['received','complaint_id'],ascending=[False,True]).head(500).copy()
    sample.to_csv(out/'excel_sample.csv',index=False)
    delta=issue_changes(full,months[-2],months[-1]);delta.to_csv(out/'latest_issue_changes.csv',index=False)
    summary={'source_export_rows':len(raw),'retained_rows':len(df),'boundary_exclusions':excluded,'complete':kpis(full),'partial':kpis(df.loc[~df.is_complete_month]),'monthly_rows':len(monthly),'complete_months':24,'missing_state':int(df.state.eq('Unknown').sum()),'sent_before_received':int(df.sent.lt(df.received).sum()),'source_hash_verified':True,'unique_identifiers':True,'sql_reconciled':True,'latest_complete_month':str(months[-1].date()),'previous_complete_month':str(months[-2].date()),'latest_month_count':int(full.month.eq(months[-1]).sum()),'previous_month_count':int(full.month.eq(months[-2]).sum()),'flagged_issues':int(delta.review_flag.sum()),'products':full.groupby('product').size().to_dict(),'companies':int(full.company.nunique())}
    (ROOT/'reports/quality.json').write_text(json.dumps(summary,indent=2)+'\n')
    payload={'lock':lock,'summary':summary,'monthly':json.loads(monthly.to_json(orient='records',date_format='iso')),'sample':json.loads(sample.to_json(orient='records',date_format='iso')),'issues':json.loads(delta.to_json(orient='records'))}
    (ROOT/'excel/inputs.json').write_text(json.dumps(payload,indent=2)+'\n')
    con.close();print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
