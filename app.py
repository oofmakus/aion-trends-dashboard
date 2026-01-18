import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import plotly.express as px
import time
import random

# --- 1. ตั้งค่าหน้าเว็บและ Session State ---
st.set_page_config(page_title="AION Monitor Pro", page_icon="⚡", layout="wide")

# สร้างตัวแปรจับเวลาในระบบ ถ้ายังไม่มี
if 'last_run_time' not in st.session_state:
    st.session_state.last_run_time = 0

# --- 2. CSS & UI/UX Design (แต่งสวย) ---
st.markdown("""
<style>
    /* เปลี่ยน Font และ Theme หลัก */
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;600&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Prompt', sans-serif;
    }
    
    /* แต่งกล่อง Metric (คะแนน) */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px rgba(0,0,0,0.1);
    }
    
    /* แต่งกล่องผู้ชนะ (สีเขียว) */
    .metric-winner {
        background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%);
        border: none;
        color: #1b5e20;
    }

    /* แต่ง Footer */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f8f9fa;
        color: #6c757d;
        text-align: center;
        padding: 10px;
        font-size: 12px;
        border-top: 1px solid #dee2e6;
        z-index: 999;
    }
    
    /* ปรับแต่งหัวข้อ */
    h1, h2, h3 {
        color: #0D47A1;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ฟังก์ชันดึงข้อมูล (Backend) ---

@st.cache_data(ttl=3600, show_spinner=False)
def get_trends_data(keywords, timeframe, geo):
    # เชื่อมต่อ Google Trends
    pytrends = TrendReq(hl='th-TH', tz=420, retries=3, backoff_factor=0.5, timeout=(10,25))
    result = {"graph": None, "related": None, "error": None, "average": {}}
    
    try:
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        
        # 1. กราฟ
        data = pytrends.interest_over_time()
        if not data.empty:
            data = data.drop(labels=['isPartial'], axis=1, errors='ignore')
            result["graph"] = data
            for kw in keywords:
                if kw in data.columns:
                    result["average"][kw] = round(data[kw].mean(), 1)
            
        # 2. Insight (Related Queries)
        if not ("now" in timeframe and "H" in timeframe):
            time.sleep(random.uniform(1, 1.5)) 
            related = pytrends.related_queries()
            result["related"] = related
            
    except Exception as e:
        result["error"] = str(e)
        
    return result

@st.cache_data(ttl=1800) # Cache 30 นาที
def get_realtime_trends():
    try:
        pytrends = TrendReq(hl='th-TH', tz=420)
        # ใช้ Realtime Trends แทน Daily เพราะเสถียรกว่าในไทย
        df = pytrends.realtime_trending_searches(pn='TH')
        return df.head(10)
    except:
        return None

# --- 4. Config & Presets ---
provinces = {
    "ชลบุรี (Chonburi Focus)": "TH-20",
    "กรุงเทพฯ (Bangkok)": "TH-10",
    "ทั้งประเทศไทย": "TH",
    "ระยอง (Rayong)": "TH-21",
    "เชียงใหม่ (Chiang Mai)": "TH-50",
    "ขอนแก่น (Khon Kaen)": "TH-40",
    "นครราชสีมา (Korat)": "TH-30",
    "ภูเก็ต (Phuket)": "TH-83",
    "สงขลา (Hatyai)": "TH-90"
}

timeframe_options = {
    "1 วันที่ผ่านมา (Monitor รายวัน)": "now 1-d",
    "7 วันที่ผ่านมา (ดูเทรนด์สัปดาห์)": "now 7-d",
    "30 วันที่ผ่านมา (วิเคราะห์ภาพรวม)": "today 1-m",
    "90 วันที่ผ่านมา (รายไตรมาส)": "today 3-m"
}

presets = {
    "1. City Car Battle (AION UT)": ["AION UT", "NETA V", "BYD Dolphin", "ORA Good Cat"],
    "2. Compact SUV Battle (AION V)": ["AION V", "BYD Atto 3", "MG ZS EV", "Omoda C5"],
    "3. Premium SUV (HYPTEC HT)": ["HYPTEC HT", "Deepal S07", "Tesla Model Y", "XPENG G6"],
    "4. 🔥 เทรนด์ตลาด EV (ภาพรวม)": ["รถไฟฟ้า", "รถ EV", "ราคารถไฟฟ้า", "Motor Expo"],
    "5. เช็คโปรโมชั่น/ราคา (Buying Intent)": ["ราคา AION", "โปรโมชั่น AION", "AION ตารางผ่อน", "ส่วนลด AION"],
    "6. เช็คปัญหา (Objection Handling)": ["ปัญหา AION", "AION ดีไหม", "ศูนย์บริการ AION", "อะไหล่ AION"]
}

# --- 5. Sidebar Layout ---
# เปลี่ยน URL รูปให้เสถียรขึ้น
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3209/3209990.png", width=70)
st.sidebar.markdown("## ⚡ AION War Room")
st.sidebar.caption("Data GOOGLE TREND Intelligence for Sales Team By OOfmakus")

selected_preset = st.sidebar.selectbox("🎯 เลือกสมรภูมิ (Segment):", list(presets.keys()))
kw_list = presets[selected_preset]

add_on = st.sidebar.text_input("➕ เพิ่มคำค้นหาคู่แข่ง (ถ้ามี):", "")
if add_on:
    kw_list.append(add_on)

selected_province_name = st.sidebar.selectbox("📍 พื้นที่:", list(provinces.keys()))
geo_code = provinces[selected_province_name]

selected_time_name = st.sidebar.selectbox("⏳ ช่วงเวลา:", list(timeframe_options.keys()))
timeframe_code = timeframe_options[selected_time_name]

st.sidebar.markdown("---")

# --- 6. ปุ่ม Run พร้อมระบบ Cooldown (สำคัญ!) ---
# เช็คเวลาก่อน
current_time = time.time()
time_diff = current_time - st.session_state.last_run_time
cooldown_seconds = 15 # บังคับรอ 15 วินาที

if st.sidebar.button('🚀 ประมวลผลข้อมูล', type="primary", use_container_width=True):
    if time_diff < cooldown_seconds:
        # ถ้ารีบกดเกินไป
        wait_time = int(cooldown_seconds - time_diff)
        st.sidebar.error(f"⏳ ใจเย็นวัยรุ่น! กรุณารออีก {wait_time} วินาที")
    else:
        # ถ้าเวลาผ่านไปนานพอแล้ว ให้ทำงานได้
        st.session_state.last_run_time = current_time # อัปเดตเวลาล่าสุด
        st.session_state.run_triggered = True # ส่งสัญญาณให้ Main Content ทำงาน

# ปุ่มดู Daily Trends
if st.sidebar.button("🔥 เช็คเทรนด์ฮิตวันนี้ (Realtime)"):
    with st.spinner("กำลังดึงข้อมูล Realtime..."):
        daily_trends = get_realtime_trends()
        st.sidebar.markdown("### 🇹🇭 คำค้นหามาแรง (Realtime)")
        if daily_trends is not None and not daily_trends.empty:
            # แต่งตารางให้สวย
            st.sidebar.dataframe(daily_trends.head(10), hide_index=True, use_container_width=True)
        else:
            st.sidebar.warning("ขณะนี้ Google ไม่ส่งข้อมูล Realtime (ลองกดใหม่ในอีก 5 นาที)")

# --- 7. Main Content Area ---
st.title(f"📊 {selected_preset.split('(')[0]}")
st.markdown(f"**พื้นที่:** {selected_province_name} | **เวลา:** {selected_time_name}")

# ตรวจสอบว่ามีการกดปุ่ม Run หรือยัง
if 'run_triggered' in st.session_state and st.session_state.run_triggered:
    
    # รีเซ็ต Trigger เพื่อไม่ให้รันซ้ำเอง
    st.session_state.run_triggered = False 

    with st.spinner('🤖 AI กำลังวิเคราะห์ข้อมูลคู่แข่ง...'):
        results = get_trends_data(kw_list, timeframe_code, geo_code)
        
        if results["error"]:
            if "429" in results["error"]:
                st.error("⚠️ Google Trends ทำงานหนักเกินไป (Rate Limit) - กรุณารอสัก 1-2 นาทีแล้วค่อยกดใหม่")
            else:
                st.error(f"Error: {results['error']}")
        
        elif results["graph"] is not None:
            # --- A. ส่วนสรุปตัวเลข (Metrics Card UI) ---
            avg_data = results["average"]
            if avg_data:
                st.subheader("🏆 คะแนนความนิยมเฉลี่ย (Score 0-100)")
                cols = st.columns(len(kw_list))
                winner = max(avg_data, key=avg_data.get) if avg_data else None
                
                for i, (key, val) in enumerate(avg_data.items()):
                    with cols[i]:
                        if key == winner:
                            # การ์ดผู้ชนะ
                            st.markdown(f"""
                            <div class='metric-card metric-winner'>
                                <div style='font-size:30px;'>🥇</div>
                                <b>{key}</b><br>
                                <h1 style='margin:0; color:#1b5e20;'>{val}</h1>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # การ์ดธรรมดา
                            st.markdown(f"""
                            <div class='metric-card'>
                                <div style='height:30px;'></div>
                                <b>{key}</b><br>
                                <h2 style='margin:0; color:#555;'>{val}</h2>
                            </div>
                            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)

            # --- B. กราฟเส้น (Plotly) ---
            df = results["graph"]
            # ใช้ Template 'plotly_white' หรือ 'plotly_dark' หรือ 'ggplot2'
            fig = px.line(df, x=df.index, y=kw_list, 
                          title=f"📈 แนวโน้มการค้นหา: {', '.join(kw_list)}",
                          template="plotly_white", 
                          color_discrete_sequence=px.colors.qualitative.Bold, # สีสดชัด
                          labels={'value': 'Search Volume', 'date': 'Date', 'variable': 'Model'})
            
            fig.update_traces(line=dict(width=3), mode='lines+markers') # เส้นหนา มีจุด
            fig.update_layout(hovermode="x unified", height=450) # เวลาเอาเมาส์จ่อ จะขึ้นข้อมูลครบทุกเส้น
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("ดูตารางข้อมูลดิบ (Raw Data)"):
                st.dataframe(df.sort_index(ascending=False))

            # --- C. Insight เจาะลึก ---
            st.markdown("---")
            st.subheader("🔍 เจาะลึกพฤติกรรมลูกค้า (Insight)")
            
            if results["related"]:
                related = results["related"]
                cols = st.columns(len(kw_list))
                for i, kw in enumerate(kw_list):
                    with cols[i]:
                        st.info(f"**{kw}**")
                        if kw in related and related[kw]:
                            rising = related[kw]['rising']
                            top = related[kw]['top']
                            
                            tab1, tab2 = st.tabs(["🔥 มาแรง", "⭐ ยอดนิยม"])
                            with tab1:
                                if rising is not None:
                                    st.dataframe(rising.head(5)[['query', 'value']], hide_index=True)
                                else:
                                    st.caption("- ไม่มีข้อมูล -")
                            with tab2:
                                if top is not None:
                                    st.dataframe(top.head(5)[['query', 'value']], hide_index=True)
                                else:
                                    st.caption("- ไม่มีข้อมูล -")
                        else:
                            st.caption("- ไม่มีข้อมูล -")
            else:
                 st.info("💡 หมายเหตุ: Google ไม่แสดง Insight สำหรับคำค้นหาที่มีปริมาณน้อย หรือช่วงเวลาสั้นเกินไป")
                 
        else:
            st.warning("⚠️ ไม่พบข้อมูลกราฟในช่วงเวลานี้ (ลองเปลี่ยนพื้นที่ หรือขยายช่วงเวลา)")

# --- Footer Credits ---
st.markdown("<div class='footer'>Developed by oofmakus</div>", unsafe_allow_html=True)

