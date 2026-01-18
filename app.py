import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import plotly.express as px
import time # เพิ่มตัวนี้มาเพื่อถ่วงเวลา
import random

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="AION Monitor Pro", page_icon="⚡", layout="wide")

# เชื่อมต่อ Google Trends
# retries และ backoff_factor ช่วยลดโอกาส error (เพิ่มค่า retries เป็น 3)
pytrends = TrendReq(hl='th-TH', tz=420, retries=3, backoff_factor=0.2)

# --- ส่วนตั้งค่า (Config) ---
provinces = {
    "ทั้งประเทศไทย": "TH",
    "ชลบุรี (Chonburi)": "TH-20",
    "กรุงเทพฯ (Bangkok)": "TH-10",
    "ระยอง (Rayong)": "TH-21",
    "สมุทรปราการ": "TH-11",
    "เชียงใหม่": "TH-50",
    "ภูเก็ต": "TH-83",
    "ขอนแก่น": "TH-40",
    "นครราชสีมา": "TH-30"
}

timeframe_options = {
    "1 ชั่วโมงที่ผ่านมา (ละเอียดสุด)": "now 1-H",
    "4 ชั่วโมงที่ผ่านมา": "now 4-H",
    "1 วันที่ผ่านมา": "now 1-d",
    "7 วันที่ผ่านมา": "now 7-d",
    "30 วันที่ผ่านมา": "today 1-m",
    "90 วันที่ผ่านมา": "today 3-m",
    "12 เดือนที่ผ่านมา": "today 12-m"
}

presets = {
    "1. กำหนดเอง (พิมพ์ใหม่)": [],
    "2. AION vs คู่แข่งหลัก": ["AION", "BYD", "DEEPAL", "MG", "OMODA"],
    "3. เทียบรุ่นเล็ก (UT vs Dolphin)": ["AION UT", "BYD Dolphin", "ORA Good Cat", "MG4" ],
    "4. เทียบรุ่นใหญ่ (AION V vs Atto 3)": ["AION V", "BYD Atto 3","jaecoo 5"],
}

# --- ส่วนแสดงผล Sidebar ---
st.sidebar.title("⚡ AION War Room")

selected_preset = st.sidebar.selectbox("เลือกชุดคำค้นหา (Saved Lists):", list(presets.keys()))

if selected_preset == "1. กำหนดเอง (พิมพ์ใหม่)":
    if 'custom_kw' not in st.session_state:
        st.session_state.custom_kw = "AION, BYD"
    user_kw = st.sidebar.text_input("พิมพ์คำค้นหา (คั่นด้วย ,)", st.session_state.custom_kw)
    st.session_state.custom_kw = user_kw 
    kw_list = [x.strip() for x in user_kw.split(',')]
else:
    kw_list = presets[selected_preset]
    st.sidebar.info(f"คำค้นหา: {', '.join(kw_list)}")

selected_province_name = st.sidebar.selectbox("เลือกพื้นที่ (Location):", list(provinces.keys()))
geo_code = provinces[selected_province_name]

selected_time_name = st.sidebar.selectbox("ช่วงเวลา (Timeframe):", list(timeframe_options.keys()))
timeframe_code = timeframe_options[selected_time_name]

run_btn = st.sidebar.button('🚀 วิเคราะห์ข้อมูล', type="primary")

# --- ส่วนแสดงผลหลัก (Main) ---
st.title(f"📈 Trends Analysis: {selected_province_name}")
st.caption(f"ช่วงเวลา: {selected_time_name}")

if run_btn:
    # สร้าง Payload ครั้งเดียว
    pytrends.build_payload(kw_list, cat=0, timeframe=timeframe_code, geo=geo_code)
    
    # --- ส่วนที่ 1: กราฟ (Graph) ---
    with st.spinner('กำลังดึงกราฟ...'):
        try:
            data = pytrends.interest_over_time()
            if not data.empty:
                data = data.drop(labels=['isPartial'], axis=1)
                fig = px.line(data, x=data.index, y=kw_list, 
                              title=f"ปริมาณการค้นหาใน {selected_province_name}",
                              labels={'value': 'ความสนใจ (0-100)', 'date': 'เวลา', 'variable': 'คำค้นหา'})
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("ดูข้อมูลดิบ (Table)"):
                    st.dataframe(data.sort_index(ascending=False))
            else:
                st.warning(f"⚠️ ไม่พบข้อมูลกราฟใน '{selected_province_name}' (Volume อาจจะน้อยเกินไป)")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการดึงกราฟ: {e}")

    # --- ส่วนที่ 2: Insight (แยก Try/Except เพื่อไม่ให้พังตามกราฟ) ---
    st.markdown("---")
    st.subheader("🔍 คำค้นหาที่เกี่ยวข้อง (Insight)")
    
    # ถ่วงเวลาเล็กน้อย เพื่อป้องกัน Error 429
    time.sleep(1) 

    with st.spinner('กำลังเจาะลึก Insight...'):
        try:
            # เช็คก่อนว่าควรดึงไหม (ถ้าเวลาน้อยกว่า 1 วัน Google มักไม่ส่งค่านี้)
            if "now" in timeframe_code and ("H" in timeframe_code):
                 st.info("💡 หมายเหตุ: โหมดรายชั่วโมง Google จะไม่แสดง Insight คำค้นหา")
            else:
                related = pytrends.related_queries()
                
                if related:
                    cols = st.columns(len(kw_list))
                    for i, kw in enumerate(kw_list):
                        with cols[i]:
                            st.markdown(f"**{kw}**")
                            # เช็คว่ามีข้อมูลของ keyword นี้ไหม
                            if kw in related and related[kw]:
                                top = related[kw]['top']
                                rising = related[kw]['rising']
                                
                                tab1, tab2 = st.tabs(["มาแรง (Rising)", "ยอดนิยม (Top)"])
                                with tab1:
                                    if rising is not None:
                                        st.dataframe(rising.head(5), hide_index=True)
                                    else:
                                        st.write("-")
                                with tab2:
                                    if top is not None:
                                        st.dataframe(top.head(5), hide_index=True)
                                    else:
                                        st.write("-")
                            else:
                                st.write("- ไม่มีข้อมูล -")
                else:
                    st.warning("Google ไม่ส่งข้อมูล Insight กลับมา (อาจเพราะค้นหาเจาะจงเกินไป)")

        except Exception as e:
            # ถ้า Error 429 (Too Many Requests) จะเข้ามาตรงนี้
            if "429" in str(e):
                st.warning("⚠️ Google กำลังจำกัดการเข้าถึง (Rate Limit) เนื่องจากดึงข้อมูล 'คำที่เกี่ยวข้อง' ถี่เกินไป -> **แต่กราฟด้านบนยังดูได้ปกตินะครับ**")
                st.caption("คำแนะนำ: รอสัก 1 นาทีแล้วกดใหม่ หรือเปลี่ยนเป็นดูภาพรวมประเทศ")
            else:
                st.error(f"เกิดข้อผิดพลาดส่วน Insight: {e}")
