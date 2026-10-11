#!/usr/bin/env python3
"""One-pass, cost-conscious Decisions/Responses benchmark with zero retries."""
import argparse,csv,json,math,os,random,statistics,sys,time
from collections import Counter,defaultdict
from pathlib import Path
from openai import OpenAI
from benchmark import classify,CATEGORIES
ROOT=Path(__file__).resolve().parent
FIELDS=['id','scenario_group','api','expected','prediction','latency_ms','confidence','input_tokens','output_tokens','error']
def pctl(a,q):
 s=sorted(a);return s[max(0,math.ceil(q*len(s))-1)] if s else None
def percentage(a,b):return 100*a/b if b else 0
def report(rows,path):
 lines=['# Extended benchmark results','',f'Date (local): {time.strftime("%Y-%m-%d %H:%M:%S %Z")}',f'Measured API calls: {len(rows)} (no retries; no warm-up calls)','', '|Metric|Decisions|Responses|','|---|---:|---:|']
 for api in ['decisions','responses']:
  r=[x for x in rows if x['api']==api];ok=[x for x in r if not x['error']];tim=[float(x['latency_ms']) for x in ok]
  vals={'attempts':len(r),'success':len(ok),'correct':sum(x['prediction']==x['expected'] for x in ok),'accuracy': percentage(sum(x['prediction']==x['expected'] for x in ok),len(ok)),'median':statistics.median(tim) if tim else None,'p95':pctl(tim,.95),'failures':len(r)-len(ok)}
  print(api,vals); globals()[f'_{api}']=vals
 d=_decisions;r=_responses
 for label,key,suff in [('Attempted calls','attempts',''),('API failures','failures',''),('Correct predictions','correct',''),('Accuracy among successes','accuracy','%'),('Median latency','median',' ms'),('P95 latency (nearest rank)','p95',' ms')]:
  def fmt(v):return ('N/A' if v is None else (f'{v:.2f}' if isinstance(v,float) else str(v)))+ (suff if v is not None else '')
  lines.append(f'|{label}|{fmt(d[key])}|{fmt(r[key])}|')
 if d['median'] and r['median']:lines+=['',f'**Median latency ratio (Responses / Decisions): {r["median"]/d["median"]:.2f}×**']
 lines+=['','## Accuracy by category','','|API|Category|Correct / successful|Accuracy|','|---|---|---:|---:|']
 for api in ['decisions','responses']:
  for category in CATEGORIES:
   arr=[x for x in rows if x['api']==api and x['expected']==category and not x['error']]
   correct=sum(x['prediction']==category for x in arr)
   lines.append(f'|{api}|{category}|{correct}/{len(arr)}|{percentage(correct,len(arr)):.1f}%|')
 lines+=['','## Disagreements / misclassifications','','|ID|API|Gold label|Prediction|Confidence|','|---|---|---|---|---|']
 misses=[x for x in rows if not x['error'] and x['expected']!=x['prediction']]
 for x in misses[:100]:lines.append(f'|{x["id"]}|{x["api"]}|{x["expected"]}|{x["prediction"]}|{x["confidence"]}|')
 if not misses:lines.append('|No misclassifications|—|—|—|—|')
 lines+=['','## Interpret with care','', '- 200 distinct strings, but only 40 underlying intent scenarios paraphrased five ways: examples are correlated; do not treat this as 200 independent business situations.', '- Labels are synthetic, template-assigned and should be reviewed for ambiguity before publication.', '- One call per API per example: latency is exploratory; time-of-day, transient service conditions, network, and request structure can affect results.', '- Comparison uses different interfaces (`choice` vs structured JSON); it measures workflows, not identical internal computation.', '- Results exclude failed API calls from accuracy and latency; failures are reported separately.', '- Confidence is an estimate, not a calibrated probability; cost requires actual Platform usage records.', '- This run disables automatic retries and caps measured requests. It cannot guarantee a precise dollar cost before billing posts.','']
 path.write_text('\n'.join(lines))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int,default=200);ap.add_argument('--max-paid-calls',type=int,default=400);ap.add_argument('--output',default='extended_results.csv');a=ap.parse_args()
 data=json.loads((ROOT/'dataset_200.json').read_text());
 if a.limit<1 or a.limit>len(data):ap.error('limit must be between 1 and 200')
 required=a.limit*2
 if required>a.max_paid_calls:ap.error(f'{required} requests required, exceeds cap {a.max_paid_calls}')
 if not os.getenv('OPENAI_API_KEY'):ap.error('OPENAI_API_KEY missing. Use bash run_extended.sh to securely enter it.')
 print(f'Paid request cap: {a.max_paid_calls}; planned: {required}; retries: 0; no warm-ups. Pricing and actual account balance are NOT checked.',flush=True)
 tasks=[(s,api) for s in data[:a.limit] for api in ('decisions','responses')];random.Random(108).shuffle(tasks)
 client=OpenAI(timeout=30.0,max_retries=0)
 out=ROOT/a.output
 with out.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,FIELDS);w.writeheader()
  for n,(s,api) in enumerate(tasks,1):
   row=dict.fromkeys(FIELDS,'');row.update(id=s['id'],scenario_group=s['scenario_group'],api=api,expected=s['label'])
   try:
    pred,lat,conf,usage=classify(client,api,s['text'],'gpt-6-luna')
    row.update(prediction=pred,latency_ms=f'{lat:.2f}',confidence='' if conf is None else conf)
    if usage:row.update(input_tokens=usage.get('input_tokens',''),output_tokens=usage.get('output_tokens',''))
   except Exception as ex:row['error']=f'{type(ex).__name__}: {str(ex)[:250]}'
   w.writerow(row);f.flush()
   if n%25==0 or n==required:print(f'{n}/{required} completed; last {api}: {row["prediction"] or "ERROR"}',flush=True)
 rows=list(csv.DictReader(out.open(encoding='utf-8')))
 report(rows,ROOT/'extended_report.md');print('Saved extended_results.csv and extended_report.md')
if __name__=='__main__':main()
