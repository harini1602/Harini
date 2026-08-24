import pandas as pd, plotly.express as px, plotly.graph_objects as go

def risk_distribution(df): return px.histogram(df, x='risk_score', nbins=20, color='urgency', title='Risk score distribution', labels={'risk_score':'Calibrated risk score'})
def risk_by_class(df): return px.bar(df.groupby(['class_name','urgency']).size().reset_index(name='students'), x='class_name', y='students', color='urgency', title='Risk bands by class')
def shap_bar(drivers): return px.bar(pd.DataFrame(drivers), x='impact', y='label', orientation='h', title='Top model-signal drivers')
def gauge(score):
    fig=go.Figure(go.Indicator(mode='gauge+number', value=score, gauge={'axis':{'range':[0,100]}, 'bar':{'color':'#0f766e'}, 'steps':[{'range':[0,50],'color':'#dcfce7'},{'range':[50,70],'color':'#fef3c7'},{'range':[70,85],'color':'#fed7aa'},{'range':[85,100],'color':'#fecaca'}]})); fig.update_layout(height=260); return fig
