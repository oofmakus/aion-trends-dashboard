import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import plotly.express as px
import time
import random

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="AION Chonburi War Room", page_icon="⚡", layout="wide")

# --- CSS ปรับแต่งให้สวยงาม ---
st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center;}
    h1 {color: #1E88E5;}
</style>
""", unsafe_allow_html=True)

# --- ฟังก์ชันดึงข้อมูล (Cache 1 ชั่วโมง) ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_trends_data(keywords, timeframe, geo):
    pytrends = TrendReq(hl='th-TH', tz=420, retries=2, backoff_factor=0.5, timeout=(10,25))
    result = {"graph": None, "related": None, "error": None, "average": {}}
    
    try:
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        
        # 1. กราฟ
        data = pytrends.interest_over_time()
        if not data.empty:
            data = data.drop(labels=['isPartial'], axis=1, errors='ignore')
            result["graph"] = data
            # คำนวณค่าเฉลี่ยความสนใจ
            for kw in keywords:
                if kw in data.columns:
                    result["average"][kw] = round(data[kw].mean(), 1)
            
        # 2. Insight
        if not ("now" in timeframe and "H" in timeframe):
            time.sleep(random.uniform(1, 2))
            related = pytrends.related_queries()
            result["related"] = related
            
    except Exception as e:
        result["error"] = str(e)
        
    return result

# --- Config & Presets (ปรับตามยอดขายจริงของคุณ) ---
provinces = {
    "ชลบุรี (Chonburi Focus)": "TH-20",
    "ทั้งประเทศไทย": "TH",
    "ระยอง (Rayong)": "TH-21",
    "กรุงเทพฯ": "TH-10"
}

timeframe_options = {
    "1 วันที่ผ่านมา (Monitor รายวัน)": "now 1-d",
    "7 วันที่ผ่านมา (ดูเทรนด์สัปดาห์)": "now 7-d",
    "30 วันที่ผ่านมา (วิเคราะห์ภาพรวม)": "today 1-m",
    "90 วันที่ผ่านมา (รายไตรมาส)": "today 3-m"
}

# จัดกลุ่มตามรุ่นรถที่คุณขายจริง
presets = {
    "1. City Car Battle (AION UT)": ["AION UT", "NETA V", "BYD Dolphin", "ORA Good Cat"],
    "2. Compact SUV Battle (AION V)": ["AION V", "BYD Atto 3", "MG ZS EV", "Omoda C5"],
    "3. Premium SUV (HYPTEC HT)": ["HYPTEC HT", "Deepal S07", "Tesla Model Y", "XPENG G6"],
    "4. เช็คโปรโมชั่น/ราคา (Buying Intent)": ["ราคา AION", "โปรโมชั่น AION", "AION ตารางผ่อน", "ส่วนลด AION"],
    "5. เช็คปัญหา (Objection Handling)": ["ปัญหา AION", "AION ดีไหม", "ศูนย์บริการ AION", "อะไหล่ AION"]
}

# --- Sidebar ---
st.sidebar.image("https://img.icons8.com/color/96/electric-vehicle.png", width=50)
st.sidebar.title("⚡ AION Monitor")
st.sidebar.caption("Support Data for Sales Team")

selected_preset = st.sidebar.selectbox("🎯 เลือกสมรภูมิ (Segment):", list(presets.keys()))
kw_list = presets[selected_preset]

# Option เสริม: ให้ผู้ใช้พิมพ์เพิ่มเองได้
add_on = st.sidebar.text_input("➕ เพิ่มคำค้นหาคู่แข่ง (ถ้ามี):", "")
if add_on:
    kw_list.append(add_on)

selected_province_name = st.sidebar.selectbox("📍 พื้นที่:", list(provinces.keys()))
geo_code = provinces[selected_province_name]

selected_time_name = st.sidebar.selectbox("⏳ ช่วงเวลา:", list(timeframe_options.keys()))
timeframe_code = timeframe_options[selected_time_name]

run_btn = st.sidebar.button('🚀 ประมวลผลข้อมูล', type="primary")

# --- Main Content ---
st.title(f"📊 {selected_preset.split('(')[0]}")
st.markdown(f"**พื้นที่:** {selected_province_name} | **เวลา:** {selected_time_name}")

if run_btn:
    with st.spinner('🤖 AI กำลังวิเคราะห์ข้อมูลคู่แข่ง...'):
        results = get_trends_data(kw_list, timeframe_code, geo_code)
        
        if results["error"]:
            if "429" in results["error"]:
                st.warning("⚠️ Google Trends ทำงานหนักเกินไป (Rate Limit) - กรุณารอสัก 1-2 นาที")
            else:
                st.error(f"Error: {results['error']}")
        
        elif results["graph"] is not None:
            # --- 1. ส่วนสรุปตัวเลข (Metrics) ---
            avg_data = results["average"]
            if avg_data:
                st.subheader("🏆 คะแนนความนิยมเฉลี่ย (0-100)")
                cols = st.columns(len(kw_list))
                # หาค่าสูงสุดเพื่อไฮไลท์ผู้ชนะ
                winner = max(avg_data, key=avg_data.get)
                
                for i, (key, val) in enumerate(avg_data.items()):
                    with cols[i]:
                        if key == winner:
                            st.markdown(f"<div class='metric-card' style='border: 2px solid #2ecc71;'>🥇 <b>{key}</b><br><h2>{val}</h2></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='metric-card'><b>{key}</b><br><h3>{val}</h3></div>", unsafe_allow_html=True)
            
            st.markdown("---")

            # --- 2. กราฟเส้น ---
            df = results["graph"]
            fig = px.line(df, x=df.index, y=kw_list, 
                          title=f"📈 แนวโน้มการค้นหา: {', '.join(kw_list)}",
                          template="plotly_white",
                          labels={'value': 'Search Volume', 'date': 'Date', 'variable': 'Car Model'})
            # ปรับเส้นให้หนาขึ้น
            fig.update_traces(line=dict(width=3))
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("ไม่พบข้อมูลกราฟในช่วงเวลานี้")

        # --- 3. Insight เจาะลึก ---
        st.markdown("---")
        st.subheader("🔍 เจาะลึกพฤติกรรมลูกค้า (Related Queries)")
        
        if results["related"]:
            related = results["related"]
            cols = st.columns(len(kw_list))
            for i, kw in enumerate(kw_list):
                with cols[i]:
                    st.info(f"เกี่ยวกับ: {kw}")
                    if kw in related and related[kw]:
                        rising = related[kw]['rising']
                        if rising is not None:
                            st.dataframe(rising.head(5)[['query', 'value']], hide_index=True)
                        else:
                            st.caption("- ไม่มีเทรนด์พุ่งแรง -")
                    else:
                        st.caption("- ไม่มีข้อมูล -")
        else:
             st.info("💡 หมายเหตุ: Google ไม่แสดง Insight สำหรับคำค้นหาที่มีปริมาณน้อย หรือช่วงเวลาสั้นเกินไป")
