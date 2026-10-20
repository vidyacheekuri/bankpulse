import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const root=new URL('..',import.meta.url).pathname;
const previewDir=process.env.BANKPULSE_PREVIEW_DIR || `${root}/excel/previews`;
await fs.mkdir(previewDir,{recursive:true});
const payload=JSON.parse(await fs.readFile(`${root}/excel/inputs.json`,'utf8'));
const uat=JSON.parse(await fs.readFile(`${root}/excel/uat.json`,'utf8'));
const {monthly,sample,summary,lock}=payload;
const wb=Workbook.create();
const names=['Overview','Analysis','Capacity','Pivot Analysis','Detail','Monthly Source','Lookups','UAT','Read Me'];
const sheets=Object.fromEntries(names.map(n=>[n,wb.worksheets.add(n)]));
const ink='#293b52',blue='#607f9f',copper='#bb8966',ivory='#f7f5ef',pale='#e8edf2',input='#fff0cb';
function setup(name,end='L45'){
 const s=sheets[name];s.showGridLines=false;s.getRange(`A1:${end}`).format.font={name:'Arial',size:11,color:ink};
 s.getRange(`A1:${end}`).format.rowHeight=23;s.getRange(`A1:${end}`).format.verticalAlignment='center';
 s.getRange(`A1:${end}`).format.columnWidth=16;return s;
}
function title(s,text){s.getRange('A2').values=[[text]];s.getRange('A2').format.font={name:'Arial',size:17,bold:true,color:ink};s.getRange('A2:L2').format.rowHeight=30;s.getRange('A3:L3').format.borders={bottom:{style:'thin',color:'#b6c2ce'}};}
function header(s,range){s.getRange(range).format={fill:blue,font:{name:'Arial',size:11,bold:true,color:'#ffffff'},rowHeight:34,wrapText:true,horizontalAlignment:'center',verticalAlignment:'center'};}
function table(s,range,name){const t=s.tables.add(range,true,name);t.style='TableStyleLight1';return t;}
function chart(s,type,ranges,titleText,a,b){const c=s.charts.add(type,ranges);c.title=titleText;c.titleTextStyle.fontSize=14;c.titleTextStyle.typeface='Arial';c.setPosition(a,b);c.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:10}};c.yAxis={numberFormatCode:'#,##0',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:10}};c.hasLegend=false;for(const [i,series] of c.series.items.entries()){series.fill=[blue,copper][i%2];if(type==='line')series.line={fill:[blue,copper][i%2],style:'solid',width:2};}return c;}

// Complete-population source; no formulas or summaries flow back into this table.
const ms=setup('Monthly Source','H55');title(ms,'Monthly source · complete population');
ms.getRange('A4').values=[['Source: CFPB Consumer Complaint Database; retrieved '+lock.as_of]];
ms.getRange('A5').values=[['https://www.consumerfinance.gov/data-research/consumer-complaints/']];
ms.getRange('A7:H7').values=[['Month','Product','Complaints','Timely Yes','Known status','Not timely','Unknown','Month label']];
ms.getRange('A8:H55').values=monthly.map(r=>[new Date(r.month),r.product,r.complaints,r.timely_yes,r.known,r.timely_no,r.unknown,new Date(r.month).toLocaleDateString('en-US',{month:'short',year:'numeric',timeZone:'UTC'})]);
ms.getRange('A8:A55').setNumberFormat('mmm yyyy');ms.getRange('C8:G55').setNumberFormat('#,##0');ms.getRange('B7:B55').format.columnWidth=35;
table(ms,'A7:H55','MonthlySource');header(ms,'A7:H7');ms.freezePanes.freezeRows(7);

const look=setup('Lookups','D12');title(look,'Product mapping');
look.getRange('A4').values=[['Review-team mapping is a fictional portfolio workflow assumption.']];
look.getRange('A6:B8').values=[['Product','Review team'],['Credit card','Card operations'],['Checking or savings account','Deposit operations']];
look.getRange('A6:B8').format.columnWidth=37;look.getRange('B7:B8').format.fill=input;table(look,'A6:B8','ProductMapping');header(look,'A6:B6');

const det=setup('Detail','N507');title(det,'Detail · 500-record demonstration extract');
det.getRange('A4').values=[['Newest complete-month records; not a representative sample. Full-population analysis uses Monthly Source.']];
det.getRange('A5').values=[['Source: CFPB Consumer Complaint Database, '+lock.as_of+'; original IDs preserved as text.']];
det.getRange('A7:N7').values=[['Complaint ID','Received','Product','Issue','Company','State','Timely','Response','Channel','Sent','Sub-product','Sub-issue','Review team (simulated)','Received month']];
det.getRange('A8:L507').values=sample.map(r=>[r.complaint_id,new Date(r.received),r.product,r.issue,r.company,r.state,r.timely,r.response,r.channel,r.sent?new Date(r.sent):null,r.sub_product,r.sub_issue]);
det.getRange('A8:A507').setNumberFormat('@');for(const col of ['B','J','N'])det.getRange(`${col}8:${col}507`).setNumberFormat('mm/dd/yy');
det.getRange('M8:M507').formulas=sample.map((_,i)=>[`=_xlfn.XLOOKUP(C${i+8},'Lookups'!$A$7:$A$8,'Lookups'!$B$7:$B$8,"Unmapped",0)`]);
det.getRange('N8:N507').formulas=sample.map((_,i)=>[`=DATE(YEAR(B${i+8}),MONTH(B${i+8}),1)`]);
for(const col of ['C','D','E','H','K','L','M'])det.getRange(`${col}7:${col}507`).format.columnWidth=35;
table(det,'A7:N507','ComplaintDetail');header(det,'A7:N7');det.freezePanes.freezeRows(7);
det.getRange('C8:M507').format.wrapText=true;det.getRange('A8:N507').format.rowHeight=55;
det.getRange('G8:G507').conditionalFormats.add('containsText',{text:'No',format:{fill:'#f4ddd0',font:{color:'#8e412b'}}});

const a=setup('Analysis','L43');title(a,'Monthly analysis');a.getRange('A4').values=[['Product']];a.getRange('B4').values=[['All products']];a.getRange('B4').format.fill=input;a.getRange('B4').format.columnWidth=22;
a.getRange('B4').dataValidation={rule:{type:'list',values:['All products',...lock.products]}};
a.getRange('A6').values=[['Product selection controls full-population totals; rates exclude unknown statuses.']];
a.getRange('A8:G8').values=[['Month','Complaints','Timely Yes','Known status','Timely rate','Monthly change %','Chart month']];
const dates=[...new Set(monthly.map(r=>r.month))];
a.getRange('A9:A32').values=dates.map(d=>[new Date(d)]);a.getRange('A9:A32').setNumberFormat('mmm yyyy');
for(let i=9;i<=32;i++){
 for(const [out,src] of [['B','C'],['C','D'],['D','E']])a.getRange(`${out}${i}`).formulas=[[`=IF($B$4="All products",SUMIFS('Monthly Source'!$${src}$8:$${src}$55,'Monthly Source'!$A$8:$A$55,$A${i}),SUMIFS('Monthly Source'!$${src}$8:$${src}$55,'Monthly Source'!$A$8:$A$55,$A${i},'Monthly Source'!$B$8:$B$55,$B$4))`]];
 a.getRange(`E${i}`).formulas=[[`=IF(D${i}=0,"n.a.",C${i}/D${i})`]];
 if(i>9)a.getRange(`F${i}`).formulas=[[`=IF(B${i-1}=0,"n.a.",B${i}/B${i-1}-1)`]];
 a.getRange(`G${i}`).formulas=[[`=TEXT(A${i},"mmm yyyy")`]];
}
a.getRange('F9').values=[['n.a.']];header(a,'A8:G8');a.getRange('B9:D35').setNumberFormat('#,##0');a.getRange('E9:F35').setNumberFormat('0.0%');
a.getRange('A35').values=[['Total / weighted rate']];a.getRange('A35').format.columnWidth=24;
a.getRange('B35:E35').formulas=[['=SUM(B9:B32)','=SUM(C9:C32)','=SUM(D9:D32)','=IF(D35=0,"n.a.",C35/D35)']];a.getRange('A35:E35').format.font.bold=true;
a.getRange('I8:J8').values=[['Detail checks','500-record extract']];header(a,'I8:J8');a.getRange('I9:J11').values=[['Record count',null],['Timely Yes',null],['Not timely',null]];
a.getRange('J9:J11').formulas=[['=COUNTA(Detail!A8:A507)'],['=COUNTIFS(Detail!G8:G507,"Yes")'],['=COUNTIFS(Detail!G8:G507,"No")']];a.getRange('I13').values=[['Independent full-population controls']];
a.getRange('I14:J16').values=[['Expected count',summary.complete.complaints],['Expected Yes',summary.complete.timely_yes],['Expected known',summary.complete.known]];
a.getRange('I18:J20').values=[['Count difference',null],['Yes difference',null],['Known difference',null]];
a.getRange('J18:J20').formulas=[["=SUM('Monthly Source'!C8:C55)-J14"],["=SUM('Monthly Source'!D8:D55)-J15"],["=SUM('Monthly Source'!E8:E55)-J16"]];
a.getRange('I8:J20').format.columnWidth=25;a.getRange('J18:J20').conditionalFormats.add('cellIs',{operator:'notEqual',formula:0,format:{fill:'#f4ddd0',font:{color:'#8e412b'}}});
a.getRange('F10:F32').conditionalFormats.add('colorScale',{colors:['#dbe6ef','#fffefb','#e6c3a8']});a.freezePanes.freezeRows(8);

const o=setup('Overview','L34');title(o,'BankPulse · Banking complaints');o.tabColor=ink;
o.getRange('A4').values=[[`${dates[0].slice(0,7)} through ${dates.at(-1).slice(0,7)} · snapshot ${lock.as_of}`]];
o.getRange('A6').values=[['Selected product']];o.getRange('C6').formulas=[["='Analysis'!B4"]];
o.getRange('A8').values=[['Complaints']];o.getRange('D8').values=[['Timely response']];o.getRange('G8').values=[['Known status']];o.getRange('J8').values=[['Unknown status']];
o.getRange('A9').formulas=[["='Analysis'!B35"]];o.getRange('D9').formulas=[["='Analysis'!E35"]];o.getRange('G9').formulas=[["='Analysis'!D35"]];o.getRange('J9').formulas=[["='Analysis'!B35-'Analysis'!D35"]];
for(const col of ['A','D','G','J']){o.getRange(`${col}9`).format.font={name:'Arial',size:17,bold:true,color:ink};o.getRange(`${col}9`).setNumberFormat(col==='D'?'0.0%':'#,##0');}
chart(o,'line',[a.getRange('G8:G32'),a.getRange('B8:B32')],'Published complaints by month','A12','L28');
o.getRange('A30').values=[['Change the product selector on Analysis. Capacity assumptions are editable on Capacity.']];
o.getRange('A32').values=[['Published complaints are not customer complaint rates. Recent complete months may backfill.']];

const c=setup('Capacity','L33');title(c,'Review capacity · weekly scenario');c.tabColor=blue;
c.getRange('A4').values=[['Illustrative review effort; historical not-timely records are not a live unresolved backlog.']];
c.getRange('A6:B6').values=[['Review month',new Date(summary.latest_complete_month)]];c.getRange('B6').setNumberFormat('mmm yyyy');
c.getRange('A7').values=[['Selected records']];c.getRange('B7').formulas=[["=SUMIFS('Monthly Source'!$F$8:$F$55,'Monthly Source'!$A$8:$A$55,B6)"]];
c.getRange('A9:B12').values=[['Reviewers',2],['Hours / reviewer',20],['Minutes / review',30],['Productive time',.75]];c.getRange('A6:A12').format.columnWidth=24;c.getRange('B9:B12').format.fill=input;c.getRange('B12').setNumberFormat('0%');
c.getRange('B9').dataValidation={rule:{type:'whole',operator:'between',formula1:0,formula2:100}};
c.getRange('B10').dataValidation={rule:{type:'decimal',operator:'between',formula1:0,formula2:168}};
c.getRange('B11').dataValidation={rule:{type:'decimal',operator:'between',formula1:1,formula2:480}};
c.getRange('B12').dataValidation={rule:{type:'decimal',operator:'between',formula1:.01,formula2:1}};
c.getRange('D6:E12').values=[['Available minutes',null],['Minutes per review',null],['Weekly capacity',null],['Reviewable records',null],['Remaining records',null],['Review effort (hours)',null],['Input status',null]];c.getRange('D6:D12').format.columnWidth=25;
c.getRange('E6:E12').formulas=[['=IF(COUNT(B9:B12)<>4,"n.a.",IF(OR(B9<0,B10<0,B11<=0,B12<=0,B12>1),"n.a.",B9*B10*60*B12))'],['=IF(ISNUMBER(B11),B11,"n.a.")'],['=IF(ISNUMBER(E6),INT(E6/E7),"n.a.")'],['=IF(ISNUMBER(E8),MIN(B7,E8),"n.a.")'],['=IF(ISNUMBER(E8),MAX(0,B7-E8),"n.a.")'],['=IF(AND(ISNUMBER(B11),B11>0),B7*B11/60,"n.a.")'],['=IF(ISNUMBER(E8),"Inputs valid","Enter valid inputs")']];
c.getRange('E8:E10').setNumberFormat('#,##0');c.getRange('E11').setNumberFormat('0.0');c.getRange('E12').format.columnWidth=23;
chart(c,'bar',c.getRange('D9:E10'),'Records within weekly capacity','A16','H26');
c.getRange('J9').values=[['Amber cells are editable.']];c.getRange('J11').values=[['No source data is changed.']];

const pv=setup('Pivot Analysis','L36');title(pv,'Pivot analysis · monthly complaints');pv.getRange('A4').values=[['Native PivotTable: product filter and slicer, month rows, summed complaints. Source: all 48 monthly aggregates.']];
pv.getRange('A6:B6').values=[['Product','(All)']];pv.getRange('A8:B8').values=[['Month','Complaints']];header(pv,'A8:B8');
const byMonth=dates.map(d=>monthly.filter(r=>r.month===d).reduce((s,r)=>s+r.complaints,0));
pv.getRange('A9:B32').values=dates.map((d,i)=>[new Date(d).toLocaleDateString('en-US',{month:'short',year:'numeric',timeZone:'UTC'}),byMonth[i]]);pv.getRange('A33:B33').values=[['Grand Total',summary.complete.complaints]];pv.getRange('B9:B33').setNumberFormat('#,##0');pv.getRange('A6:B33').format.columnWidth=24;
chart(pv,'bar',pv.getRange('A8:B32'),'Monthly published complaints','D12','L33');

const u=setup('UAT','J31');title(u,'User acceptance testing');u.getRange('A4').values=[['Human acceptance: pending. Developer test evidence is separate; no stakeholder sign-off is claimed.']];
const heads=['Test ID','Requirement','Scenario','Steps','Expected result','Actual result','Status','Reviewer','Evidence / defect','Developer check reference'];
u.getRange('A6:J6').values=[heads];u.getRange('A7:J30').values=uat.map(r=>heads.map(h=>r[h]));table(u,'A6:J30','AcceptanceTests');header(u,'A6:J6');
for(const col of ['C','D','E','F','I','J'])u.getRange(`${col}6:${col}30`).format.columnWidth=col==='D'||col==='E'?62:34;
u.getRange('A7:J30').format.rowHeight=82;u.getRange('C7:J30').format.wrapText=true;u.getRange('F7:I30').format.fill=input;
u.getRange('G7:G30').dataValidation={rule:{type:'list',values:['Not run','Pass','Fail','Blocked']}};
u.getRange('G7:G30').conditionalFormats.add('containsText',{text:'Fail',format:{fill:'#f4ddd0',font:{color:'#8e412b',bold:true}}});u.freezePanes.freezeRows(6);

const r=setup('Read Me','H25');title(r,'Workbook guide');r.tabColor='#b8b8b0';r.getRange('A5:B18').values=[
 ['Purpose','Analyze published banking complaints and practice an auditable business analysis workflow.'],
 ['Source','CFPB Consumer Complaint Database. '+lock.source],
 ['Snapshot',lock.as_of+'; complete months '+lock.complete_start+' to '+summary.latest_complete_month.slice(0,7)+'.'],
 ['Population',summary.complete.complaints+' records across 24 complete months. Partial month excluded from analysis.'],
 ['Detail extract','Newest 500 complete-month records. Not representative; do not extrapolate its percentages.'],
 ['Rates','Timely Yes / (Yes + No). Unknown statuses remain separate. No resolution duration is inferred.'],
 ['Controls','Analysis B4 selects product. Capacity B9:B12 are assumptions. Amber cells are editable.'],
 ['Lookups','Detail uses XLOOKUP into the simulated team mapping. Identifiers remain text.'],
 ['Pivot','Pivot Analysis contains a native PivotTable and product filter. Refresh it after source changes.'],
 ['Refresh','Rebuild the pipeline and workbook from the frozen source, or replace matching source table rows and refresh calculations/pivots.'],
 ['UAT','Human test statuses start Not run. Enter actual results, reviewer and evidence after executing a case.'],
 ['Limits','Complaint counts are not customer incidence, market share, legal findings, or an unresolved backlog.'],
 ['Review checks','Analysis J18:J20 compare source totals with independent pipeline controls. Zero means reconciled.'],
 ['Verification','Formula calculations, input changes, charts and workbook package structure are checked. See reports/excel_verification.json for native Excel verification status.']];
r.getRange('A5:A18').format.columnWidth=20;r.getRange('B5:B18').format.columnWidth=108;r.getRange('A5:B18').format.rowHeight=45;r.getRange('B5:B18').format.wrapText=true;

wb.recalculate();
const checks=[];function assertEq(name,actual,expected){if(typeof expected==='number'?Math.abs(actual-expected)>1e-9:actual!==expected)throw Error(`${name}: ${actual} != ${expected}`);checks.push({name,actual,expected});}
assertEq('Full-population count',a.getRange('B35').values[0][0],summary.complete.complaints);
assertEq('Known denominator',a.getRange('D35').values[0][0],summary.complete.known);
assertEq('Weighted timely rate',a.getRange('E35').values[0][0],summary.complete.timely_rate);
assertEq('Capacity base',c.getRange('E8').values[0][0],60);
c.getRange('B9').values=[[0]];wb.recalculate();assertEq('Zero reviewers capacity',c.getRange('E8').values[0][0],0);assertEq('Zero reviewers remaining',c.getRange('E10').values[0][0],c.getRange('B7').values[0][0]);
c.getRange('B9').values=[[null]];wb.recalculate();assertEq('Blank input unavailable',c.getRange('E8').values[0][0],'n.a.');c.getRange('B9').values=[[2]];
a.getRange('B4').values=[['Credit card']];wb.recalculate();assertEq('Product selector',a.getRange('B35').values[0][0],summary.products['Credit card']);a.getRange('B4').values=[['All products']];
const firstTeam=sample[0].product==='Credit card'?'Card operations':'Deposit operations';assertEq('Detail XLOOKUP',det.getRange('M8').values[0][0],firstTeam);
look.getRange(sample[0].product==='Credit card'?'B7':'B8').values=[['Test team']];wb.recalculate();assertEq('Lookup reacts to source change',det.getRange('M8').values[0][0],'Test team');look.getRange(sample[0].product==='Credit card'?'B7':'B8').values=[[firstTeam]];
wb.recalculate();
const errorScan=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},summary:'Final formula errors'});
console.log(errorScan.ndjson);
console.log((await wb.inspect({kind:'table',range:'Analysis!A35:E35',include:'values,formulas',tableMaxRows:1,tableMaxCols:5})).ndjson);
await fs.writeFile(`${root}/reports/excel_verification.json`,JSON.stringify({engine:'Artifact Tool calculation engine',checks,formula_error_scan:errorScan.ndjson,native_excel:'Not verified: macOS computer-use permissions pending',human_uat:'Not run'},null,2));
const output=await SpreadsheetFile.exportXlsx(wb);await output.save(`${root}/excel/BankPulse.xlsx`);
for(const [name,range] of [['Overview','A1:L33'],['Analysis','A1:G35'],['Capacity','A1:H31'],['Pivot Analysis','A1:L34'],['Detail','A1:F12'],['Monthly Source','A1:H15'],['Lookups','A1:D10'],['UAT','A1:E10'],['Read Me','A1:B18']]){
 const preview=await wb.render({sheetName:name,range,scale:1.4,format:'png'});await fs.writeFile(`${previewDir}/${name.replaceAll(' ','-')}.png`,new Uint8Array(await preview.arrayBuffer()));
}
console.log('Workbook exported and rendered.');
