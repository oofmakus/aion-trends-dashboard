import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import plotly.express as px
import time
import random

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="AION Monitor Pro", page_icon="⚡", layout="wide")

# --- ฟังก์ชันดึงข้อมูล (หัวใจสำคัญ: ใส่ Cache ไว้ตรงนี้) ---
# ttl=3600 หมายถึง ให้จำข้อมูลไว้ 1 ชั่วโมง (3600 วินาที) ถ้าค้นคำเดิมใน 1 ชม. จะไม่ยิง Google ใหม่
@st.cache_data(ttl=3600, show_spinner=False)
def get_trends_data(keywords, timeframe, geo):
    # เชื่อมต่อ Google Trends (ลด Timeout ลงเพื่อไม่ให้หน้าจอค้างนานถ้าเน็ตหลุด)
    pytrends = TrendReq(hl='th-TH', tz=420, retries=2, backoff_factor=0.5, timeout=(10,25))
    
    result = {"graph": None, "related": None, "error": None}
    
    try:
        # สร้าง Payload
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        
        # 1. ดึงกราฟ
        data = pytrends.interest_over_time()
        if not data.empty:
            data = data.drop(labels=['isPartial'], axis=1, errors='ignore')
            result["graph"] = data
            
        # 2. ดึง Insight (ถ้า Timeframe ไม่ใช่รายชั่วโมง)
        if not ("now" in timeframe and "H" in timeframe):
            time.sleep(random.uniform(1, 2)) # พักนิดนึงก่อนดึงส่วนที่ 2
            related = pytrends.related_queries()
            result["related"] = related
            
    except Exception as e:
        result["error"] = str(e)
        
    return result

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
    "1 วันที่ผ่านมา": "now 1-d",
    "7 วันที่ผ่านมา": "now 7-d",
    "30 วันที่ผ่านมา": "today 1-m",
    "90 วันที่ผ่านมา": "today 3-m",
    "12 เดือนที่ผ่านมา": "today 12-m",
    "1 ชั่วโมงที่ผ่านมา (ไม่แนะนำ-เสี่ยงจอขาว)": "now 1-H",
    "4 ชั่วโมงที่ผ่านมา": "now 4-H"
}

presets = {
    "1. กำหนดเอง (พิมพ์ใหม่)": [],
    "2. AION vs คู่แข่งหลัก": ["AION", "BYD", "DEEPAL", "MG", "OMODA"],
    "3. เทียบรุ่นเล็ก (AION UT vs Dolphin)": ["AION UT", "BYD Dolphin", "ORA Good Cat", "MG4" ],
    "4. เทียบรุ่นใหญ่ (AION V vs Atto 3)": ["AION V", "BYD Atto 3","jaecoo 5"],
    "5. ทีม AION ชลบุรี": ["AION Service ", "AION Service", "ศูนย์ AION"],
}

# --- Sidebar ---
st.sidebar.title("⚡ AION War Room")

selected_preset = st.sidebar.selectbox("เลือกชุดคำค้นหา:", list(presets.keys()))

if selected_preset == "1. กำหนดเอง (พิมพ์ใหม่)":
    if 'custom_kw' not in st.session_state:
        st.session_state.custom_kw = "AION, BYD"
    user_kw = st.sidebar.text_input("พิมพ์คำค้นหา (คั่น ,)", st.session_state.custom_kw)
    st.session_state.custom_kw = user_kw 
    kw_list = [x.strip() for x in user_kw.split(',')]
else:
    kw_list = presets[selected_preset]
    st.sidebar.info(f"คำค้นหา: {', '.join(kw_list)}")

selected_province_name = st.sidebar.selectbox("เลือกพื้นที่:", list(provinces.keys()))
geo_code = provinces[selected_province_name]

selected_time_name = st.sidebar.selectbox("ช่วงเวลา:", list(timeframe_options.keys()))
timeframe_code = timeframe_options[selected_time_name]

run_btn = st.sidebar.button('🚀 วิเคราะห์ข้อมูล', type="primary")

# --- Main Content ---
st.title(f"📈 Trends: {selected_province_name}")
st.caption(f"ช่วงเวลา: {selected_time_name}")

if run_btn:
    with st.spinner('กำลังดึงข้อมูล (อาจใช้เวลา 5-10 วินาที)...'):
        # เรียกใช้ฟังก์ชันที่มี Cache (ถ้าเคยค้นแล้ว มันจะคืนค่าทันที ไม่ต้องรอนาน)
        results = get_trends_data(kw_list, timeframe_code, geo_code)
        
        # ตรวจสอบ Error
        if results["error"]:
            if "429" in results["error"]:
                st.warning("⚠️ ระบบ Google กำลังยุ่ง (Too Many Requests) - ข้อมูลอาจจะมาช้าหรือมาไม่ครบ กรุณารอสัก 1 นาทีแล้วกดใหม่")
            else:
                st.error(f"เกิดข้อผิดพลาด: {results['error']}")
        
        # แสดงกราฟ
        if results["graph"] is not None:
            df = results["graph"]
            fig = px.line(df, x=df.index, y=kw_list, 
                          title=f"Trend ใน {selected_province_name}",
                          labels={'value': 'ความสนใจ', 'date': 'เวลา', 'variable': 'คำค้นหา'})
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("ดูข้อมูลดิบ (Table)"):
                st.dataframe(df.sort_index(ascending=False))
        elif not results["error"]:
            st.warning("ไม่พบข้อมูลกราฟ (ปริมาณการค้นหาน้อยเกินไป)")

        # แสดง Insight
        st.markdown("---")
        st.subheader("🔍 คำค้นหาที่เกี่ยวข้อง")
        
        if results["related"]:
            related = results["related"]
            cols = st.columns(len(kw_list))
            for i, kw in enumerate(kw_list):
                with cols[i]:
                    st.markdown(f"**{kw}**")
                    if kw in related and related[kw]:
                        top = related[kw]['top']
                        rising = related[kw]['rising']
                        
                        tab1, tab2 = st.tabs(["มาแรง 🔥", "ยอดนิยม ⭐"])
                        with tab1:
                            if rising is not None:
                                st.dataframe(rising.head(5), hide_index=True)
                            else:
                                st.caption("ไม่มีข้อมูล")
                        with tab2:
                            if top is not None:
                                st.dataframe(top.head(5), hide_index=True)
                            else:
                                st.caption("ไม่มีข้อมูล")
                    else:
                        st.caption("-")
        else:
            if "now" in timeframe_code and "H" in timeframe_code:
                st.info("💡 โหมดรายชั่วโมง Google จะไม่แสดง Insight คำที่เกี่ยวข้อง")
            elif not results["error"]:
                 st.info("Google ไม่ส่งข้อมูล Insight กลับมา (อาจเพราะค้นหาเจาะจงเกินไป)")
