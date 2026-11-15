import pandas as pd, numpy as np
from pathlib import Path

EIA="/home/hatch/workspace/pjm-capacity-stack/raw/eia860m_sep2026.xlsx"
OUT=Path("/home/hatch/workspace/miso-capacity-stack/eia_explore_miso.txt")
COAL={"ANT","BIT","LIG","SUB","WC"}; OIL={"DFO","RFO","JF","KER","PC"}
def eia_fuel(row):
    esc, pm = row["Energy Source Code"], row["Prime Mover Code"]
    if pm in ("BA","FW"): return "Battery Storage"
    if pm=="PS": return "Pumped Storage"
    if esc=="NUC": return "Nuclear"
    if esc=="SUN": return "Solar"
    if esc=="WND": return "Wind"
    if esc=="WAT": return "Hydro"
    if esc=="NG": return "Natural Gas"
    if esc in COAL: return "Coal"
    if esc in OIL: return "Oil"
    return "Other"
def load(name):
    df=pd.read_excel(EIA, sheet_name=name, header=2)
    for c in ["Nameplate Capacity (MW)","Net Summer Capacity (MW)","Net Winter Capacity (MW)"]:
        if c in df.columns: df[c]=pd.to_numeric(df[c], errors="coerce")
    return df

op=load("Operating"); pl=load("Planned"); rt=load("Retired")
for df in (op,pl,rt): df["fuel"]=df.apply(eia_fuel,axis=1)
mop=op[op["Balancing Authority Code"]=="MISO"].copy()
mpl=pl[pl["Balancing Authority Code"]=="MISO"].copy()
mrt=rt[rt["Balancing Authority Code"]=="MISO"].copy()

L=[]
def w(s=""): L.append(s)
def table(df, cols, title):
    w(title); w(df.to_string() if len(df) else "(empty)"); w("")
def agg(df, mw="Nameplate Capacity (MW)"):
    return df.groupby("fuel")[mw].sum().round(1)
FUELS=["Coal","Natural Gas","Nuclear","Solar","Wind","Hydro","Pumped Storage","Battery Storage","Oil","Other"]

w("EIA-860M September 2026 vintage — BA = MISO exploration")
w("Source: /home/hatch/workspace/pjm-capacity-stack/raw/eia860m_sep2026.xlsx")
w("Logic mirrored from /home/hatch/workspace/pjm-capacity-stack/build_stack.py load_eia_sheet/eia_fuel/eia_changelog, BA='MISO' instead of 'PJM'. Sheets read with pd.read_excel(header=2).")
w("Fuel buckets: Coal ANT/BIT/LIG/SUB/WC; Natural Gas NG; Nuclear NUC; Solar SUN; Wind WND; Hydro WAT; Pumped Storage prime mover PS; Battery prime mover BA/FW; Oil DFO/RFO/JF/KER/PC; else Other.")
w(f"Raw sheet row counts (all BAs): Operating {len(op)}, Planned {len(pl)}, Retired {len(rt)}")
w(f"BA=MISO row counts: Operating {len(mop)}, Planned {len(mpl)}, Retired {len(mrt)}")
w("")

# 1
w("="*80); w("1. OPERATING SHEET, BA=MISO — ALL STATUSES")
w(f"Units: {len(mop)}  Total nameplate: {mop['Nameplate Capacity (MW)'].sum():,.1f} MW  Total net summer: {mop['Net Summer Capacity (MW)'].sum():,.1f} MW  Total net winter: {mop['Net Winter Capacity (MW)'].sum():,.1f} MW")
w("Status values present (units / nameplate MW):")
w(mop.groupby("Status").agg(units=("Plant ID","size"), nameplate_MW=("Nameplate Capacity (MW)","sum"), netsummer_MW=("Net Summer Capacity (MW)","sum")).round(1).to_string())
w("")
w("By fuel — ALL statuses:")
t=pd.DataFrame({"units":mop.groupby("fuel").size(),"nameplate_MW":agg(mop),"netsummer_MW":agg(mop,"Net Summer Capacity (MW)"),"netwinter_MW":agg(mop,"Net Winter Capacity (MW)")}).reindex(FUELS).fillna(0)
t.loc["TOTAL"]=[len(mop), mop["Nameplate Capacity (MW)"].sum(), mop["Net Summer Capacity (MW)"].sum(), mop["Net Winter Capacity (MW)"].sum()]
w(t.round(1).to_string()); w("")
w("OP-status only: '(OP) Operating'")
oponly=mop[mop["Status"]=="(OP) Operating"]
w(f"Units: {len(oponly)}  Nameplate: {oponly['Nameplate Capacity (MW)'].sum():,.1f} MW  Net summer: {oponly['Net Summer Capacity (MW)'].sum():,.1f} MW")
t2=pd.DataFrame({"units":oponly.groupby("fuel").size(),"nameplate_MW":agg(oponly),"netsummer_MW":agg(oponly,"Net Summer Capacity (MW)")}).reindex(FUELS).fillna(0)
t2.loc["TOTAL"]=[len(oponly), oponly["Nameplate Capacity (MW)"].sum(), oponly["Net Summer Capacity (MW)"].sum()]
w(t2.round(1).to_string()); w("")
w("Non-OP (Status != '(OP) Operating') — by fuel, and by status x fuel:")
nonop=mop[mop["Status"]!="(OP) Operating"]
w(f"Units: {len(nonop)}  Nameplate: {nonop['Nameplate Capacity (MW)'].sum():,.1f} MW  Net summer: {nonop['Net Summer Capacity (MW)'].sum():,.1f} MW")
t3=pd.DataFrame({"units":nonop.groupby("fuel").size(),"nameplate_MW":agg(nonop),"netsummer_MW":agg(nonop,"Net Summer Capacity (MW)")}).reindex(FUELS).fillna(0)
t3.loc["TOTAL"]=[len(nonop), nonop["Nameplate Capacity (MW)"].sum(), nonop["Net Summer Capacity (MW)"].sum()]
w(t3.round(1).to_string()); w("")
w(nonop.pivot_table(index="Status", columns="fuel", values="Nameplate Capacity (MW)", aggfunc="sum", margins=True, margins_name="TOTAL").round(1).fillna(0).to_string()); w("")
w("Non-OP unit counts by status x fuel:")
w(nonop.pivot_table(index="Status", columns="fuel", values="Plant ID", aggfunc="count", margins=True, margins_name="TOTAL").fillna(0).astype(int).to_string()); w("")

# 2
w("="*80); w("2. OPERATING SHEET, BA=MISO, OPERATING YEAR == 2026 (in service Jan-Sep 2026)")
y26=mop[pd.to_numeric(mop["Operating Year"],errors="coerce")==2026]
w(f"Units: {len(y26)}  Nameplate: {y26['Nameplate Capacity (MW)'].sum():,.1f} MW  Net summer: {y26['Net Summer Capacity (MW)'].sum():,.1f} MW")
t=pd.DataFrame({"units":y26.groupby("fuel").size(),"nameplate_MW":agg(y26),"netsummer_MW":agg(y26,"Net Summer Capacity (MW)")}).reindex(FUELS).fillna(0)
t.loc["TOTAL"]=[len(y26), y26["Nameplate Capacity (MW)"].sum(), y26["Net Summer Capacity (MW)"].sum()]
w(t.round(1).to_string()); w("")
w("Unit list (by month):")
cols=["Plant Name","Plant State","Plant ID","Generator ID","fuel","Nameplate Capacity (MW)","Net Summer Capacity (MW)","Operating Month","Operating Year","Status","Technology","Energy Source Code","Prime Mover Code"]
w(y26.sort_values(["Operating Month","Plant Name"])[cols].to_string(index=False)); w("")

# 3
w("="*80); w("3. PLANNED SHEET, BA=MISO, PLANNED OPERATION YEAR 2026-2031")
mpl["poy"]=pd.to_numeric(mpl["Planned Operation Year"],errors="coerce")
mpl["pom"]=pd.to_numeric(mpl["Planned Operation Month"],errors="coerce")
p26_31=mpl[mpl["poy"].between(2026,2031)].copy()
w(f"All BA=MISO Planned rows: {len(mpl)}  Planned Operation Year 2026-2031: {len(p26_31)} units, {p26_31['Nameplate Capacity (MW)'].sum():,.1f} MW nameplate, {p26_31['Net Summer Capacity (MW)'].sum():,.1f} MW net summer")
w(f"Planned rows with missing Planned Operation Year: {int(mpl['poy'].isna().sum())}  (nameplate {mpl[mpl['poy'].isna()]['Nameplate Capacity (MW)'].sum():,.1f} MW)")
w("Planned Operation Year distribution (all BA=MISO Planned rows):")
w(mpl.groupby(mpl["poy"].fillna("MISSING")).agg(units=("Plant ID","size"), nameplate_MW=("Nameplate Capacity (MW)","sum")).round(1).to_string()); w("")
w("MW by year x fuel (nameplate MW), 2026-2031:")
piv=p26_31.pivot_table(index="poy", columns="fuel", values="Nameplate Capacity (MW)", aggfunc="sum", margins=True, margins_name="TOTAL").reindex(columns=FUELS+["TOTAL"]).round(1).fillna(0)
w(piv.to_string()); w("")
w("Unit counts by year x fuel, 2026-2031:")
w(p26_31.pivot_table(index="poy", columns="fuel", values="Plant ID", aggfunc="count", margins=True, margins_name="TOTAL").reindex(columns=FUELS+["TOTAL"]).fillna(0).astype(int).to_string()); w("")
w("MW by year (totals):")
w(p26_31.groupby("poy").agg(units=("Plant ID","size"), nameplate_MW=("Nameplate Capacity (MW)","sum"), netsummer_MW=("Net Summer Capacity (MW)","sum")).round(1).to_string()); w("")
w("By fuel (2026-2031 totals):")
t=pd.DataFrame({"units":p26_31.groupby("fuel").size(),"nameplate_MW":agg(p26_31),"netsummer_MW":agg(p26_31,"Net Summer Capacity (MW)")}).reindex(FUELS).fillna(0)
t.loc["TOTAL"]=[len(p26_31), p26_31["Nameplate Capacity (MW)"].sum(), p26_31["Net Summer Capacity (MW)"].sum()]
w(t.round(1).to_string()); w("")
w("By status x fuel (nameplate MW), 2026-2031:")
w(p26_31.pivot_table(index="Status", columns="fuel", values="Nameplate Capacity (MW)", aggfunc="sum", margins=True, margins_name="TOTAL").round(1).fillna(0).to_string()); w("")
w("By status x fuel (unit counts), 2026-2031:")
w(p26_31.pivot_table(index="Status", columns="fuel", values="Plant ID", aggfunc="count", margins=True, margins_name="TOTAL").fillna(0).astype(int).to_string()); w("")
w("Status values in Planned 2026-2031 (units / MW):")
w(p26_31.groupby("Status").agg(units=("Plant ID","size"), nameplate_MW=("Nameplate Capacity (MW)","sum")).round(1).to_string()); w("")
w("TOP 20 LARGEST PLANNED ADDITIONS, 2026-2031 (by nameplate MW):")
top=p26_31.sort_values("Nameplate Capacity (MW)", ascending=False).head(20)
for i,(_,r) in enumerate(top.iterrows(),1):
    w(f"{i:2d}. {r['Plant Name']} — {r['Plant State']}, Plant {r['Plant ID']}, Gen {r['Generator ID']}, {r['fuel']} ({r['Energy Source Code']}/{r['Prime Mover Code']}), {r['Nameplate Capacity (MW)']:,.1f} MW nameplate / {r['Net Summer Capacity (MW)']:,.1f} MW net summer, planned {int(r['poy'])}-{int(r['pom']) if not pd.isna(r['pom']) else '?':02d}, status {r['Status']}")
w("")

# 4
w("="*80); w("4. RETIRED SHEET, BA=MISO, RETIREMENT YEAR == 2026")
mrt["ry"]=pd.to_numeric(mrt["Retirement Year"],errors="coerce")
rt26=mrt[mrt["ry"]==2026]
w(f"All BA=MISO Retired rows: {len(mrt)}  Retirement Year == 2026: {len(rt26)} units, {rt26['Nameplate Capacity (MW)'].sum():,.1f} MW nameplate, {rt26['Net Summer Capacity (MW)'].sum():,.1f} MW net summer")
w("Retirement Year distribution (all BA=MISO Retired rows):")
w(mrt.groupby(mrt["ry"].fillna("MISSING")).agg(units=("Plant ID","size"), nameplate_MW=("Nameplate Capacity (MW)","sum")).round(1).to_string()); w("")
t=pd.DataFrame({"units":rt26.groupby("fuel").size(),"nameplate_MW":agg(rt26),"netsummer_MW":agg(rt26,"Net Summer Capacity (MW)")}).reindex(FUELS).fillna(0)
t.loc["TOTAL"]=[len(rt26), rt26["Nameplate Capacity (MW)"].sum(), rt26["Net Summer Capacity (MW)"].sum()]
w(t.round(1).to_string()); w("")
w("Unit list, Retirement Year 2026:")
cols=["Plant Name","Plant State","Plant ID","Generator ID","fuel","Nameplate Capacity (MW)","Net Summer Capacity (MW)","Retirement Month","Retirement Year","Technology","Energy Source Code","Prime Mover Code"]
w(rt26.sort_values(["Retirement Month","Plant Name"])[cols].to_string(index=False) if len(rt26) else "(none)"); w("")

# 5
w("="*80); w("5. OPERATING SHEET, BA=MISO, PLANNED RETIREMENTS (Planned Retirement Year 2026-2036)")
mop["pry"]=pd.to_numeric(mop["Planned Retirement Year"],errors="coerce")
mop["prm"]=pd.to_numeric(mop["Planned Retirement Month"],errors="coerce")
pr=mop[mop["pry"].between(2026,2036)].copy()
w(f"Operating units with any Planned Retirement Year: {int(mop['pry'].notna().sum())}  In 2026-2036: {len(pr)} units, {pr['Nameplate Capacity (MW)'].sum():,.1f} MW nameplate, {pr['Net Summer Capacity (MW)'].sum():,.1f} MW net summer")
w("Planned Retirement Year distribution (all BA=MISO Operating rows with a planned retirement year):")
w(mop[mop['pry'].notna()].groupby("pry").agg(units=("Plant ID","size"), nameplate_MW=("Nameplate Capacity (MW)","sum"), netsummer_MW=("Net Summer Capacity (MW)","sum")).round(1).to_string()); w("")
w("MW by year x fuel (nameplate MW), planned retirements 2026-2036:")
piv=pr.pivot_table(index="pry", columns="fuel", values="Nameplate Capacity (MW)", aggfunc="sum", margins=True, margins_name="TOTAL").reindex(columns=FUELS+["TOTAL"]).round(1).fillna(0)
w(piv.to_string()); w("")
w("Unit counts by year x fuel, planned retirements 2026-2036:")
w(pr.pivot_table(index="pry", columns="fuel", values="Plant ID", aggfunc="count", margins=True, margins_name="TOTAL").reindex(columns=FUELS+["TOTAL"]).fillna(0).astype(int).to_string()); w("")
w("MW by year (totals), planned retirements:")
w(pr.groupby("pry").agg(units=("Plant ID","size"), nameplate_MW=("Nameplate Capacity (MW)","sum"), netsummer_MW=("Net Summer Capacity (MW)","sum")).round(1).to_string()); w("")
w("By fuel (2026-2036 totals):")
t=pd.DataFrame({"units":pr.groupby("fuel").size(),"nameplate_MW":agg(pr),"netsummer_MW":agg(pr,"Net Summer Capacity (MW)")}).reindex(FUELS).fillna(0)
t.loc["TOTAL"]=[len(pr), pr["Nameplate Capacity (MW)"].sum(), pr["Net Summer Capacity (MW)"].sum()]
w(t.round(1).to_string()); w("")
w("TOP 20 LARGEST PLANNED RETIREMENTS, 2026-2036 (by nameplate MW):")
top=pr.sort_values("Nameplate Capacity (MW)", ascending=False).head(20)
for i,(_,r) in enumerate(top.iterrows(),1):
    w(f"{i:2d}. {r['Plant Name']} — {r['Plant State']}, Plant {r['Plant ID']}, Gen {r['Generator ID']}, {r['fuel']} ({r['Energy Source Code']}/{r['Prime Mover Code']}), {r['Nameplate Capacity (MW)']:,.1f} MW nameplate / {r['Net Summer Capacity (MW)']:,.1f} MW net summer, planned retirement {int(r['pry'])}-{int(r['prm']) if not pd.isna(r['prm']) else '?':02d}, status {r['Status']}")
w("")
w("Overlap guard (PJM-script style): Retired-2026 units also appearing as Operating planned-retirement-2026:")
k=lambda d: set(zip(d["Plant ID"].astype(str), d["Generator ID"].astype(str)))
w(f"  overlap = {len(k(rt26) & k(mop[mop['pry']==2026]))} units")
w(f"Overlap guard: Operating-2026 units also in Planned-2026: {len(k(y26) & k(mpl[mpl['poy']==2026]))} units")
w("")

# 6
w("="*80); w("6. STATE DISTRIBUTION — BA=MISO OPERATING PLANTS")
expected=["ND","SD","MN","WI","MI","IA","IL","IN","MO","KY","AR","LA","MS","TX"]
w("MW by state (nameplate, all BA=MISO Operating units):")
st=mop.groupby("Plant State").agg(units=("Plant ID","size"), nameplate_MW=("Nameplate Capacity (MW)","sum"), netsummer_MW=("Net Summer Capacity (MW)","sum")).sort_values("nameplate_MW", ascending=False).round(1)
w(st.to_string()); w("")
w(f"States present: {sorted(mop['Plant State'].dropna().unique().tolist())}  ({mop['Plant State'].nunique()} states)")
outside=sorted(set(mop['Plant State'].dropna().unique())-set(expected))
w(f"States OUTSIDE expected set {expected}: {outside if outside else 'NONE'}")
if outside:
    o=mop[mop["Plant State"].isin(outside)]
    w(o.groupby("Plant State").agg(units=("Plant ID","size"), nameplate_MW=("Nameplate Capacity (MW)","sum")).round(1).to_string())
    w("Outside-set plants (largest first):")
    w(o.sort_values("Nameplate Capacity (MW)",ascending=False)[["Plant Name","Plant State","Plant ID","Generator ID","fuel","Nameplate Capacity (MW)","Status"]].head(30).to_string(index=False))
w(f"States in expected set with ZERO BA=MISO Operating units: {sorted(set(expected)-set(mop['Plant State'].dropna().unique()))}")
w(f"TOTAL BA=MISO Operating units: {len(mop)}  Total nameplate: {mop['Nameplate Capacity (MW)'].sum():,.1f} MW  Total net summer: {mop['Net Summer Capacity (MW)'].sum():,.1f} MW")
w("")
w("For reference — footprint-state check (PJM-script style, reversed): Operating units in expected MISO states whose BA is NOT MISO:")
in_states=op[op["Plant State"].isin(expected)]
out_ba=in_states[in_states["Balancing Authority Code"]!="MISO"]
w(f"  Units: {len(out_ba)}  Nameplate: {out_ba['Nameplate Capacity (MW)'].sum():,.1f} MW")
w(out_ba.groupby("Balancing Authority Code").agg(units=("Plant ID","size"), nameplate_MW=("Nameplate Capacity (MW)","sum")).round(1).sort_values("nameplate_MW",ascending=False).to_string()); w("")

# 7
w("="*80); w("7. DATA QUIRKS")
w(f"Missing Nameplate Capacity (MW): Operating BA=MISO {int(mop['Nameplate Capacity (MW)'].isna().sum())} / {len(mop)}; Planned BA=MISO {int(mpl['Nameplate Capacity (MW)'].isna().sum())} / {len(mpl)}; Retired BA=MISO {int(mrt['Nameplate Capacity (MW)'].isna().sum())} / {len(mrt)}")
w(f"Missing Net Summer Capacity (MW): Operating BA=MISO {int(mop['Net Summer Capacity (MW)'].isna().sum())}; Planned {int(mpl['Net Summer Capacity (MW)'].isna().sum())}; Retired {int(mrt['Net Summer Capacity (MW)'].isna().sum())}")
w(f"Missing Energy Source Code: Operating BA=MISO {int(mop['Energy Source Code'].isna().sum())}; Planned {int(mpl['Energy Source Code'].isna().sum())}; Retired {int(mrt['Energy Source Code'].isna().sum())}")
w(f"Missing Prime Mover Code: Operating BA=MISO {int(mop['Prime Mover Code'].isna().sum())}; Planned {int(mpl['Prime Mover Code'].isna().sum())}; Retired {int(mrt['Prime Mover Code'].isna().sum())}")
w(f"Missing Plant State: Operating BA=MISO {int(mop['Plant State'].isna().sum())}; Planned {int(mpl['Plant State'].isna().sum())}")
w(f"Missing Balancing Authority Code (all sheets): Operating {int(op['Balancing Authority Code'].isna().sum())}, Planned {int(pl['Balancing Authority Code'].isna().sum())}, Retired {int(rt['Balancing Authority Code'].isna().sum())}")
w("")
w("Fuel bucket 'Other' rows — BA=MISO (all sheets):")
for nm,df in [("Operating",mop),("Planned",mpl),("Retired",mrt)]:
    o=df[df["fuel"]=="Other"]
    w(f"  {nm}: {len(o)} units, {o['Nameplate Capacity (MW)'].sum():,.1f} MW")
    if len(o): w(o.groupby(["Energy Source Code","Prime Mover Code"]).agg(units=("Plant ID","size"), nameplate_MW=("Nameplate Capacity (MW)","sum")).round(1).to_string())
w("")
w("Prime mover HY rows (task note: Hydro = WAT + prime mover HY; script's eia_fuel only maps esc==WAT to Hydro):")
for nm,df in [("Operating",mop),("Planned",mpl),("Retired",mrt)]:
    hy=df[df["Prime Mover Code"]=="HY"]
    w(f"  {nm} BA=MISO: {len(hy)} HY units, {hy['Nameplate Capacity (MW)'].sum():,.1f} MW; of those, esc==WAT: {int((hy['Energy Source Code']=='WAT').sum())}, esc!=WAT: {int((hy['Energy Source Code']!='WAT').sum())}, fuel buckets: {hy['fuel'].value_counts().to_dict()}")
    if len(hy) and (hy['Energy Source Code']!='WAT').any():
        w(hy[hy['Energy Source Code']!='WAT'][["Plant Name","Plant State","Plant ID","Generator ID","Energy Source Code","Prime Mover Code","fuel","Nameplate Capacity (MW)"]].to_string(index=False))
w("")
w("Ambiguous / notable fuel+prime-mover combos, BA=MISO Operating:")
w(mop.groupby(["Energy Source Code","Prime Mover Code","fuel"]).agg(units=("Plant ID","size"), nameplate_MW=("Nameplate Capacity (MW)","sum")).round(1).sort_values("nameplate_MW",ascending=False).to_string()); w("")
w("Planned additions with Planned Operation Year beyond 2031 (BA=MISO):")
beyond=mpl[mpl["poy"]>2031]
w(f"  {len(beyond)} units, {beyond['Nameplate Capacity (MW)'].sum():,.1f} MW")
if len(beyond):
    w(beyond.groupby("poy").agg(units=("Plant ID","size"), nameplate_MW=("Nameplate Capacity (MW)","sum")).round(1).to_string())
    w(beyond.sort_values(["poy","Nameplate Capacity (MW)"],ascending=[True,False])[["Plant Name","Plant State","Plant ID","Generator ID","fuel","Nameplate Capacity (MW)","Planned Operation Month","Planned Operation Year","Status"]].to_string(index=False))
w("")
w("Planned additions with Planned Operation Year before 2026 (BA=MISO) — stale/delayed rows:")
old=mpl[mpl["poy"]<2026]
w(f"  {len(old)} units, {old['Nameplate Capacity (MW)'].sum():,.1f} MW; years: {sorted(old['poy'].dropna().unique().tolist())}")
w("")
w("Planned retirements beyond 2036 (BA=MISO Operating):")
beyond_r=mop[mop["pry"]>2036]
w(f"  {len(beyond_r)} units, {beyond_r['Nameplate Capacity (MW)'].sum():,.1f} MW")
if len(beyond_r):
    w(beyond_r.groupby("pry").agg(units=("Plant ID","size"), nameplate_MW=("Nameplate Capacity (MW)","sum")).round(1).to_string())
    w(beyond_r.sort_values(["pry","Nameplate Capacity (MW)"],ascending=[True,False])[["Plant Name","Plant State","Plant ID","Generator ID","fuel","Nameplate Capacity (MW)","Planned Retirement Month","Planned Retirement Year","Status"]].to_string(index=False))
w("")
w("Planned retirements before 2026 (BA=MISO Operating) — stale rows still on Operating sheet:")
old_r=mop[mop["pry"]<2026]
w(f"  {len(old_r)} units, {old_r['Nameplate Capacity (MW)'].sum():,.1f} MW; years: {sorted(old_r['pry'].dropna().unique().tolist())}")
w("")
w("Zero / negative nameplate rows, BA=MISO:")
for nm,df in [("Operating",mop),("Planned",mpl),("Retired",mrt)]:
    z=df[df["Nameplate Capacity (MW)"].fillna(0)<=0]
    w(f"  {nm}: {len(z)} rows <=0 MW")
    if len(z): w(z[["Plant Name","Plant State","Plant ID","Generator ID","fuel","Nameplate Capacity (MW)","Status"]].to_string(index=False))
w("")
w("Duplicate (Plant ID, Generator ID) rows within BA=MISO sheets:")
for nm,df in [("Operating",mop),("Planned",mpl),("Retired",mrt)]:
    d=df.duplicated(subset=["Plant ID","Generator ID"], keep=False)
    w(f"  {nm}: {int(d.sum())} rows in duplicated keys ({df[df.duplicated(subset=['Plant ID','Generator ID'])].shape[0]} extra rows)")
w("")
w("DC Net Capacity (MW) present for solar/battery rows (nameplate vs DC check, BA=MISO Operating Solar+Battery):")
sb=mop[mop["fuel"].isin(["Solar","Battery Storage"])]
dc=pd.to_numeric(sb['DC Net Capacity (MW)'], errors="coerce")
w(f"  Solar+Battery units: {len(sb)}, nameplate {sb['Nameplate Capacity (MW)'].sum():,.1f} MW, DC net {dc.sum():,.1f} MW, DC missing {int(dc.isna().sum())}")
w("")
w("END OF EXPLORATION")
OUT.write_text("\n".join(L))
print("\n".join(L[:60]))
print("... written to", OUT, "lines:", len(L))
