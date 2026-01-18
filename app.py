import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import plotly.express as px
import time
import random

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="AION Monitor Pro", page_icon="⚡", layout="wide")

# CSS ปรับแต่งความสวยงาม
st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px;}
    .footer {position: fixed; left: 0; bottom: 0; width: 100%; background-color: white; color: grey; text-align: center; padding: 10px; font-size: 12px; border-top: 1px solid #eee;}
    .warning-box {background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 14px;}
</style>
""", unsafe_allow_html=True)

# --- ฟังก์ชันดึงข้อมูล (Cache 1 ชม.) ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_trends_data(keywords, timeframe, geo):
    # เชื่อมต่อ Google Trends
    pytrends = TrendReq(hl='th-TH', tz=420, retries=2, backoff_factor=0.5, timeout=(10,25))
    result = {"graph": None, "related": None, "error": None, "average": {}}
    
    try:
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        
        # 1. กราฟ
        data = pytrends.interest_over_time()
        if not data.empty:
            data = data.drop(labels=['isPartial'], axis=1, errors='ignore')
            result["graph"] = data
            # คำนวณค่าเฉลี่ย
            for kw in keywords:
                if kw in data.columns:
                    result["average"][kw] = round(data[kw].mean(), 1)
            
        # 2. Insight (Related Queries)
        # ถ้า Timeframe ไม่ใช่รายชั่วโมง ให้ดึงข้อมูลที่เกี่ยวข้องมาด้วย
        if not ("now" in timeframe and "H" in timeframe):
            time.sleep(random.uniform(1, 2)) # Delay นิดนึง
            related = pytrends.related_queries()
            result["related"] = related
            
    except Exception as e:
        result["error"] = str(e)
        
    return result

# --- ฟังก์ชันดึง Daily Trends (เทรนด์ฮิตประจำวัน) ---
@st.cache_data(ttl=3600)
def get_daily_trends():
    try:
        pytrends = TrendReq(hl='th-TH', tz=420)
        # ดึง Trending Searches ของประเทศไทย
        trending = pytrends.trending_searches(pn='thailand')
        return trending.head(10) # เอาแค่ 10 อันดับแรก
    except:
        return None

# --- Config: รายชื่อจังหวัด (หัวเมืองใหญ่) ---
provinces = {
    "ชลบุรี (Chonburi Focus)": "TH-20",
    "กรุงเทพฯ (Bangkok)": "TH-10",
    "ทั้งประเทศไทย": "TH",
    "ระยอง (Rayong)": "TH-21",
    "สมุทรปราการ": "TH-11",
    "เชียงใหม่ (Chiang Mai)": "TH-50",
    "ขอนแก่น (Khon Kaen)": "TH-40",
    "นครราชสีมา (Korat)": "TH-30",
    "ภูเก็ต (Phuket)": "TH-83",
    "สงขลา (Songkhla/Hatyai)": "TH-90",
    "อุดรธานี (Udon Thani)": "TH-41",
    "อุบลราชธานี": "TH-34"
}

# Config: ช่วงเวลา
timeframe_options = {
    "1 วันที่ผ่านมา (Monitor รายวัน)": "now 1-d",
    "7 วันที่ผ่านมา (ดูเทรนด์สัปดาห์)": "now 7-d",
    "30 วันที่ผ่านมา (วิเคราะห์ภาพรวม)": "today 1-m",
    "90 วันที่ผ่านมา (รายไตรมาส)": "today 3-m"
}

# Config: Presets
presets = {
    "1. City Car Battle (AION UT)": ["AION UT", "NETA V", "BYD Dolphin", "ORA Good Cat"],
    "2. Compact SUV Battle (AION V)": ["AION V", "BYD Atto 3", "MG ZS EV", "Omoda C5"],
    "3. Premium SUV (HYPTEC HT)": ["HYPTEC HT", "Deepal S07", "Tesla Model Y", "XPENG G6"],
    "4. 🔥 เทรนด์ตลาด EV (ภาพรวม)": ["รถไฟฟ้า", "รถ EV", "ราคารถไฟฟ้า", "Motor Expo"],
    "5. เช็คโปรโมชั่น/ราคา (Buying Intent)": ["ราคา AION", "โปรโมชั่น AION", "AION ตารางผ่อน", "ส่วนลด AION"],
    "6. เช็คปัญหา (Objection Handling)": ["ปัญหา AION", "AION ดีไหม", "ศูนย์บริการ AION", "อะไหล่ AION"]
}

# --- Sidebar ---
st.sidebar.image("https://img.icons8.com/color/96/electric-vehicle.png", width=50)
st.sidebar.title("⚡ AION Monitor")
st.sidebar.caption("Support Data for Sales Team")

# ส่วนเลือกข้อมูล
selected_preset = st.sidebar.selectbox("🎯 เลือกสมรภูมิ (Segment):", list(presets.keys()))
kw_list = presets[selected_preset]

# เพิ่มคำค้นหาเอง
add_on = st.sidebar.text_input("➕ เพิ่มคำค้นหาคู่แข่ง (ถ้ามี):", "")
if add_on:
    kw_list.append(add_on)

selected_province_name = st.sidebar.selectbox("📍 พื้นที่:", list(provinces.keys()))
geo_code = provinces[selected_province_name]

selected_time_name = st.sidebar.selectbox("⏳ ช่วงเวลา:", list(timeframe_options.keys()))
timeframe_code = timeframe_options[selected_time_name]

# คำเตือน
st.sidebar.markdown("""
<div class='warning-box'>
⚠️ <b>คำแนะนำ:</b> อย่ากดปุ่มรัวเกินไป (ควรเว้นระยะ 10-20 วินาที) เพื่อป้องกัน Google บล็อกการค้นหา
</div>
""", unsafe_allow_html=True)

run_btn = st.sidebar.button('🚀 ประมวลผลข้อมูล', type="primary")

st.sidebar.markdown("---")
# ปุ่มดูเทรนด์ฮิตประจำวัน
if st.sidebar.button("🔥 เช็คเทรนด์ฮิตวันนี้ (Thailand Daily)"):
    with st.spinner("กำลังดึงข้อมูล Top Searches..."):
        daily_trends = get_daily_trends()
        st.sidebar.markdown("### 🇹🇭 10 อันดับคำค้นวันนี้")
        if daily_trends is not None:
            st.sidebar.dataframe(daily_trends, hide_index=True, use_container_width=True)
        else:
            st.sidebar.warning("ไม่สามารถดึงข้อมูลได้ขณะนี้")

# --- Main Content ---
st.title(f"📊 {selected_preset.split('(')[0]}")
st.markdown(f"**พื้นที่:** {selected_province_name} | **เวลา:** {selected_time_name}")

if run_btn:
    with st.spinner('🤖 AI กำลังวิเคราะห์ข้อมูลคู่แข่ง...'):
        results = get_trends_data(kw_list, timeframe_code, geo_code)
        
        if results["error"]:
            if "429" in results["error"]:
                st.warning("⚠️ Google Trends ทำงานหนักเกินไป (Rate Limit) - กรุณารอสัก 1 นาทีแล้วลองใหม่")
            else:
                st.error(f"Error: {results['error']}")
        
        elif results["graph"] is not None:
            # --- 1. ส่วนสรุปตัวเลข (Metrics) ---
            avg_data = results["average"]
            if avg_data:
                st.subheader("🏆 คะแนนความนิยมเฉลี่ย (0-100)")
                cols = st.columns(len(kw_list))
                # หาค่าสูงสุด
                winner = max(avg_data, key=avg_data.get) if avg_data else None
                
                for i, (key, val) in enumerate(avg_data.items()):
                    with cols[i]:
                        if key == winner:
                            st.markdown(f"<div class='metric-card' style='border: 2px solid #2ecc71; background-color: #e8f8f5;'>🥇 <b>{key}</b><br><h2 style='color:#27ae60'>{val}</h2></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='metric-card'><b>{key}</b><br><h3>{val}</h3></div>", unsafe_allow_html=True)
            
            st.markdown("---")

            # --- 2. กราฟเส้น ---
            df = results["graph"]
            fig = px.line(df, x=df.index, y=kw_list, 
                          title=f"📈 แนวโน้มการค้นหา: {', '.join(kw_list)}",
                          template="plotly_white",
                          labels={'value': 'Search Volume', 'date': 'Date', 'variable': 'Model'})
            fig.update_traces(line=dict(width=3))
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("ดูตารางข้อมูลดิบ"):
                st.dataframe(df.sort_index(ascending=False))

            # --- 3. Insight เจาะลึก ---
            st.markdown("---")
            st.subheader("🔍 เจาะลึกพฤติกรรมลูกค้า (Related Queries)")
            
            if results["related"]:
                related = results["related"]
                cols = st.columns(len(kw_list))
                for i, kw in enumerate(kw_list):
                    with cols[i]:
                        st.info(f"คำค้นหาที่มาคู่กับ: **{kw}**")
                        if kw in related and related[kw]:
                            rising = related[kw]['rising']
                            top = related[kw]['top']
                            
                            tab1, tab2 = st.tabs(["🔥 มาแรง (Rising)", "⭐ ยอดนิยม (Top)"])
                            with tab1:
                                if rising is not None:
                                    st.dataframe(rising.head(5)[['query', 'value']], hide_index=True)
                                else:
                                    st.caption("- ไม่มีเทรนด์พุ่งแรง -")
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
            st.warning("ไม่พบข้อมูลกราฟในช่วงเวลานี้ (ลองเปลี่ยนพื้นที่ หรือขยายช่วงเวลา)")

# --- Footer Credits ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: grey;'>Developed by oofmakus</div>", unsafe_allow_html=True)
