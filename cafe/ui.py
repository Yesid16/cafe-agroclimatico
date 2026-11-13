"""Presentación del dashboard. No altera datos, credenciales ni inferencia."""
from html import escape
import streamlit as st

LABOR_LABELS = {'deshierba':'Deshierba','fertilizacion':'Fertilización',
                'aspersion_roya':'Aspersión para roya','recoleccion':'Recolección','poda_zoca':'Poda / zoca'}


def apply_theme(root):
    css=(root/'assets/dashboard.css').read_text(encoding='utf-8')
    st.markdown(f'<style>{css}</style>',unsafe_allow_html=True)


def summary_card(label,value,note='',risk=''):
    st.markdown(
        f'<div class="agro-card"><div class="agro-card-label">{escape(str(label))}</div>'
        f'<div class="agro-card-value" data-risk="{escape(str(risk),quote=True)}">{escape(str(value))}</div>'
        f'<div class="agro-card-note">{escape(str(note))}</div></div>',unsafe_allow_html=True)


def show_chart(fig):
    fig.update_layout(template='plotly_white',paper_bgcolor='#ffffff',plot_bgcolor='#ffffff',
        font=dict(family='Segoe UI, Arial, sans-serif',color='#425b4d',size=12),
        colorway=['#397d60','#8baea0','#c6a667','#6e9bad','#b86b57'],
        hoverlabel=dict(bgcolor='white',font_color='#243d32'),
        legend=dict(bgcolor='rgba(255,255,255,0)',font=dict(size=11)))
    fig.update_xaxes(gridcolor='#eef2ed',zeroline=False)
    fig.update_yaxes(gridcolor='#eef2ed',zeroline=False)
    st.plotly_chart(fig,width='stretch',theme=None,config={'displaylogo':False})
