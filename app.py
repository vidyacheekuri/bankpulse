"""BankPulse — a banking operations research and acceptance workbench."""
from pathlib import Path
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from bankpulse.analytics import filter_records,kpis,monthly,issue_changes,capacity_plan,review_queue,safe_csv

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='BankPulse · Banking operations',page_icon='◒',layout='wide')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Libre+Baskerville:wght@400;700&display=swap');
html,body,.stApp{font-family:'DM Sans',sans-serif;}
.block-container{padding-top:1.7rem;max-width:1480px;}
h1{font-family:'Libre Baskerville',serif!important;font-weight:400!important;letter-spacing:-.04em;}
h2,h3{letter-spacing:-.025em;color:#293b52;}
[data-testid="stSidebar"]{background:#e8edf2;border-right:1px solid #d1dae2;}
[data-testid="stMetric"]{background:#fffefb;border-top:3px solid #647f9e;border-bottom:1px solid #deddd7;padding:16px 12px;}
[data-testid="stMetricValue"]{font-size:1.8rem;color:#304b67;font-weight:500;}
.masthead{display:flex;justify-content:space-between;border-bottom:1px solid #b6c2ce;padding-bottom:13px;margin-bottom:22px;font-size:.75rem;letter-spacing:.16em;color:#64758a;}
.intro{border-left:4px solid #b37d5a;padding-left:24px;margin:25px 0;}
.intro h1{font-size:2.65rem;color:#2d4259;margin:0 0 14px;}
.intro p{color:#65717d;max-width:790px;line-height:1.7;}
.note{padding:15px 20px;background:#ede9df;border-radius:6px;color:#59616a;margin:16px 0;font-size:.9rem;}
.foot{border-top:1px solid #d6d8d8;margin-top:35px;padding-top:16px;color:#74808a;font-size:.75rem;}
@media(max-width:1100px){.block-container{padding-left:2rem;padding-right:2rem;}.intro h1{font-size:2rem;}[data-testid="stMetricValue"]{font-size:1.4rem;}}
</style>''',unsafe_allow_html=True)
COLORS=['#607f9f','#bb8966','#9eabb6','#c8bba8']

@st.cache_data
def load():
    return pd.read_parquet(ROOT/'data/processed/complaints.parquet'),json.loads((ROOT/'data/source_lock.json').read_text()),json.loads((ROOT/'reports/quality.json').read_text())
df,lock,quality=load();complete=df.loc[df.is_complete_month]
months=sorted(complete.month.unique());start=pd.Timestamp(lock['complete_start']);end=pd.Timestamp(lock['complete_end_exclusive'])-pd.Timedelta(days=1)
with st.sidebar:
    st.markdown('## ◒ BankPulse')
    st.caption('BANKING OPERATIONS RESEARCH')
    page=st.radio('Workspace',['Executive overview','Issue explorer','Response quality','Review planning','Project evidence'],label_visibility='collapsed')
    st.divider()
    st.caption(f"SOURCE SNAPSHOT\n\n{lock['as_of']}\n\nComplete months: {start:%b %Y} – {end:%b %Y}")
    st.link_button('GitHub project','https://github.com/vidyacheekuri/bankpulse')
    st.caption('CFPB public complaints. Counts are not customer complaint rates.')

st.markdown('<div class="masthead"><span>BANKPULSE / SERVICE QUALITY</span><span>RESEARCH EDITION 01</span></div>',unsafe_allow_html=True)
def intro(title,description):st.markdown(f'<div class="intro"><h1>{title}</h1><p>{description}</p></div>',unsafe_allow_html=True)
def plot(fig,height=340):
    fig.update_layout(height=height,margin=dict(l=12,r=12,t=28,b=20),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(family='DM Sans',color='#40556a'),colorway=COLORS,legend=dict(orientation='h',y=1.13),legend_title_text='')
    fig.update_xaxes(gridcolor='#e3e3de');fig.update_yaxes(gridcolor='#e3e3de')
    st.plotly_chart(fig,width='stretch',config={'displaylogo':False})
def cards(items):
    for col,(title,value,helptext) in zip(st.columns(len(items)),items):col.metric(title,value,help=helptext)
def table(data):st.dataframe(data,hide_index=True,width='stretch')
def export(data,name):st.download_button('Download matching records',safe_csv(data),name,'text/csv')
def controls():
    with st.expander('Filter the analysis',expanded=False):
        a,b,c=st.columns(3)
        products=a.multiselect('Products',lock['products'],default=lock['products'])
        companies=b.multiselect('Companies (empty = all)',sorted(complete.company.unique()))
        states=c.multiselect('States (empty = all)',sorted(complete.state.unique()))
        dates=st.date_input('Received date range',(start.date(),end.date()),min_value=start.date(),max_value=end.date())
    if len(dates)!=2:st.info('Select both a start and end date.');st.stop()
    filtered=filter_records(complete,dates[0],dates[1],products,companies or None,states or None)
    st.caption(f'{len(filtered):,} published complaints · {dates[0]} through {dates[1]} · dates inclusive')
    return filtered,dates

if page=='Executive overview':
    intro('Listen to the pattern.','Follow published banking complaints, understand changes in issue mix, and inspect reported response timeliness before choosing what to investigate.')
    data,dates=controls();k=kpis(data)
    cards([('PUBLISHED COMPLAINTS',f'{k["complaints"]:,}','Count in the selected source snapshot.'),('TIMELY RESPONSE',f'{k["timely_rate"]:.1%}' if k['timely_rate'] is not None else 'n.a.','Yes / (Yes + No). Unknown statuses excluded.'),('NOT TIMELY',f'{k["timely_no"]:,}','Source explicitly reports No.'),('UNKNOWN STATUS',f'{k["unknown"]:,}','Retained and excluded from the rate denominator.')])
    trend=monthly(data,dates[0],dates[1]);a,b=st.columns([1.5,1])
    with a:
        st.markdown('### Complaints over time')
        fig=go.Figure();fig.add_trace(go.Scatter(x=trend.month,y=trend.complaints,name='Published complaints',mode='lines+markers',line=dict(color=COLORS[0],width=3)))
        fig.add_trace(go.Scatter(x=trend.month,y=trend.rolling_3m,name='3-month average',line=dict(color=COLORS[1],dash='dot')));plot(fig)
    with b:
        st.markdown('### Product mix')
        mix=data.groupby('product').size().reset_index(name='Complaints');plot(px.bar(mix,x='Complaints',y='product',orientation='h',color_discrete_sequence=COLORS,labels={'product':''}))
    shown=trend.copy();shown['timely_rate']=shown.timely_rate*100
    shown[shown.select_dtypes('number').columns]=shown.select_dtypes('number').round(3)
    table(shown.rename(columns={'month':'Month','complaints':'Complaints','timely_rate':'Timely response %','mom_pct':'Month-over-month %'}))
    st.caption('Boundary months reflect the selected days. Rolling averages use the displayed monthly counts; choose full months for like-for-like comparisons. Zero-count months remain visible.')
    st.markdown(f'<div class="note">The partial current month contains {quality["partial"]["complaints"]:,} published records in this snapshot and is excluded above. Recent complete months may still backfill as complaints become eligible for publication.</div>',unsafe_allow_html=True)
    export(data,'bankpulse-filtered-complaints.csv')

elif page=='Issue explorer':
    intro('Find what changed.','Compare two complete calendar months. Separate the issues contributing to the change from percentage spikes caused by small baselines.')
    a,b,c=st.columns(3)
    previous=a.selectbox('Baseline month',months[:-1],index=len(months)-2,format_func=lambda d:pd.Timestamp(d).strftime('%b %Y'))
    later=[m for m in months if m>previous];current=b.selectbox('Comparison month',later,index=len(later)-1,format_func=lambda d:pd.Timestamp(d).strftime('%b %Y'))
    product=c.selectbox('Product',['All products']+lock['products'])
    data=complete if product=='All products' else complete.loc[complete.product.eq(product)]
    a,b=st.columns(2);minimum=a.number_input('Minimum complaints in each month',min_value=1,value=30,step=10);threshold=b.slider('Growth threshold (%)',5,200,25,5)
    changes=issue_changes(data,previous,current,minimum,threshold)
    cards([('BASELINE',f'{changes.previous.sum():,}','Complaints in the earlier month.'),('COMPARISON',f'{changes.current.sum():,}','Complaints in the later month.'),('NET CHANGE',f'{changes.change.sum():+,}','Sum of issue contributions.'),('REVIEW FLAGS',str(changes.review_flag.sum()),'Both counts meet the minimum and percentage growth meets the threshold.')])
    st.markdown('### Contributions to the change')
    top=changes.reindex(changes.change.abs().sort_values(ascending=False).index).head(8)
    labels=top.issue.str.slice(0,38).tolist()+['Other issues','Net change'];values=top.change.tolist()+[int(changes.change.sum()-top.change.sum()),int(changes.change.sum())]
    fig=go.Figure(go.Waterfall(x=labels,y=values,measure=['relative']*(len(labels)-1)+['total'],increasing={'marker':{'color':COLORS[1]}},decreasing={'marker':{'color':COLORS[0]}},totals={'marker':{'color':'#304b67'}}));plot(fig,420)
    st.caption('All issues reconcile to net change, including declines and issues with zero complaints at either endpoint.')
    table(changes.round(2));st.download_button('Download issue comparison',safe_csv(changes),'bankpulse-issue-comparison.csv','text/csv')
    st.info('Review flags use an explicit rule, not a forecast or statistical significance test. New issues without a baseline have no percentage change.')

elif page=='Response quality':
    intro('Keep the denominator visible.','Explore company response categories and the published timeliness indicator. Volume gives context; it does not measure customer-level risk.')
    data,dates=controls();k=kpis(data)
    cards([('TIMELY YES',f'{k["timely_yes"]:,}','Published Yes status.'),('KNOWN STATUS',f'{k["known"]:,}','Yes plus No.'),('TIMELY RESPONSE',f'{k["timely_rate"]:.2%}' if k['timely_rate'] is not None else 'n.a.','Weighted by records, not an average of company percentages.')])
    a,b=st.columns(2)
    with a:
        st.markdown('### Company response categories');responses=data.groupby('response').size().reset_index(name='Complaints').sort_values('Complaints')
        plot(px.bar(responses,x='Complaints',y='response',orientation='h',labels={'response':''},color_discrete_sequence=[COLORS[0]]))
    with b:
        st.markdown('### Reported timeliness');status=data.groupby('timely').size().reset_index(name='Complaints')
        plot(px.bar(status,x='timely',y='Complaints',color='timely',color_discrete_map={'Yes':COLORS[0],'No':COLORS[1],'Unknown':COLORS[2]},labels={'timely':'Source status'}))
    minimum=st.number_input('Minimum known-status records per company',min_value=1,value=100,step=25)
    company=data.groupby('company').agg(complaints=('complaint_id','size'),known=('is_known','sum'),timely_yes=('is_timely','sum'),not_timely=('is_not_timely','sum')).reset_index()
    company['timely_rate']=company.timely_yes.div(company.known.where(company.known.gt(0)));company=company.loc[company.known.ge(minimum)].sort_values(['not_timely','company'],ascending=[False,True])
    table(company);st.caption('Companies have different sizes and product mixes. This table is an investigation aid, not a ranking of bank quality. Dates sent to companies are not resolution dates.')
    status_choice=st.selectbox('Record-level response status',['All','Yes','No','Unknown'])
    selected=data if status_choice=='All' else data.loc[data.timely.eq(status_choice)]
    st.caption(f'{len(selected):,} records match the status filter. Preview shows the first 100.')
    table(selected.head(100)[['complaint_id','received','product','issue','company','timely','response']]);export(selected,'bankpulse-response-records.csv')

elif page=='Review planning':
    intro('Turn an observation into a review plan.','Build an investigation queue from complaints explicitly marked not timely. Test review capacity with editable assumptions, separate from the public source data.')
    product=st.selectbox('Product',['All products']+lock['products']);month=st.selectbox('Review month',months,index=len(months)-1,format_func=lambda d:pd.Timestamp(d).strftime('%b %Y'))
    data=complete.loc[complete.month.eq(month)];data=data if product=='All products' else data.loc[data.product.eq(product)]
    queue=review_queue(data,limit=len(data));a,b,c,d=st.columns(4)
    staff=a.number_input('Reviewers',min_value=0,value=2,step=1);hours=b.number_input('Hours per reviewer / week',min_value=0.,value=20.,step=1.)
    minutes=c.number_input('Minutes per review',min_value=1.,value=30.,step=5.);util=d.slider('Productive time (%)',10,100,75,5)
    plan=capacity_plan(len(queue),staff,hours,minutes,util/100)
    cards([('SELECTED RECORDS',f'{len(queue):,}','Historical records flagged No, not a live unresolved backlog.'),('WEEKLY CAPACITY',f'{plan["capacity"]:,}','Floor(reviewers × hours × 60 × productive fraction / minutes).'),('REMAINING AFTER WEEK',f'{plan["remaining"]:,}','Maximum of zero and selected records minus simulated capacity.')])
    chart=pd.DataFrame({'Outcome':['Reviewable within capacity','Remaining'],'Records':[plan['reviewed'],plan['remaining']]});plot(px.bar(chart,x='Records',y='Outcome',orientation='h',color='Outcome',color_discrete_sequence=COLORS),240)
    st.caption(f'Simulation only. Assumed total review effort: {plan["hours_required"]:,.1f} hours. Queue order: newest received date, then complaint ID. No severity or unresolved status is inferred.')
    table(queue.head(100)[['complaint_id','received','product','issue','company','timely']]);export(queue,'bankpulse-review-queue.csv')

else:
    intro('From user need to tested result.','Inspect the requirements, workbook, acceptance scenarios, and source controls behind BankPulse.')
    cards([('SOURCE RECORDS',f'{quality["source_export_rows"]:,}','Complete scoped export.'),('COMPLETE MONTHS','24','24 full calendar months, with publication lag caveats.'),('HUMAN UAT','Not run','Acceptance scripts are ready for a human reviewer; developer tests are separate.')])
    for label,file,mime in [('Download Excel workbook','excel/BankPulse.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),('Download UAT scenarios','docs/uat_cases.csv','text/csv'),('Download business requirements','docs/requirements.md','text/markdown')]:
        path=ROOT/file
        if path.exists():st.download_button(label,path.read_bytes(),path.name,mime)
    st.markdown('### Source controls');table(pd.DataFrame({'Control':['Snapshot fingerprint','Unique complaint IDs','SQL totals reconciled','Unknown states retained'],'Result':[str(quality['source_hash_verified']),str(quality['unique_identifiers']),str(quality['sql_reconciled']),f'{quality["missing_state"]:,}']}))
    st.caption('The Excel detail sheet is a 500-record demonstration extract. Its monthly analysis uses the complete population, with separate reconciliation controls.')
    with st.expander('Provenance and exclusions'):st.json(lock)
    st.markdown('[CFPB dataset](https://www.consumerfinance.gov/data-research/consumer-complaints/) · [Field definitions](https://cfpb.github.io/api/ccdb/fields.html)')

st.markdown('<div class="foot">BANKPULSE · PUBLIC COMPLAINT DATA · SOURCE-DATED ANALYSIS · PORTFOLIO CASE STUDY</div>',unsafe_allow_html=True)
