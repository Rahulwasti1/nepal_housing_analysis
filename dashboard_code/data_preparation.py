import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import ast

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: LOAD PRE-CLEANED DATASET
# ─────────────────────────────────────────────────────────────────────────────
df = pd.read_csv("Nepali_house_cleaned.csv")

print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
print(f"Districts: {df['Location_district'].value_counts().to_dict()}")
print(f"Price range: Rs.{df['Price_in_cr'].min():.2f}Cr — Rs.{df['Price_in_cr'].max():.2f}Cr")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: COLUMN ALIASES for convenience
# ─────────────────────────────────────────────────────────────────────────────
df = df.rename(columns={
    'Location_district': 'DISTRICT',
    'Location_area':     'AREA',
    'Price_in_cr':       'PRICE_CR',
    'Land_area_aana':    'LAND_AANA',
    'Price_per_aana':    'PRICE_PER_AANA',
    'Road_access_ft':    'ROAD_FT',
    'Built_year_bs':     'BUILT_YEAR_BS',
    'Has_parking':       'HAS_PARKING',
    'Amenity_count':     'AMENITY_COUNT',
    'Floor':             'FLOOR',
    'Bedroom':           'BEDROOM',
    'Bathroom':          'BATHROOM',
    'Facing':            'FACING',
    'Title':             'TITLE',
})

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: SHARED STYLE
# ─────────────────────────────────────────────────────────────────────────────
COLORS = {'Kathmandu':'#D55E00','Lalitpur':'#0072B2','Bhaktapur':'#E69F00'}
HL     = dict(bgcolor='white', bordercolor='#E2E8F0',
              font=dict(family='DM Sans', size=11, color='#0F172A'))
FONT   = dict(family='DM Sans', size=11, color='#64748B')

def base_layout(**kw):
    l = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#FAFAFA',
             font=FONT, hoverlabel=HL, margin=dict(t=6,b=32,l=44,r=10),
             xaxis=dict(gridcolor='#F1F5F9', showline=False),
             yaxis=dict(gridcolor='#F1F5F9', showline=False))
    l.update(kw); return l

# ─────────────────────────────────────────────────────────────────────────────
# VIZ 1 — Price Distribution Histogram
# ─────────────────────────────────────────────────────────────────────────────
fig1 = go.Figure()
for dist in ['Kathmandu','Lalitpur','Bhaktapur']:
    sub = df[df['DISTRICT']==dist]
    fig1.add_trace(go.Histogram(
        x=sub['PRICE_CR'], name=dist, nbinsx=50, opacity=0.75,
        marker_color=COLORS[dist],
        hovertemplate=f'<b>{dist}</b><br>Price: Rs.%{{x:.2f}}Cr<br>Count: %{{y}}<extra></extra>'
    ))

affordable_pct = round(len(df[df['PRICE_CR']<2])/len(df)*100,1)
midrange_pct   = round(len(df[(df['PRICE_CR']>=2)&(df['PRICE_CR']<=5)])/len(df)*100,1)
luxury_pct     = round(len(df[df['PRICE_CR']>5])/len(df)*100,1)
median_price   = df['PRICE_CR'].median()

fig1.add_vrect(x0=0.5, x1=2.0, fillcolor='#009E73', opacity=0.07, line_width=0)
fig1.add_vrect(x0=2.0, x1=5.0, fillcolor='#0077BB', opacity=0.07, line_width=0)
fig1.add_vrect(x0=5.0, x1=35,  fillcolor='#AA3377', opacity=0.07, line_width=0)

for x, txt, col in [(1.25,'Affordable<br>(<Rs.2Cr)','#009E73'),
                    (3.5, 'Mid-Range<br>(Rs.2-5Cr)','#0077BB'),
                    (6.5, 'Luxury<br>(>Rs.5Cr)',    '#AA3377')]:
    fig1.add_annotation(x=x, y=1.08, text=txt, showarrow=False,
        xref='x', yref='paper', font=dict(size=10,color=col), align='center')

for x, pct, col in [(1.25,affordable_pct,'#009E73'),
                    (3.5, midrange_pct,  '#0077BB'),
                    (6.5, luxury_pct,    '#AA3377')]:
    fig1.add_annotation(x=x, y=0.08, text=f'{pct}% of listings',
        showarrow=False, xref='x', yref='paper',
        font=dict(size=9,color=col), bgcolor='white',
        bordercolor=col, borderwidth=1, align='center')

fig1.add_vline(x=median_price, line_dash='dash', line_color='black', line_width=2)
fig1.add_annotation(x=median_price+0.2, y=0.94,
    text=f'Median: Rs.{median_price:.2f}Cr', showarrow=False,
    xref='x', yref='paper', font=dict(size=10,color='black'),
    bgcolor='white', bordercolor='black', borderwidth=1)

fig1.update_layout(base_layout(
    barmode='overlay', bargap=0.05,
    xaxis=dict(title='Price (Crore NPR)', gridcolor='#F1F5F9',
               range=[0,df['PRICE_CR'].max()+0.5]),
    yaxis=dict(title='Number of Houses', gridcolor='#F1F5F9'),
    legend=dict(x=0.78,y=0.97,bgcolor='rgba(255,255,255,0.92)',
                bordercolor='#E2E8F0',borderwidth=1,font_size=10),
    margin=dict(t=70,b=32,l=44,r=10)
))

# ─────────────────────────────────────────────────────────────────────────────
# VIZ 2 — Top 5 Most Expensive vs Affordable Areas
# ─────────────────────────────────────────────────────────────────────────────
area_stats = (df.groupby(['AREA','DISTRICT'])['PRICE_PER_AANA']
              .agg(['median','count']).reset_index())
area_stats.columns = ['Area','District','Median_PPA','Count']
area_stats = area_stats[area_stats['Count']>=5]

top5_exp  = area_stats.nlargest(5,'Median_PPA').copy()
top5_aff  = area_stats.nsmallest(5,'Median_PPA').copy()
top5_exp['Category']  = 'Most Expensive'
top5_aff['Category']  = 'Most Affordable'
combined = pd.concat([top5_exp,top5_aff],ignore_index=True)
combined['Bar_color'] = combined['District'].map(COLORS)

fig2 = go.Figure()
for cat in ['Most Affordable','Most Expensive']:
    sub = combined[combined['Category']==cat].sort_values('Median_PPA',ascending=True)
    fig2.add_trace(go.Bar(
        x=sub['Median_PPA'], y=sub['Area'], orientation='h', name=cat,
        marker=dict(color=sub['Bar_color'].tolist(), line=dict(color='white',width=1.5)),
        text=sub.apply(lambda r: f"Rs.{r['Median_PPA']:.2f}Cr ({r['District']})",axis=1),
        textposition='inside', textfont=dict(size=9,color='white'),
        customdata=sub[['District','Count']].values,
        hovertemplate='<b>%{y}</b><br>%{customdata[0]}<br>Rs.%{x:.2f}Cr/Aana<br>n=%{customdata[1]}<extra></extra>'
    ))

valley_ppa = df['PRICE_PER_AANA'].median()
fig2.add_vline(x=valley_ppa, line_dash='dot', line_color='black', line_width=1.5,
    annotation_text=f'Median: Rs.{valley_ppa:.2f}Cr',
    annotation_position='top right',
    annotation_font=dict(size=9,color='black'),
    annotation_bgcolor='white', annotation_bordercolor='black', annotation_borderwidth=1)

fig2.update_layout(base_layout(
    barmode='relative', showlegend=True,
    legend=dict(x=0.65,y=0.05,bgcolor='rgba(255,255,255,0.92)',
                bordercolor='#E2E8F0',borderwidth=1,font_size=9),
    margin=dict(t=6,b=32,l=120,r=50),
    xaxis=dict(title='Median Price per Aana (Crore NPR)',gridcolor='#F1F5F9'),
    yaxis=dict(tickfont=dict(size=9))
))

# ─────────────────────────────────────────────────────────────────────────────
# VIZ 3 — Road Width vs Price per Aana
# ─────────────────────────────────────────────────────────────────────────────
df['ROAD_CAT'] = pd.cut(df['ROAD_FT'],
    bins=[0,10,13,16,20,100],
    labels=['Narrow\n(<10ft)','Standard\n(10-13ft)',
            'Wide\n(13-16ft)','Very Wide\n(16-20ft)','Highway\n(>20ft)'])

road_stats = (df.dropna(subset=['ROAD_CAT'])
              .groupby(['ROAD_CAT','DISTRICT'],observed=True)['PRICE_PER_AANA']
              .agg(['median','count']).reset_index())
road_stats.columns = ['Road_Cat','District','Median_PPA','Count']
road_stats = road_stats[road_stats['Count']>=5]

CAT_ORDER = ['Narrow\n(<10ft)','Standard\n(10-13ft)',
             'Wide\n(13-16ft)','Very Wide\n(16-20ft)','Highway\n(>20ft)']

fig3 = go.Figure()
for dist in ['Kathmandu','Lalitpur','Bhaktapur']:
    grp = road_stats[road_stats['District']==dist]
    fig3.add_trace(go.Bar(
        x=grp['Road_Cat'].astype(str), y=grp['Median_PPA'], name=dist,
        marker_color=COLORS[dist], marker_line_color='white', marker_line_width=1.5,
        opacity=0.88,
        text=grp['Median_PPA'].round(2), texttemplate='Rs.%{text:.2f}',
        textposition='inside', textfont=dict(size=9,color='white'),
        customdata=grp['Count'].values,
        hovertemplate=f'<b>{dist}</b><br>%{{x}}<br>Rs.%{{y:.2f}}Cr/Aana<br>n=%{{customdata}}<extra></extra>'
    ))

overall = (df.dropna(subset=['ROAD_CAT'])
           .groupby('ROAD_CAT',observed=True)['PRICE_PER_AANA']
           .median().reset_index())
overall.columns = ['Road_Cat','Median_PPA']
fig3.add_trace(go.Scatter(
    x=overall['Road_Cat'].astype(str), y=overall['Median_PPA'],
    name='Valley Median', mode='lines+markers',
    line=dict(color='black',dash='dot',width=2),
    marker=dict(size=7,symbol='diamond',color='black'),
    hovertemplate='Valley Median: Rs.%{y:.2f}Cr/Aana<extra></extra>'
))

fig3.update_layout(base_layout(
    barmode='group',
    legend=dict(x=0.01,y=0.99,bgcolor='rgba(255,255,255,0.92)',
                bordercolor='#E2E8F0',borderwidth=1,font_size=10,orientation='h'),
    xaxis=dict(title='Road Width Category',gridcolor='#F1F5F9',
               categoryorder='array',categoryarray=CAT_ORDER),
    yaxis=dict(title='Median Price per Aana (Crore NPR)',gridcolor='#F1F5F9',
               range=[0,road_stats['Median_PPA'].max()*1.35])
))
df = df.drop(columns=['ROAD_CAT'])

# ─────────────────────────────────────────────────────────────────────────────
# VIZ 4 — Construction Trend
# ─────────────────────────────────────────────────────────────────────────────
year_dist = (df[df['BUILT_YEAR_BS'].between(2047,2079)]
             .groupby(['BUILT_YEAR_BS','DISTRICT']).size().reset_index(name='Count'))

fig4 = go.Figure()
for dist in ['Kathmandu','Lalitpur','Bhaktapur']:
    sub = year_dist[year_dist['DISTRICT']==dist]
    fig4.add_trace(go.Scatter(
        x=sub['BUILT_YEAR_BS'], y=sub['Count'],
        mode='lines+markers', name=dist,
        line=dict(color=COLORS[dist],width=2.5),
        marker=dict(size=5,color=COLORS[dist]),
        hovertemplate=f'<b>{dist}</b><br>%{{x}} B.S<br>%{{y}} houses<extra></extra>'
    ))

fig4.add_vline(x=2072, line_dash='dot', line_color='red', line_width=2)
fig4.add_annotation(x=2072, y=1.13, text='2072 B.S<br>Earthquake',
    showarrow=False, xref='x', yref='paper',
    font=dict(size=9,color='red'), bgcolor='white',
    bordercolor='red', borderwidth=1, align='center')

fig4.add_vline(x=2076, line_dash='dot', line_color='#E69F00', line_width=2)
fig4.add_annotation(x=2077, y=1.13, text='2076 B.S<br>COVID-19',
    showarrow=False, xref='x', yref='paper',
    font=dict(size=9,color='#E69F00'), bgcolor='white',
    bordercolor='#E69F00', borderwidth=1, align='center')

fig4.add_vrect(x0=2072, x1=2076, fillcolor='red', opacity=0.04, line_width=0)
fig4.add_vrect(x0=2076, x1=2079, fillcolor='#E69F00', opacity=0.04, line_width=0)
fig4.add_annotation(x=(2072+2076)/2, y=1.06, text='Post-Earthquake Reconstruction',
    showarrow=False, xref='x', yref='paper', font=dict(size=8,color='red'), align='center')
fig4.add_annotation(x=(2076+2079)/2, y=1.06, text='Post-COVID Recovery',
    showarrow=False, xref='x', yref='paper', font=dict(size=8,color='#E69F00'), align='center')

fig4.update_layout(base_layout(
    margin=dict(t=80,b=32,l=44,r=10),
    xaxis=dict(title='Year Built (B.S)',gridcolor='#F1F5F9',
               tickmode='linear',dtick=4,
               range=[year_dist['BUILT_YEAR_BS'].min()-0.5,2079.5]),
    yaxis=dict(title='Number of Houses Built',gridcolor='#F1F5F9'),
    legend=dict(x=0.01,y=0.99,bgcolor='rgba(255,255,255,0.92)',
                bordercolor='#E2E8F0',borderwidth=1,font_size=10)
))

# ─────────────────────────────────────────────────────────────────────────────
# VIZ 5 — Land Area vs Price Scatter
# ─────────────────────────────────────────────────────────────────────────────
fig5 = go.Figure()
for dist in ['Kathmandu','Lalitpur','Bhaktapur']:
    sub = df[(df['DISTRICT']==dist) & (df['LAND_AANA']<=20)].copy()
    fig5.add_trace(go.Scatter(
        x=sub['LAND_AANA'], y=sub['PRICE_CR'], mode='markers', name=dist,
        marker=dict(color=COLORS[dist],
                    size=sub['PRICE_PER_AANA'].apply(lambda p: max(5,min(p*12,18))),
                    line=dict(color='white',width=0.8), opacity=0.65),
        customdata=sub[['AREA','PRICE_PER_AANA','ROAD_FT']].values,
        hovertemplate=(f'<b>{dist}</b><br>%{{customdata[0]}}<br>'
                       'Land: %{x:.1f}Aana<br>Price: Rs.%{y:.2f}Cr<br>'
                       'Price/Aana: Rs.%{customdata[1]:.2f}Cr<extra></extra>')
    ))
    sub_clean = sub[['LAND_AANA','PRICE_CR']].dropna()
    if len(sub_clean)>=3:
        z = np.polyfit(sub_clean['LAND_AANA'],sub_clean['PRICE_CR'],1)
        p = np.poly1d(z)
        xl = np.linspace(sub_clean['LAND_AANA'].min(),sub_clean['LAND_AANA'].max(),100)
        fig5.add_trace(go.Scatter(x=xl,y=p(xl),mode='lines',
            line=dict(color=COLORS[dist],width=1.8,dash='dash'),
            showlegend=False,hoverinfo='skip'))

fig5.add_hline(y=df['PRICE_CR'].median(), line_dash='dot', line_color='black', line_width=1.5,
    annotation_text=f'Median: Rs.{df["PRICE_CR"].median():.2f}Cr',
    annotation_position='top left',
    annotation_font=dict(size=9,color='black'),
    annotation_bgcolor='white',annotation_bordercolor='black',annotation_borderwidth=1)
fig5.add_annotation(x=0.98,y=0.02,xref='paper',yref='paper',
    text='Bubble Size = Price per Aana',showarrow=False,
    font=dict(size=9,color='#666'),bgcolor='white',bordercolor='lightgrey',borderwidth=1)

fig5.update_layout(base_layout(
    xaxis=dict(title='Land Area (Aana)',gridcolor='#F1F5F9',dtick=2,showgrid=False),
    yaxis=dict(title='Total House Price (Crore NPR)',gridcolor='#F1F5F9',showgrid=False),
    legend=dict(x=0.01,y=0.99,bgcolor='rgba(255,255,255,0.92)',
                bordercolor='#E2E8F0',borderwidth=1,font_size=10)
))

# ─────────────────────────────────────────────────────────────────────────────
# VIZ 6 — Amenity Level vs Price
# ─────────────────────────────────────────────────────────────────────────────
df['AMENITY_GROUP'] = pd.cut(df['AMENITY_COUNT'],
    bins=[-1,0,2,5,10,100],
    labels=['None (0)','Basic (1-2)','Standard (3-5)','Premium (6-10)','Luxury (11+)'])

amenity_price = (df.groupby(['AMENITY_GROUP','DISTRICT'],observed=True)['PRICE_CR']
                 .agg(['median','count']).reset_index())
amenity_price.columns = ['Amenity_group','District','Median_Price','Count']
amenity_price = amenity_price[amenity_price['Count']>=3]

AMENITY_ORDER = ['None (0)','Basic (1-2)','Standard (3-5)','Premium (6-10)','Luxury (11+)']
fig6 = go.Figure()
for dist in ['Kathmandu','Lalitpur','Bhaktapur']:
    grp = amenity_price[amenity_price['District']==dist]
    fig6.add_trace(go.Bar(
        x=grp['Amenity_group'].astype(str), y=grp['Median_Price'], name=dist,
        marker_color=COLORS[dist], marker_line_color='white', marker_line_width=1.5,
        opacity=0.88,
        text=grp['Median_Price'].round(2), texttemplate='Rs.%{text:.2f}',
        textposition='inside', textfont=dict(size=9,color='white'),
        customdata=grp['Count'].values,
        hovertemplate=(f'<b>{dist}</b><br>%{{x}}<br>Rs.%{{y:.2f}}Cr<br>n=%{{customdata}}<extra></extra>')
    ))

fig6.add_hline(y=df['PRICE_CR'].median(), line_dash='dot', line_color='black', line_width=1.5,
    annotation_text=f'Median: Rs.{df["PRICE_CR"].median():.2f}Cr',
    annotation_position='top left',
    annotation_font=dict(size=9,color='black'),
    annotation_bgcolor='white',annotation_bordercolor='black',annotation_borderwidth=1)
fig6.add_annotation(x='Luxury (11+)', y=amenity_price['Median_Price'].max()*1.25,
    text='Diminishing returns\nbeyond Premium',
    showarrow=True, arrowhead=2, arrowcolor='grey',
    font=dict(size=9,color='#333'), bgcolor='white',
    bordercolor='lightgrey', borderwidth=1, ax=-60, ay=-30)

fig6.update_layout(base_layout(
    barmode='group',
    legend=dict(x=0.01,y=0.99,bgcolor='rgba(255,255,255,0.92)',
                bordercolor='#E2E8F0',borderwidth=1,font_size=10,orientation='h'),
    xaxis=dict(title='Amenity Level',gridcolor='#F1F5F9',
               categoryorder='array',categoryarray=AMENITY_ORDER),
    yaxis=dict(title='Median Price (Crore NPR)',gridcolor='#F1F5F9',
               range=[0,amenity_price['Median_Price'].max()*1.45])
))
df = df.drop(columns=['AMENITY_GROUP'])

# ─────────────────────────────────────────────────────────────────────────────
# VIZ 7 — Housing Segment Donut
# ─────────────────────────────────────────────────────────────────────────────
df['SEGMENT'] = pd.cut(df['PRICE_PER_AANA'],
    bins=[0,0.50,0.90,100],
    labels=['Budget (<0.5Cr/Aana)','Mid-Range (0.5-0.9Cr/Aana)','Premium (>0.9Cr/Aana)'])

SEGMENT_ORDER  = ['Budget (<0.5Cr/Aana)','Mid-Range (0.5-0.9Cr/Aana)','Premium (>0.9Cr/Aana)']
SEGMENT_COLORS = ['#AA3377','#009E73','#0077BB']

fig7 = make_subplots(rows=1,cols=3,
    specs=[[{'type':'domain'},{'type':'domain'},{'type':'domain'}]],
    subplot_titles=['Kathmandu','Lalitpur','Bhaktapur'])

for i,dist in enumerate(['Kathmandu','Lalitpur','Bhaktapur']):
    sub = df[df['DISTRICT']==dist]
    seg_counts = (sub['SEGMENT'].value_counts()
                  .reindex(SEGMENT_ORDER,fill_value=0).reset_index())
    seg_counts.columns = ['Segment','Count']
    total = seg_counts['Count'].sum()
    fig7.add_trace(go.Pie(
        labels=seg_counts['Segment'], values=seg_counts['Count'],
        name=dist, hole=0.55,
        marker=dict(colors=SEGMENT_COLORS, line=dict(color='white',width=2.5)),
        textinfo='percent', textfont=dict(size=11,color='white'),
        sort=False,
        hovertemplate=f'<b>{dist}</b><br>%{{label}}<br>%{{value}} listings · %{{percent}}<extra></extra>'
    ),row=1,col=i+1)
    fig7.add_annotation(
        text=f'<b>{dist}</b><br>{total}',
        x=[0.11,0.5,0.89][i], y=0.5,
        font=dict(size=10,color='#333'),
        showarrow=False, xref='paper', yref='paper', align='center')

fig7.update_layout(
    paper_bgcolor='rgba(0,0,0,0)', font=FONT, hoverlabel=HL,
    showlegend=True,
    legend=dict(orientation='h',x=0.5,xanchor='center',y=-0.12,
                bgcolor='rgba(255,255,255,0.92)',bordercolor='#E2E8F0',
                borderwidth=1,font_size=10),
    margin=dict(t=20,b=60,l=10,r=10)
)
df = df.drop(columns=['SEGMENT'])

# ─────────────────────────────────────────────────────────────────────────────
# VIZ 8 — Price Heatmap by Year and District
# ─────────────────────────────────────────────────────────────────────────────
heatmap_data = (df[df['BUILT_YEAR_BS'].between(2060,2079)]
                .groupby(['DISTRICT','BUILT_YEAR_BS'])['PRICE_PER_AANA']
                .agg(['median','count']).reset_index())
heatmap_data.columns = ['District','Year','Median_PPA','Count']

all_years = list(range(2060,2080))
pivot = heatmap_data.pivot(index='District',columns='Year',values='Median_PPA')
pivot = pivot.reindex(columns=all_years)
pivot = pivot.interpolate(axis=1,method='linear',limit_direction='both')
pivot = pivot.reindex(['Kathmandu','Lalitpur','Bhaktapur'])

count_pivot = (heatmap_data.pivot(index='District',columns='Year',values='Count')
               .reindex(columns=all_years).reindex(['Kathmandu','Lalitpur','Bhaktapur']).fillna(0))

text_matrix = []
for dist in ['Kathmandu','Lalitpur','Bhaktapur']:
    row = []
    for yr in all_years:
        val = pivot.loc[dist,yr]
        cnt = count_pivot.loc[dist,yr]
        if np.isnan(val): row.append('')
        elif cnt==0: row.append(f'Rs.{val:.2f}*')
        else: row.append(f'Rs.{val:.2f}')
    text_matrix.append(row)

fig8 = go.Figure(data=go.Heatmap(
    z=pivot.values, x=all_years, y=pivot.index.tolist(),
    colorscale=[[0.0,'#EFF6FF'],[0.35,'#93C5FD'],[0.70,'#2563EB'],[1.0,'#1E3A8A']],
    text=text_matrix, texttemplate='%{text}',
    textfont=dict(size=9,color='white'),
    hoverongaps=False,
    hovertemplate='<b>%{y}</b><br>%{x} B.S<br>%{text}<extra></extra>',
    colorbar=dict(title=dict(text='Price/Aana<br>(Cr NPR)',font=dict(size=9)),
                  thickness=12,len=0.7,tickfont=dict(size=9))
))
fig8.add_vline(x=2072, line_dash='dot', line_color='red', line_width=2)
fig8.add_annotation(x=2072,y=1.15,text='2072 — Earthquake',showarrow=False,
    xref='x',yref='paper',font=dict(size=9,color='red'),
    bgcolor='white',bordercolor='red',borderwidth=1,align='center')
fig8.add_vline(x=2076, line_dash='dot', line_color='#E69F00', line_width=2)
fig8.add_annotation(x=2076,y=1.15,text='2076 — COVID',showarrow=False,
    xref='x',yref='paper',font=dict(size=9,color='#E69F00'),
    bgcolor='white',bordercolor='#E69F00',borderwidth=1,align='center')
fig8.update_layout(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='white',
    font=FONT, hoverlabel=HL,
    margin=dict(t=70,b=60,l=90,r=70),
    xaxis=dict(title='Year Built (B.S)',tickmode='linear',dtick=2,showgrid=False),
    yaxis=dict(title='District',tickfont=dict(size=11),showgrid=False)
)

# ─────────────────────────────────────────────────────────────────────────────
# VIZ 9 — Amenity Scatter with Trendline
# ─────────────────────────────────────────────────────────────────────────────
amenity_agg = (df.groupby(['AMENITY_COUNT','DISTRICT'])['PRICE_PER_AANA']
               .agg(['median','count']).reset_index())
amenity_agg.columns = ['Amenity_count','District','Median_PPA','Count']
amenity_agg = amenity_agg[amenity_agg['Count']>=3]

fig9 = go.Figure()
for dist in ['Kathmandu','Lalitpur','Bhaktapur']:
    sub = amenity_agg[amenity_agg['District']==dist].sort_values('Amenity_count')
    fig9.add_trace(go.Scatter(
        x=sub['Amenity_count'], y=sub['Median_PPA'], mode='markers', name=dist,
        marker=dict(color=COLORS[dist],
                    size=sub['Count'].apply(lambda n: min(6+n*0.4,20)),
                    line=dict(color='white',width=1.5), opacity=0.85),
        customdata=sub['Count'].values,
        hovertemplate=(f'<b>{dist}</b><br>Amenities: %{{x}}<br>'
                       f'Rs.%{{y:.2f}}Cr/Aana<br>n=%{{customdata}}<extra></extra>')
    ))
    if len(sub)>=3:
        z = np.polyfit(sub['Amenity_count'],sub['Median_PPA'],1)
        p = np.poly1d(z)
        xl = np.linspace(sub['Amenity_count'].min(),sub['Amenity_count'].max(),100)
        fig9.add_trace(go.Scatter(x=xl,y=p(xl),mode='lines',
            line=dict(color=COLORS[dist],width=2,dash='dash'),
            showlegend=False,hoverinfo='skip'))

for xval,label,col in [(3,'Low','#009E73'),(6,'Standard','#0077BB'),(11,'High','#AA3377')]:
    fig9.add_vline(x=xval,line_dash='dot',line_color=col,line_width=1.2,
        annotation_text=label,annotation_position='top',
        annotation_font=dict(size=8,color=col))

fig9.add_hline(y=df['PRICE_PER_AANA'].median(),line_dash='dot',line_color='black',line_width=1.5,
    annotation_text=f'Median: Rs.{df["PRICE_PER_AANA"].median():.2f}Cr',
    annotation_position='top right',
    annotation_font=dict(size=9,color='black'),
    annotation_bgcolor='white',annotation_bordercolor='black',annotation_borderwidth=1)

fig9.update_layout(base_layout(
    xaxis=dict(title='Number of Amenities',gridcolor='#F1F5F9',dtick=1),
    yaxis=dict(title='Median Price per Aana (Crore NPR)',gridcolor='#F1F5F9'),
    legend=dict(x=0.01,y=0.99,bgcolor='rgba(255,255,255,0.92)',
                bordercolor='#E2E8F0',borderwidth=1,font_size=10)
))

# ─────────────────────────────────────────────────────────────────────────────
# ADVANCED VIZ 10 — Sunburst: Housing Market Structure
# Hierarchy: Root → District → Price Segment (with range label) → Top Areas
# ─────────────────────────────────────────────────────────────────────────────

# Feature engineering: quartile-based price segmentation
_q25 = df['PRICE_CR'].quantile(0.25)
_q50 = df['PRICE_CR'].quantile(0.50)
_q75 = df['PRICE_CR'].quantile(0.75)

def _price_seg(p):
    if p <= _q25:   return 'Affordable (<2Cr)'
    elif p <= _q50: return 'Mid-Range (2-3Cr)'
    elif p <= _q75: return 'Premium (3-5Cr)'
    else:           return 'Luxury (5Cr+)'

df['_PRICE_SEG'] = df['PRICE_CR'].apply(_price_seg)

_SEG_CFG = {
    'Affordable (<2Cr)': {'short':'Affordable', 'range':'Below 2Cr',  'color':'#059669'},
    'Mid-Range (2-3Cr)': {'short':'Mid-Range',  'range':'2 - 3 Cr',   'color':'#2563EB'},
    'Premium (3-5Cr)':   {'short':'Premium',    'range':'3 - 5 Cr',   'color':'#D97706'},
    'Luxury (5Cr+)':     {'short':'Luxury',     'range':'Above 5 Cr', 'color':'#DC2626'},
}

_sb_ids, _sb_labels, _sb_parents, _sb_values, _sb_colors, _sb_hover = [], [], [], [], [], []

# Root
_sb_ids.append('Root'); _sb_labels.append(''); _sb_parents.append('')
_sb_values.append(int(len(df))); _sb_colors.append('rgba(240,244,248,0.5)')
_sb_hover.append(f'<b>Kathmandu Valley</b><br>Total listings: {len(df):,}')

# Ring 1: District
for _dist, _dgrp in df.groupby('DISTRICT'):
    _sb_ids.append(_dist); _sb_labels.append(_dist); _sb_parents.append('Root')
    _sb_values.append(int(len(_dgrp))); _sb_colors.append(COLORS[_dist])
    _sb_hover.append(
        f'<b>{_dist}</b><br>Listings: {len(_dgrp):,}<br>'
        f'Median Price: Rs.{_dgrp["PRICE_CR"].median():.2f}Cr<br>'
        f'Median Price/Aana: Rs.{_dgrp["PRICE_PER_AANA"].median():.3f}Cr'
    )

# Ring 2: Price Segment with price range label
for (_dist, _seg), _sgrp in df.groupby(['DISTRICT', '_PRICE_SEG']):
    _cfg = _SEG_CFG[_seg]
    _sid = f'{_dist}|{_seg}'
    _sb_ids.append(_sid)
    _sb_labels.append(f'{_cfg["short"]}<br>{_cfg["range"]}')
    _sb_parents.append(_dist); _sb_values.append(int(len(_sgrp)))
    _sb_colors.append(_cfg['color'])
    _sb_hover.append(
        f'<b>{_dist} — {_cfg["short"]}</b><br>Price Range: {_cfg["range"]}<br>'
        f'Listings: {len(_sgrp):,}<br>Median Price: Rs.{_sgrp["PRICE_CR"].median():.2f}Cr<br>'
        f'Actual Range: Rs.{_sgrp["PRICE_CR"].min():.2f}–Rs.{_sgrp["PRICE_CR"].max():.2f}Cr'
    )

# Ring 3: Top 4 areas per district × segment
_area_agg = (df.groupby(['DISTRICT','_PRICE_SEG','AREA'])
               .agg(_Count=('PRICE_CR','count'), _MedPrice=('PRICE_CR','median'),
                    _MedPPA=('PRICE_PER_AANA','median')).reset_index())
_top_areas = (_area_agg[_area_agg['_Count']>=3]
               .sort_values('_Count', ascending=False)
               .groupby(['DISTRICT','_PRICE_SEG']).head(4))

for _, _row in _top_areas.iterrows():
    _cfg = _SEG_CFG[_row['_PRICE_SEG']]
    _sb_ids.append(f'{_row["DISTRICT"]}|{_row["_PRICE_SEG"]}|{_row["AREA"]}')
    _sb_labels.append(_row['AREA'])
    _sb_parents.append(f'{_row["DISTRICT"]}|{_row["_PRICE_SEG"]}')
    _sb_values.append(int(_row['_Count']))
    _ppa = float(_row['_MedPPA'])
    _sb_colors.append('#34D399' if _ppa<0.60 else '#60A5FA' if _ppa<0.75 else '#FBBF24' if _ppa<0.90 else '#F87171')
    _sb_hover.append(
        f'<b>{_row["AREA"]}</b> ({_row["DISTRICT"]})<br>'
        f'Segment: {_cfg["short"]} ({_cfg["range"]})<br>'
        f'Listings: {int(_row["_Count"]):,}<br>'
        f'Median Price: Rs.{_row["_MedPrice"]:.2f}Cr<br>'
        f'Price/Aana: Rs.{_row["_MedPPA"]:.3f}Cr'
    )

fig10 = go.Figure(go.Sunburst(
    ids=_sb_ids, labels=_sb_labels, parents=_sb_parents,
    values=_sb_values, branchvalues='total',
    marker=dict(colors=_sb_colors, line=dict(color='white', width=1.5)),
    hovertext=_sb_hover, hovertemplate='%{hovertext}<extra></extra>',
    textinfo='label+percent parent', insidetextorientation='radial',
    maxdepth=3, leaf=dict(opacity=0.88), rotation=0,
))
fig10.update_layout(
    autosize=True, margin=dict(l=10,r=10,t=10,b=10),
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family='DM Sans, sans-serif', size=11),
    annotations=[],
)
df = df.drop(columns=['_PRICE_SEG'])

# ─────────────────────────────────────────────────────────────────────────────
# VIZ 11 — Faceted Stacked Bar (Segment × Road × District)
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# ADVANCED VIZ 11 — 3D Scatter: Land vs Price vs Price-per-Aana
# X=Land Area, Y=House Price, Z=Price/Aana, size=Road width, color=District
# ─────────────────────────────────────────────────────────────────────────────
_area_df = df.groupby(['AREA','DISTRICT']).agg(
    _n          =('PRICE_CR',        'count'),
    _MedPrice   =('PRICE_CR',        'median'),
    _MinPrice   =('PRICE_CR',        'min'),
    _MaxPrice   =('PRICE_CR',        'max'),
    _MedLand    =('LAND_AANA',       'median'),
    _MedPPA     =('PRICE_PER_AANA',  'median'),
    _MedRoad    =('ROAD_FT',         'median'),
    _MedAmen    =('AMENITY_COUNT',   'median'),
).reset_index()
_area_df = _area_df[_area_df['_n'] >= 5].copy()

fig11 = go.Figure()
for _dist in ['Kathmandu','Lalitpur','Bhaktapur']:
    _sub = _area_df[_area_df['DISTRICT']==_dist]
    _sizes = [max(5, min(float(r)/20*22, 22)) for r in _sub['_MedRoad']]
    fig11.add_trace(go.Scatter3d(
        name=_dist,
        x=[float(v) for v in _sub['_MedLand']],
        y=[float(v) for v in _sub['_MedPrice']],
        z=[float(v) for v in _sub['_MedPPA']],
        text=list(_sub['AREA']),
        mode='markers',
        marker=dict(color=COLORS[_dist], size=_sizes, opacity=0.82,
                    line=dict(color='white', width=0.5), symbol='circle'),
        customdata=[[int(r['_n']), float(r['_MedRoad']),
                     float(r['_MinPrice']), float(r['_MaxPrice'])]
                    for _, r in _sub.iterrows()],
        hovertemplate=(
            '<b>%{text}</b><br>'
            'Land Area: %{x:.1f} Aana<br>'
            'Median Price: Rs.%{y:.2f}Cr<br>'
            'Price/Aana: Rs.%{z:.3f}Cr<br>'
            'Road Width: %{customdata[1]:.0f}ft<br>'
            'Price Range: Rs.%{customdata[2]:.2f}–%{customdata[3]:.2f}Cr<br>'
            'Listings: %{customdata[0]}<extra></extra>'
        ),
    ))

fig11.update_layout(
    autosize=True,
    scene=dict(
        xaxis=dict(title=dict(text='Land Area (Aana)',font=dict(size=11)),
                   gridcolor='#E2E8F0', backgroundcolor='rgba(248,250,252,0.9)'),
        yaxis=dict(title=dict(text='House Price (Cr NPR)',font=dict(size=11)),
                   tickprefix='Rs.', gridcolor='#E2E8F0',
                   backgroundcolor='rgba(248,250,252,0.9)'),
        zaxis=dict(title=dict(text='Price per Aana (Cr)',font=dict(size=11)),
                   tickprefix='Rs.', gridcolor='#E2E8F0',
                   backgroundcolor='rgba(248,250,252,0.9)'),
        camera=dict(eye=dict(x=1.8, y=-1.8, z=1.2)),
        bgcolor='rgba(248,250,252,1)',
    ),
    showlegend=True,
    legend=dict(x=0.01,y=0.99,bgcolor='rgba(255,255,255,0.85)',
                bordercolor='#E2E8F0',borderwidth=1,font=dict(size=11)),
    margin=dict(l=0,r=0,t=10,b=10),
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family='DM Sans, sans-serif', size=11),
    annotations=[dict(
        text='Bubble size = road width · Best value = large land + low Price/Aana · Drag to rotate',
        x=0.5, y=-0.01, xref='paper', yref='paper', showarrow=False,
        font=dict(size=9, color='#8892A4'), xanchor='center',
    )],
)

# ─────────────────────────────────────────────────────────────────────────────
# VIZ 12 — Bubble Scenario Matrix
# ─────────────────────────────────────────────────────────────────────────────
area_summary = df.groupby(['AREA','DISTRICT']).agg(
    Median_PPA =('PRICE_PER_AANA','median'),
    Median_Road=('ROAD_FT','median'),
    Count      =('PRICE_CR','count'),
    Median_Amen=('AMENITY_COUNT','median')
).reset_index()
area_summary = area_summary[area_summary['Count']>=5]

fig12 = go.Figure()
for dist in ['Kathmandu','Lalitpur','Bhaktapur']:
    sub = area_summary[area_summary['DISTRICT']==dist]
    fig12.add_trace(go.Scatter(
        x=sub['Median_Road'], y=sub['Median_PPA'],
        mode='markers', name=dist,
        marker=dict(color=COLORS[dist],
                    size=sub['Count'].apply(lambda n: min(8+n*0.3,35)),
                    line=dict(color='white',width=1.5), opacity=0.75),
        customdata=sub[['AREA','Count','Median_Amen']].values,
        hovertemplate=(f'<b>{dist}</b><br>Area: %{{customdata[0]}}<br>'
                       'Road: %{x:.0f}ft<br>Price/Aana: Rs.%{y:.2f}Cr<br>'
                       'n=%{customdata[1]:.0f}<extra></extra>')
    ))

median_road = area_summary['Median_Road'].median()
median_ppa  = area_summary['Median_PPA'].median()
fig12.add_vline(x=median_road,line_dash='dot',line_color='rgba(0,0,0,0.2)',line_width=1.5)
fig12.add_hline(y=median_ppa, line_dash='dot',line_color='rgba(0,0,0,0.2)',line_width=1.5)

for x, y, text, color in [
    (area_summary['Median_Road'].min()+1, median_ppa*1.08, '⚠️ Narrow + Expensive', '#E11D48'),
    (median_road*1.1,                     median_ppa*1.08, '💎 Wide + Expensive',   '#7C3AED'),
    (area_summary['Median_Road'].min()+1, median_ppa*0.90, '🟢 Hidden Gems',        '#059669'),
    (median_road*1.1,                     median_ppa*0.90, '🏆 Best Value',         '#2563EB'),
]:
    fig12.add_annotation(x=x,y=y,text=text,showarrow=False,
        font=dict(size=9,color=color,family='DM Sans'),
        bgcolor='rgba(255,255,255,0.85)',
        bordercolor=color,borderwidth=1,align='center')

fig12.update_layout(base_layout(
    xaxis=dict(title='Median Road Width (Feet)',gridcolor='#F1F5F9'),
    yaxis=dict(title='Median Price per Aana (Crore NPR)',gridcolor='#F1F5F9'),
    legend=dict(x=0.01,y=0.99,bgcolor='rgba(255,255,255,0.92)',
                bordercolor='#E2E8F0',borderwidth=1,font_size=10)
))

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: KPIs
# ─────────────────────────────────────────────────────────────────────────────
total       = len(df)
median_p    = df['PRICE_CR'].median()
afford_pct  = len(df[df['PRICE_CR']<2])/total*100
parking_pct = df['HAS_PARKING'].mean()*100
post_eq     = len(df[df['BUILT_YEAR_BS']>=2072])
pre_eq      = len(df[(df['BUILT_YEAR_BS']>=2062)&(df['BUILT_YEAR_BS']<2072)])
recovery    = (post_eq-pre_eq)/pre_eq*100 if pre_eq>0 else 0

luxury_med   = df[df['PRICE_CR']>5]['PRICE_CR'].median()
afford_med   = df[df['PRICE_CR']<2]['PRICE_CR'].median()
luxury_gap   = ((luxury_med - afford_med) / afford_med) * 100 if afford_med > 0 else 0

kpis = {
    'total':            f'{total:,}',
    'median_price':     f'Rs.{median_p:.2f} Cr',
    'median_price_sub': f'Median house price · Nepal',
    'afford_rate':      f'{afford_pct:.1f}%',
    'afford_sub':       f'Below Rs.2Cr · SDG 11 target is 20%',
    'luxury_gap':       f'+{luxury_gap:.0f}%',
    'luxury_gap_sub':   f'Luxury vs Affordable median price gap',
    'post_quake':       f'+{recovery:.0f}%',
    'post_quake_sub':   f'Construction growth post 2072 B.S earthquake',
}

print("\nKPIs:")
for k,v in kpis.items(): print(f"  {k}: {v}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5: SAVE
# ─────────────────────────────────────────────────────────────────────────────
charts_json = {f'fig{i}': eval(f'fig{i}').to_json() for i in range(1,13)}
output = {'charts': charts_json, 'kpis': kpis}

with open('chart_data.json','w') as f:
    json.dump(output, f)

print(f"\n✅ chart_data.json saved — {total:,} rows · 12 charts · 4 KPIs")
