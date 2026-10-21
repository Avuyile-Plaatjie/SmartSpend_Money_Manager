import streamlit as st
import pandas as pd, numpy as np, plotly.express as px, re
from pathlib import Path
from datetime import date
try:
 import pdfplumber
except ImportError:
 pdfplumber=None

st.set_page_config(page_title="SmartSpend | Your Money, Made Clear",page_icon="💠",layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}.stApp{background:#F5F8FC;color:#17243A}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#14213D,#1D4660)}[data-testid="stSidebar"] *{color:#F5F7FB}
.hero{background:linear-gradient(115deg,#14213D,#24516B 62%,#2E8A88);padding:34px 36px;border-radius:22px;color:white;margin-bottom:22px}
.hero h1{font-family:Manrope,sans-serif;font-size:35px;color:white;margin:0 0 10px}.hero p{color:#E3EDF6;line-height:1.65;margin:0;max-width:900px}
.eyebrow{font-size:11px;font-weight:800;letter-spacing:1.7px;text-transform:uppercase;color:#A9E5DD;margin-bottom:10px}
.section-title{font-family:Manrope,sans-serif;font-size:23px;font-weight:800;color:#17243A;margin:5px 0}.section-sub{color:#68778D;font-size:14px;margin-bottom:16px}
.panel,.step,.metric{background:white;border:1px solid #E2E9F2;border-radius:16px;padding:19px;box-shadow:0 4px 14px #18304e08}
.step{height:100%;min-height:145px}.step-no{font-size:11px;letter-spacing:1.4px;font-weight:800;color:#16877E}.step h3{font-size:16px;margin:9px 0 7px}.step p{font-size:13px;line-height:1.55;color:#68778D}
.mlabel{font-size:11px;color:#65758A;font-weight:800;text-transform:uppercase;letter-spacing:.65px}.mvalue{font-family:Manrope,sans-serif;font-size:25px;font-weight:800;color:#17243A;margin-top:6px}.mnote{font-size:12px;color:#7B899B;margin-top:4px}
.tip{background:#EAF7F3;border-left:4px solid #279B83;border-radius:11px;padding:15px 17px;margin:10px 0;color:#194D45;line-height:1.55}.caution{background:#FFF5E5;border-left:4px solid #E4A23A;border-radius:11px;padding:15px 17px;margin:10px 0;color:#7B4A0A;line-height:1.55}.info{background:#EEF4FF;border-left:4px solid #6085D7;border-radius:11px;padding:15px 17px;margin:10px 0;color:#29466F;line-height:1.55}
.stButton>button{border-radius:10px;font-weight:700;min-height:42px}div[data-testid="stMetric"]{background:#fff;border:1px solid #E2E9F2;padding:14px;border-radius:14px}.small-note{font-size:12px;color:#738197}
</style>""",unsafe_allow_html=True)

DEMO=Path(__file__).parent/"data"/"demo_transactions.csv"
def cash(x): return f"R {float(x):,.2f}"
def metric(label,value,note): st.markdown(f'<div class="metric"><div class="mlabel">{label}</div><div class="mvalue">{value}</div><div class="mnote">{note}</div></div>',unsafe_allow_html=True)
def header(k,t,p): st.markdown(f'<div class="hero"><div class="eyebrow">{k}</div><h1>{t}</h1><p>{p}</p></div>',unsafe_allow_html=True)
def norm(x): return re.sub(r"[^a-z0-9]+","_",str(x).lower()).strip("_")
def amount(x):
 if pd.isna(x): return np.nan
 if isinstance(x,(float,int,np.number)): return float(x)
 s=str(x).replace("R","").replace("ZAR","").replace(" ","").strip()
 if s.startswith("(") and s.endswith(")"): s="-"+s[1:-1]
 if "," in s and "." in s:
  s=s.replace(".","").replace(",",".") if s.rfind(",")>s.rfind(".") else s.replace(",","")
 elif "," in s:
  a=s.split(","); s="".join(a[:-1])+"."+a[-1] if len(a[-1])==2 else "".join(a)
 try: return float(re.sub(r"[^0-9.\-]","",s))
 except: return np.nan
def category(desc):
 s=str(desc).lower()
 rules=[
 (["salary","payroll","wage","stipend","payment received","income"],"Income"),
 (["rent","landlord","accommodation","residence"],"Housing"),
 (["checkers","pick n pay","picknpay","woolworths","spar","shoprite","grocery","groceries","supermarket"],"Groceries"),
 (["uber eats","mr d","mrd","takeaway","take away","restaurant","kfc","mcdonald","nandos","spur","debonairs","steers","coffee","cafe"],"Takeaways & eating out"),
 (["uber","bolt","taxi","transport","petrol","fuel","shell","engen","parking","bus","train","gautrain"],"Transport"),
 (["electricity","water","municipal","prepaid","eskom"],"Utilities"),
 (["netflix","spotify","subscription","showmax","youtube premium"],"Subscriptions"),
 (["airtime","data bundle","vodacom","mtn","telkom","cell c"],"Phone & data"),
 (["discovery","medical aid","pharmacy","clicks","dis-chem","doctor","hospital"],"Health"),
 (["school","university","college","tuition","textbook"],"Education"),
 (["interest","bank fee","monthly fee","service fee","charge"],"Bank fees"),
 (["loan","credit card","debit order","repayment"],"Debt repayments")]
 for keys,cat in rules:
  if any(k in s for k in keys): return cat
 return "Other spending"
def import_table(raw,source):
 cols={norm(c):c for c in raw.columns}
 def find(keys):
  for k in keys:
   for nk,orig in cols.items():
    if nk==k or k in nk: return orig
  return None
 dcol=find(["date","transaction_date","posting_date","value_date"])
 desc=find(["description","transaction_details","details","narrative","merchant","payee","reference"])
 acol=find(["amount","transaction_amount","value"]); debit=find(["debit","withdrawal","money_out","paid_out"]); credit=find(["credit","deposit","money_in","paid_in"])
 if not dcol or not desc or not (acol or debit or credit): raise ValueError("Could not identify date, description and amount columns. Try a CSV/Excel export with columns date, description, amount, or separate debit and credit columns.")
 out=pd.DataFrame(index=raw.index)
 out["date"]=pd.to_datetime(raw[dcol],errors="coerce",dayfirst=True); out["description"]=raw[desc].fillna("").astype(str)
 if acol: out["amount"]=raw[acol].map(amount)
 else:
  db=raw[debit].map(amount).fillna(0) if debit else pd.Series(0,index=raw.index)
  cr=raw[credit].map(amount).fillna(0) if credit else pd.Series(0,index=raw.index)
  out["amount"]=cr.abs()-db.abs()
 out=out.dropna(subset=["date","amount"]); out=out[out.description.str.strip().ne("")]
 if out.empty: raise ValueError("No readable transaction rows found.")
 typecol=find(["type","transaction_type","debit_credit"])
 catcol=find(["category","transaction_category"])
 if typecol:
  typ=raw.loc[out.index,typecol].astype(str).str.lower()
  out["kind"]=np.where(typ.str.contains("income|credit|deposit|salary|received"),"income",np.where(typ.str.contains("debit|expense|withdrawal|paid"),"expense","unknown"))
 else:
  out["kind"]="unknown"
  negative=out.amount<0; out.loc[negative,"kind"]="expense"
  positive_words=out.description.str.lower().str.contains(r"salary|payroll|wage|stipend|refund|interest received|deposit|cashback|payment received|transfer from",regex=True)
  out.loc[positive_words,"kind"]="income"
 out["amount"]=out.amount.abs(); out["category"]=out.description.map(category)
 if catcol:
  supplied=raw.loc[out.index,catcol].fillna("").astype(str).str.strip()
  out.loc[supplied.ne(""),"category"]=supplied[supplied.ne("")]
 out["source"]=source
 return out.reset_index(drop=True)
def parse_pdf(file,name):
 if not pdfplumber: raise ValueError("Install PDF support with: python -m pip install pdfplumber")
 try:
  with pdfplumber.open(file) as pdf:
   tables=[]
   for page in pdf.pages: tables += page.extract_tables() or []
 except Exception: raise ValueError("Could not read this PDF. It may be password-protected or scanned; export it as CSV/Excel instead.")
 for i,row in enumerate(tables[:20]):
  if row and any("date" in str(c).lower() for c in row) and any(any(k in str(c).lower() for k in ["amount","debit","credit","description","details","transaction"]) for c in row):
   heads=[str(c or f"column_{j}") for j,c in enumerate(row)]
   data=[r[:len(heads)]+[None]*max(0,len(heads)-len(r)) for r in tables[i+1:] if r]
   return import_table(pd.DataFrame(data,columns=heads),name)
 # Simple text-PDF fallback: date, description, final numeric amount
 try:
  with pdfplumber.open(file) as pdf: lines="\n".join(p.extract_text() or "" for p in pdf.pages).splitlines()
 except: lines=[]
 found=[]
 pattern=re.compile(r"^\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\s+(.+?)\s+(-?\(?R?\s?[\d, .]+\d(?:\.\d{2})?\)?)\s*$")
 for line in lines:
  m=pattern.match(line)
  if m: found.append({"date":m.group(1),"description":m.group(2),"amount":amount(m.group(3))})
 if found: return import_table(pd.DataFrame(found),name)
 raise ValueError("This PDF layout could not be recognised. Bank PDFs vary; export the statement as CSV or Excel for more reliable import.")
def parse_payslip(file):
 if not pdfplumber: raise ValueError("Install PDF support with: python -m pip install pdfplumber")
 try:
  with pdfplumber.open(file) as pdf: text="\n".join(p.extract_text() or "" for p in pdf.pages)
 except: raise ValueError("Could not read the PDF. Enter take-home pay manually if it is scanned.")
 if not text.strip(): raise ValueError("This payslip looks scanned or image-only. Please enter take-home pay manually.")
 results={}
 for key,pattern in [("net",r"(?:net\s+(?:pay|salary|payable)|take[- ]home\s+pay|amount\s+payable|net remuneration)\s*[:\-]?\s*(?:R\s*)?([\d, ]+(?:\.\d{2})?)"),("gross",r"(?:gross\s+(?:pay|salary|remuneration|earnings))\s*[:\-]?\s*(?:R\s*)?([\d, ]+(?:\.\d{2})?)")]:
  vals=[amount(x) for x in re.findall(pattern,text,re.I)]; vals=[v for v in vals if pd.notna(v)]
  if vals: results[key]=max(vals)
 if not results: raise ValueError("Could not confidently identify net or gross pay. Enter your take-home pay manually and check it against the original.")
 return results
def suggestions(t,inc,exp,months):
 e=t[t.kind=="expense"]; total=max(e.amount.sum(),1); by=e.groupby("category").amount.sum().to_dict(); tips=[]
 eating=by.get("Takeaways & eating out",0)
 if eating/total>=.04:
  m=eating/months; tips.append(("Food & work lunches",f"Takeaways and eating out average {cash(m)} per month. Try packing lunch 2–3 days a week and keeping takeaways for planned occasions. Cutting this category by half could free roughly {cash(m*.5)} per month."))
 subs=by.get("Subscriptions",0)
 if subs: tips.append(("Review subscriptions",f"Subscriptions average {cash(subs/months)} per month. Keep the services you use, and consider pausing any that no longer feel worth the cost."))
 grocery=by.get("Groceries",0)
 if grocery: tips.append(("Plan before grocery shopping",f"Groceries average {cash(grocery/months)} per month. Plan a few meals, shop with a list and compare unit prices to reduce impulse purchases."))
 fees=by.get("Bank fees",0)
 if fees: tips.append(("Check bank charges",f"Bank fees average {cash(fees/months)} per month. Review your account's fee structure and avoid unnecessary withdrawals or declined-payment fees where possible."))
 transport=by.get("Transport",0)
 if transport: tips.append(("Make transport more predictable",f"Transport averages {cash(transport/months)} per month. Where practical, combine errands or compare commute options to reduce avoidable trips."))
 debt=by.get("Debt repayments",0)
 if debt: tips.append(("Keep required repayments visible","Prioritise required repayments and contact your lender early if you may miss one. Avoid using new credit to cover everyday costs without understanding the full cost."))
 if inc and exp/inc>=.9: tips.insert(0,("Start with the essentials", "Your recorded expenses use a large share of recorded income. First confirm the statement is complete, then prioritise housing, food, transport, utilities and required repayments before optional spending."))
 if inc and exp>inc: tips.insert(0,("Your budget may be under pressure",f"Recorded expenses exceed recorded income by {cash(exp-inc)} in this period. Check that all income is included, then review flexible spending and upcoming bills. Avoid sudden decisions based on one report."))
 if not tips: tips.append(("Build a small buffer","If essential costs are covered, consider setting aside an affordable amount on payday for unexpected expenses. Start small and keep money available for necessities."))
 return tips

with st.sidebar:
 st.markdown("## 💠 SmartSpend"); st.caption("YOUR MONEY, MADE CLEAR"); st.markdown("---")
 page=st.radio("YOUR MONEY",["Home","Upload & build report","Your report","Spending breakdown","How it works & privacy"])
 st.markdown("---"); st.markdown("**A simple process**\n\n1. Upload records\n2. Review transactions\n3. Read your report\n4. Choose a practical next step")
 st.caption("No bank connection. Check imported values.")
if "transactions" not in st.session_state: st.session_state.transactions=pd.DataFrame()
if "payslip" not in st.session_state: st.session_state.payslip=None

if page=="Home":
 header("PERSONAL MONEY PLANNING","A clearer picture of your money starts here.","Upload a bank statement or payslip to build a straightforward money report. See income, spending patterns and practical ways to make your money go further.")
 a,b,c=st.columns(3)
 with a: st.markdown('<div class="step"><div class="step-no">STEP 01</div><h3>Bring your records</h3><p>Upload a bank statement (CSV, Excel or supported PDF) or readable PDF payslip.</p></div>',unsafe_allow_html=True)
 with b: st.markdown('<div class="step"><div class="step-no">STEP 02</div><h3>Check the numbers</h3><p>Review imported transactions and correct any income/expense labels that are wrong.</p></div>',unsafe_allow_html=True)
 with c: st.markdown('<div class="step"><div class="step-no">STEP 03</div><h3>Get your report</h3><p>See income, expenses, spending categories and realistic suggestions for saving money.</p></div>',unsafe_allow_html=True)
 st.write("")
 if st.session_state.transactions.empty: st.markdown('<div class="info"><b>Ready when you are.</b> Choose <b>Upload & build report</b> in the left menu. You can load fictional sample data to try the whole experience without uploading personal files.</div>',unsafe_allow_html=True)
 else:
  t=st.session_state.transactions; inc=t.loc[t.kind=="income","amount"].sum(); exp=t.loc[t.kind=="expense","amount"].sum()
  a,b,c,d=st.columns(4)
  with a: metric("Recorded income",cash(inc),"Imported records")
  with b: metric("Recorded expenses",cash(exp),"Imported records")
  with c: metric("Money left over",cash(inc-exp),"Income less expenses")
  with d: metric("Transactions",str(len(t)),"Review before relying on report")
 st.markdown("### Made for everyday life")
 a,b=st.columns(2)
 with a: st.markdown('<div class="panel"><h4>For students</h4><p>Understand transport, groceries, data, subscriptions and day-to-day spending.</p></div>',unsafe_allow_html=True)
 with b: st.markdown('<div class="panel"><h4>For people who work</h4><p>Compare take-home pay with regular costs and find a realistic next step before payday.</p></div>',unsafe_allow_html=True)

elif page=="Upload & build report":
 header("STEP 01 • ADD YOUR RECORDS","Let's build your money report.","CSV and Excel bank statements are usually the most reliable. A payslip can confirm income, but a bank statement is needed to analyse spending.")
 st.markdown('<div class="info"><b>Privacy first:</b> files are processed by this running app; it does not connect to your bank. Avoid files containing PINs, passwords or unnecessary identity details. Verify imported values.</div>',unsafe_allow_html=True)
 st.markdown("### A. Upload a bank statement")
 uploads=st.file_uploader("Choose statement files",type=["csv","xlsx","xls","pdf"],accept_multiple_files=True)
 if uploads:
  all_imported=[]; messages=[]
  for f in uploads:
   try:
    ext=f.name.lower().rsplit(".",1)[-1]
    if ext=="csv": raw=pd.read_csv(f); tr=import_table(raw,f.name)
    elif ext in ["xlsx","xls"]: tr=import_table(pd.read_excel(f),f.name)
    else: tr=parse_pdf(f,f.name)
    all_imported.append(tr); messages.append((True,f"{f.name}: {len(tr)} transactions imported"))
   except Exception as e: messages.append((False,f"{f.name}: {e}"))
  for ok,msg in messages: (st.success if ok else st.warning)(msg)
  if all_imported and st.button("Use imported statements",type="primary",use_container_width=True):
   t=pd.concat(all_imported,ignore_index=True).drop_duplicates(subset=["date","description","amount","source"]).sort_values("date")
   st.session_state.transactions=t.reset_index(drop=True); st.success(f"Loaded {len(t)} transactions. Review transaction types below.")
 st.markdown("### B. Upload a payslip")
 payfile=st.file_uploader("Choose a text-based PDF payslip",type=["pdf"],key="pay")
 if payfile:
  try:
   p=parse_payslip(payfile); st.session_state.payslip=p
   a,b=st.columns(2)
   with a: st.metric("Net / take-home pay",cash(p["net"]) if p.get("net") is not None else "Not found")
   with b: st.metric("Gross pay",cash(p["gross"]) if p.get("gross") is not None else "Not found")
   st.warning("Confirm these values against your payslip. Do not add the same salary twice if it already appears in your bank statement.")
  except Exception as e: st.warning(str(e))
 st.markdown("### C. Enter take-home pay manually")
 with st.form("manual"):
  pay=st.number_input("Monthly take-home pay (ZAR)",min_value=0.0,value=0.0,step=250.0)
  paydate=st.date_input("Pay date",value=date.today())
  go=st.form_submit_button("Add income")
 if go and pay>0:
  row=pd.DataFrame([{"date":pd.Timestamp(paydate),"description":"Manual take-home pay","amount":pay,"kind":"income","category":"Income","source":"Manual entry"}])
  st.session_state.transactions=pd.concat([st.session_state.transactions,row],ignore_index=True).sort_values("date").reset_index(drop=True)
  st.success("Income added. Avoid adding it again if the same salary is already in your statement.")
 st.markdown("---"); st.markdown("### Review imported transactions")
 if not st.session_state.transactions.empty:
  t=st.session_state.transactions.copy()
  st.markdown('<div class="caution"><b>Important:</b> bank exports differ. Some use positive amounts for debits. Check every Type field before saving the review.</div>',unsafe_allow_html=True)
  edited=st.data_editor(t[["date","description","amount","kind","category","source"]],use_container_width=True,hide_index=True,num_rows="dynamic",column_config={"date":st.column_config.DateColumn("Date"),"amount":st.column_config.NumberColumn("Amount (ZAR)",format="R %.2f",min_value=0),"kind":st.column_config.SelectboxColumn("Type",options=["income","expense","unknown"],required=True),"category":st.column_config.TextColumn("Category")})
  if st.button("Save reviewed transactions",type="primary"):
   edited["date"]=pd.to_datetime(edited.date,errors="coerce"); edited["amount"]=pd.to_numeric(edited.amount,errors="coerce")
   edited=edited.dropna(subset=["date","amount"]); edited["kind"]=edited.kind.astype(str).str.lower()
   st.session_state.transactions=edited.reset_index(drop=True); st.success("Review saved.")
  st.download_button("Download reviewed transactions CSV",st.session_state.transactions.to_csv(index=False).encode(),file_name="reviewed_transactions.csv",mime="text/csv")
 else: st.info("Transactions appear here after import. Or load the demonstration data below.")
 if st.button("Load demonstration data"):
  st.session_state.transactions=pd.read_csv(DEMO,parse_dates=["date"]); st.session_state.payslip=None
  st.success("Fictional sample transactions loaded.")

elif page=="Your report":
 header("YOUR PERSONAL MONEY REPORT","Your money, explained clearly.","This report is based on the records you uploaded. Check the transaction list before making decisions.")
 if st.session_state.transactions.empty: st.markdown('<div class="info">No report yet. Open <b>Upload & build report</b>, upload a statement or load the demonstration data, and review the transactions.</div>',unsafe_allow_html=True)
 else:
  t=st.session_state.transactions.copy(); t["date"]=pd.to_datetime(t.date,errors="coerce"); t["amount"]=pd.to_numeric(t.amount,errors="coerce").fillna(0)
  inc=float(t.loc[t.kind=="income","amount"].sum()); exp=float(t.loc[t.kind=="expense","amount"].sum()); unk=float(t.loc[t.kind=="unknown","amount"].sum())
  months=max(1,(t.date.max().to_period("M")-t.date.min().to_period("M")).n+1)
  st.markdown(f"**Period covered:** {t.date.min():%d %b %Y} – {t.date.max():%d %b %Y} · **{months} month(s)**")
  a,b,c,d=st.columns(4)
  with a: metric("Income recorded",cash(inc),"Rows marked income")
  with b: metric("Expenses recorded",cash(exp),"Rows marked expense")
  with c: metric("Money left over",cash(inc-exp),"Income minus expenses")
  with d: metric("Needs review",cash(unk),"Unclassified rows")
  if unk: st.markdown(f'<div class="caution"><b>Review needed:</b> {cash(unk)} is unclassified. Return to Upload & build report and label those rows as income or expense before relying on this report.</div>',unsafe_allow_html=True)
  if inc and exp>inc: st.markdown(f'<div class="caution"><b>Your recorded spending is higher than recorded income</b> by {cash(exp-inc)}. First check that all income is included, then prioritise housing, food, transport, utilities and required repayments.</div>',unsafe_allow_html=True)
  elif inc and exp/inc>=.9: st.markdown(f'<div class="caution"><b>Your budget may be tight.</b> About {exp/inc:.0%} of recorded income went to recorded expenses. Try one or two manageable changes rather than changing everything at once.</div>',unsafe_allow_html=True)
  elif inc: st.markdown(f'<div class="tip"><b>You have room to plan.</b> Recorded expenses used about {exp/inc:.0%} of recorded income. If essentials are covered, consider putting a small amount aside for unexpected costs.</div>',unsafe_allow_html=True)
  else: st.markdown('<div class="caution">No income was identified. Check the Type field or add take-home pay. Your statement may not include every income source.</div>',unsafe_allow_html=True)
  st.markdown("### Your monthly picture")
  t["month"]=t.date.dt.to_period("M").dt.to_timestamp()
  sm=t[t.kind.isin(["income","expense"])].pivot_table(index="month",columns="kind",values="amount",aggfunc="sum",fill_value=0).reset_index()
  for col in ["income","expense"]:
   if col not in sm: sm[col]=0
  sm["left_over"]=sm["income"]-sm["expense"]
  l,r=st.columns([1.3,1])
  with l:
   long=sm.melt(id_vars="month",value_vars=["income","expense"],var_name="type",value_name="amount")
   fig=px.bar(long,x="month",y="amount",color="type",barmode="group",color_discrete_map={"income":"#188C80","expense":"#5978CF"},labels={"month":"Month","amount":"Amount (ZAR)","type":"Record"})
   fig.update_layout(height=320,margin=dict(l=5,r=5,t=15,b=5),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
   st.plotly_chart(fig,use_container_width=True)
  with r:
   fig=px.area(sm,x="month",y="left_over",color_discrete_sequence=["#2A9388"],labels={"month":"Month","left_over":"Left over (ZAR)"})
   fig.add_hline(y=0,line_dash="dash",line_color="#9AA9BC"); fig.update_layout(height=320,margin=dict(l=5,r=5,t=15,b=5),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
   st.plotly_chart(fig,use_container_width=True)
  st.markdown("### Practical ways to make your money go further")
  for title,body in suggestions(t,inc,exp,months):
   st.markdown(f'<div class="panel"><b>{title}</b><p style="margin:7px 0 0;color:#53657B;line-height:1.6">{body}</p></div>',unsafe_allow_html=True)
  if st.session_state.payslip:
   p=st.session_state.payslip; a,b=st.columns(2)
   with a: metric("Payslip net pay",cash(p["net"]) if p.get("net") is not None else "Not found","Check original payslip")
   with b: metric("Payslip gross pay",cash(p["gross"]) if p.get("gross") is not None else "Not found","Before deductions")
  st.download_button("Download reviewed report data (CSV)",t.drop(columns=["month"],errors="ignore").to_csv(index=False).encode(),file_name="smartspend_report.csv",mime="text/csv",type="primary")

elif page=="Spending breakdown":
 header("EXPLORE YOUR SPENDING","See which categories take the biggest share.","A high amount is a clue to investigate, not automatically a cost to cut. Housing, groceries and transport may be essential.")
 if st.session_state.transactions.empty: st.info("Upload records first or load the demonstration data.")
 else:
  t=st.session_state.transactions; e=t[t.kind=="expense"].copy()
  if e.empty: st.info("No rows are marked as expenses. Review transaction types first.")
  else:
   start=e.date.min().date(); end=e.date.max().date(); dates=st.date_input("Filter period",value=(start,end),min_value=start,max_value=end)
   if isinstance(dates,tuple) and len(dates)==2: e=e[(pd.to_datetime(e.date).dt.date>=dates[0])&(pd.to_datetime(e.date).dt.date<=dates[1])]
   if e.empty: st.info("No expenses in that period.")
   else:
    by=e.groupby("category",as_index=False).amount.sum().sort_values("amount",ascending=False); total=by.amount.sum()
    if total:
     top=by.iloc[0]; st.markdown(f'<div class="tip"><b>Largest category:</b> {top.category} accounts for {cash(top.amount)} ({top.amount/total:.0%}) of recorded expenses in this period. Check what is essential, recurring or optional before changing your budget.</div>',unsafe_allow_html=True)
     a,b=st.columns([1.2,1])
     with a:
      fig=px.bar(by.sort_values("amount"),x="amount",y="category",orientation="h",color="amount",color_continuous_scale=["#CDEBE6","#167D7A"],labels={"amount":"Amount (ZAR)","category":"Category"}); fig.update_layout(coloraxis_showscale=False,height=360)
      st.plotly_chart(fig,use_container_width=True)
     with b:
      fig=px.pie(by,values="amount",names="category",hole=.58,color_discrete_sequence=["#16877E","#5B7BD0","#E9A23B","#9D83D5","#61A6A0","#D36F70","#6F879D"]); fig.update_layout(height=360)
      st.plotly_chart(fig,use_container_width=True)
     by["share"]=by.amount/total
     st.dataframe(by.rename(columns={"category":"Category","amount":"Total (ZAR)","share":"Share of expenses"}).style.format({"Total (ZAR)":"R {:,.2f}","Share of expenses":"{:.1%}"}),use_container_width=True,hide_index=True)
     with st.expander("View expense transactions"): st.dataframe(e.sort_values("date",ascending=False),use_container_width=True,hide_index=True)

else:
 header("TRANSPARENCY & PRIVACY","Understand how your report is created.","SmartSpend summarises the records you provide. It does not connect to your bank or make decisions on your behalf.")
 st.markdown("### Supported files")
 st.markdown("- **CSV / Excel bank statements:** best supported. Date, description and amount columns are expected; separate debit and credit columns are supported.\n- **Text-based PDF statements:** some layouts can be read, but formats vary. Export CSV/Excel if a PDF fails.\n- **PDF payslips:** common net/gross pay labels are detected. Always confirm values against the original.\n- **Scanned PDFs:** may not be readable. Enter take-home pay manually or export a text-based file.")
 st.markdown("### Important checks")
 st.markdown("- Positive amounts can represent debits depending on the bank. Review the Type column.\n- A payslip confirms income but cannot show expenses.\n- Do not count salary twice if it appears in both payslip and bank statement.\n- Transfers between your own accounts may be mistaken for spending unless recategorised.\n- The report only reflects the files provided; it may miss cash spending, other accounts or income sources.")
 st.markdown("### Privacy and responsible use")
 st.markdown("- Do not upload PINs, passwords, full card numbers or bank credentials.\n- If you deploy this app online, review hosting security, access and retention before accepting real financial records.\n- Suggestions are general budgeting ideas, not professional financial, tax, credit or investment advice.")
 st.markdown('<div class="caution"><b>For your submission:</b> test with fictional demo data, then a redacted CSV export. Verify transaction types and all imported amounts before presenting a report. PDF parsing varies by bank.</div>',unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div class="small-note">SMARTSPEND · A practical personal money organiser · Amounts shown in South African rand (ZAR)</div>',unsafe_allow_html=True)
