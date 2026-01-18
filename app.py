import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import plotly.express as px

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="AION Chonburi Trends", page_icon="🚗", layout="wide")

# Header
st.title("🚗 AION vs EV Competitors Monitor")
st.markdown("Dashboard สำหรับติดตามความสนใจลูกค้าในพื้นที่ **ชลบุรี** และ **ประเทศไทย**")

# เชื่อมต่อ Google Trends
# retries=2 และ backoff_factor=0.1 ช่วยลดโอกาส error เวลาขอข้อมูลถี่ๆ
pytrends = TrendReq(hl='th-TH', tz=420, retries=2, backoff_factor=0.1)

# Sidebar
st.sidebar.header("⚙️ ตั้งค่าการวิเคราะห์")
# Preset สำหรับ AION
preset = st.sidebar.radio("เลือกกลุ่มเปรียบเทียบ:", 
                          ["กำหนดเอง", 
                           "AION vs BYD vs NETA", 
                           "AION Y Plus vs Atto 3", 
                           "AION ES vs Dolphin"])

if preset == "กำหนดเอง":
    user_kw = st.sidebar.text_input("ใส่คำค้นหา (คั่นด้วย ,)", "AION, BYD")
    kw_list = [x.strip() for x in user_kw.split(',')]
elif preset == "AION vs BYD vs NETA":
    kw_list = ["AION", "BYD", "NETA", "MG"]
elif preset == "AION Y Plus vs Atto 3":
    kw_list = ["AION Y Plus", "BYD Atto 3", "MG ZS EV"]
else:
    kw_list = ["AION ES", "BYD Dolphin", "ORA Good Cat"]

timeframe = st.sidebar.selectbox("ช่วงเวลา", 
                                 ["today 12-m", "today 1-m", "today 3-m", "now 7-d"], 
                                 index=1) # Default เป็น 1 เดือน

# Main Content
if st.sidebar.button('🚀 รันข้อมูล'):
    with st.spinner('กำลังดึงข้อมูลจาก Google...'):
        try:
            # 1. เทรนด์ในชลบุรี (TH-20)
            st.subheader(f"📍 ความสนใจในพื้นที่ 'ชลบุรี' (Chonburi Focus)")
            pytrends.build_payload(kw_list, cat=0, timeframe=timeframe, geo='TH-20')
            data_chonburi = pytrends.interest_over_time()
            
            if not data_chonburi.empty:
                data_chonburi = data_chonburi.drop(labels=['isPartial'], axis=1)
                fig = px.line(data_chonburi, x=data_chonburi.index, y=kw_list, 
                              title=f"แนวโน้มการค้นหาในชลบุรี ({timeframe})")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ ข้อมูลในชลบุรีน้อยเกินไปในช่วงเวลานี้ (ลองเปลี่ยนช่วงเวลา หรือดูภาพรวมประเทศ)")

            # 2. เทรนด์ทั่วประเทศ (Thailand Overview)
            st.markdown("---")
            st.subheader(f"🇹🇭 ภาพรวมทั้งประเทศไทย (Thailand Overview)")
            pytrends.build_payload(kw_list, cat=0, timeframe=timeframe, geo='TH')
            data_th = pytrends.interest_over_time()
            
            if not data_th.empty:
                data_th = data_th.drop(labels=['isPartial'], axis=1)
                fig2 = px.line(data_th, x=data_th.index, y=kw_list, 
                               title=f"แนวโน้มการค้นหาทั่วประเทศ ({timeframe})")
                st.plotly_chart(fig2, use_container_width=True)

            # 3. เจาะลึก Related Queries (หา Insight)
            st.markdown("---")
            st.subheader("🔍 คำที่คนค้นหาบ่อยคู่กับแบรนด์ (Related Queries)")
            
            related = pytrends.related_queries()
            cols = st.columns(len(kw_list))
            
            for i, kw in enumerate(kw_list):
                with cols[i]:
                    st.info(f"เกี่ยวกับ: **{kw}**")
                    if related.get(kw):
                        rising = related[kw]['rising']
                        if rising is not None:
                            st.dataframe(rising.head(5), hide_index=True)
                        else:
                            st.write("- ไม่พบเทรนด์พุ่งแรง -")
                    else:
                        st.write("- ไม่มีข้อมูล -")

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
            st.write("คำแนะนำ: ลองลดจำนวนคำค้นหา หรือรอสักพักแล้วกดใหม่ (Google อาจบล็อกชั่วคราวถ้าขอบ่อยเกินไป)")