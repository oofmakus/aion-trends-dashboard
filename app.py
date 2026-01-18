import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import plotly.express as px
import time
import random

# --- 1. ตั้งค่าหน้าเว็บและ Session State ---
st.set_page_config(page_title="AION Monitor Pro", page_icon="⚡", layout="wide")

# สร้างตัวแปรจับเวลาในระบบ
if 'last_run_time' not in st.session_state:
    st.session_state.last_run_time = 0

# --- 2. CSS & UI/UX Design (Premium Thai Style) ---
st.markdown("""
<style>
    /* Import Font: Prompt */
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&display=swap');
    
    /* บังคับใช้ฟอนต์ Prompt ทุกส่วน */
    html, body, [class*="css"], button, input, select, textarea {
        font-family: 'Prompt', sans-serif !important;
    }
    
    /* แต่งกล่องคะแนน (Metric Card) */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #f0f0f0;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.08);
        border-color: #0575e6;
    }
    
    /* แต่งกล่องผู้ชนะ (Winner) */
    .metric-winner {
        background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
        border: 2px solid #00acc1;
        color: #006064;
    }

    /* แต่งปุ่มกด (Sidebar) */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }

    /* แต่งกล่องคำเตือน Cooldown */
    .cooldown-box {
        background-color: #ffebee;
        color: #c62828;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #ef5350;
        text-align: center;
        font-weight: 600;
        margin-bottom: 10px;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }

    /* Footer */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #ffffff;
        color: #9e9e9e;
        text-align: center;
        padding: 8px;
        font-size: 11px;
        border-top: 1px solid #eeeeee;
        z-index: 9999;
    }
    
    /* Headers */
    h1, h2, h3 { color: #1565C0; }
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
            
        # 2. Insight
        if not ("now" in timeframe and "H" in timeframe):
            time.sleep(random.uniform(1, 1.5)) 
            related = pytrends.related_queries()
            result["related"] = related
            
    except Exception as e:
        result["error"] = str(e)
        
    return result

# ฟังก์ชันดึงเทรนด์ (แก้ปัญหา Realtime ไม่ขึ้น)
@st.cache_data(ttl=1800) 
def get_trends_ranking():
    pytrends = TrendReq(hl='th-TH', tz=420)
    try:
        # ลองดึง Realtime ก่อน
        df = pytrends.realtime_trending_searches(pn='TH')
        return df.head(10), "🔥 Realtime (ล่าสุด)"
    except:
        try:
            # ถ้า Realtime พัง ให้ดึง Daily แทน
            df = pytrends.trending_searches(pn='thailand')
            return df.head(10), "📅 Daily (ประจำวัน)"
        except:
            return None, "Error"

# --- 4. Config & Presets ---
provinces = {
    "ทั้งประเทศไทย (TH)": "TH",
    "ชลบุรี (Chonburi Focus)": "TH-20",
    "กรุงเทพฯ (Bangkok)": "TH-10",
    "ระยอง (Rayong)": "TH-21",
    "ลำปาง (Lampang)": "TH-52",  
    "เชียงใหม่ (Chiang Mai)": "TH-50",
    "ขอนแก่น(Khon Kaen)": "TH-40",
    "โคราช (Korat)": "TH-30",
    "ภูเก็ต (Phuket)": "TH-83",
    "สงขลา (Songkhla)": "TH-90"
}

timeframe_options = {
    "30 วันที่ผ่านมา (วิเคราะห์ภาพรวม)": "today 1-m",
    "1 วันที่ผ่านมา (Monitor รายวัน)": "now 1-d",
    "7 วันที่ผ่านมา (ดูเทรนด์สัปดาห์)": "now 7-d",
    "90 วันที่ผ่านมา (รายไตรมาส)": "today 3-m"
}

presets = {
    "1. City Car Battle (AION UT)": ["AION UT", "NETA V", "BYD Dolphin", "ORA Good Cat"],
    "2. Compact SUV Battle (AION V)": ["AION V", "BYD Atto 3", "MG ZS EV", "Omoda C5"],
    "3. Premium SUV (HYPTEC HT)": ["HYPTEC HT", "Deepal S07", "Tesla Model Y", "XPENG G6"],
    "4. 🔥 เทรนด์ตลาด EV (ภาพรวม)": ["รถไฟฟ้า", "รถ EV", "ราคารถไฟฟ้า", "Motor Expo"],
    "5. เช็คโปรโมชั่น/ราคา (Buying Intent)": ["ราคา AION", "โปรโมชั่น AION", "AION ตารางผ่อน", "ส่วนลด AION"],
    "6. เช็คปัญหา (Objection Handling)": ["ปัญหา AION", "AION ดีไหม", "ศูนย์บริการ AION", "อะไหล่ AION"],
    "7. ⚔️ เปรียบเทียบแบรนด์ (Brand War)": ["AION", "BYD", "NETA", "MG", "TESLA"] 
}

# --- 5. Sidebar Layout ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3209/3209990.png", width=70)
st.sidebar.markdown("### ⚡ AION CHONBURI War Room")
st.sidebar.caption("Data Intelligence Treand for Sales Team | By oofmakus")

# Tooltip คือคำอธิบายภาษาไทยเวลาเอาเมาส์ไปชี้
selected_preset = st.sidebar.selectbox(
    "🎯 เลือกกลุ่มเปรียบเทียบ:", 
    list(presets.keys()),
    help="เลือกกลุ่มรถยนต์ที่ต้องการเปรียบเทียบ หรือเลือกดูเทรนด์ราคา/ปัญหา"
)
kw_list = presets[selected_preset]

add_on = st.sidebar.text_input(
    "➕ เพิ่มคำค้นหาคู่แข่ง (ถ้ามี):", 
    "",
    help="พิมพ์ชื่อแบรนด์หรือรุ่นรถอื่นที่ต้องการเทียบเพิ่ม"
)
if add_on:
    kw_list.append(add_on)

selected_province_name = st.sidebar.selectbox("📍 พื้นที่:", list(provinces.keys()))
geo_code = provinces[selected_province_name]

selected_time_name = st.sidebar.selectbox("⏳ ช่วงเวลา:", list(timeframe_options.keys()))
timeframe_code = timeframe_options[selected_time_name]

st.sidebar.markdown("---")

# --- 6. ปุ่ม Run พร้อมระบบ Cooldown แบบ Real-time ---
current_time = time.time()
time_diff = current_time - st.session_state.last_run_time
cooldown_seconds = 20 

# ปุ่มกด
if st.sidebar.button('🚀 ประมวลผลข้อมูล', type="primary", use_container_width=True):
    if time_diff < cooldown_seconds:
        # คำนวณเวลาที่เหลือ
        wait_time = int(cooldown_seconds - time_diff)
        
        # สร้าง Placeholder ไว้แสดงตัวเลขนับถอยหลัง
        timer_placeholder = st.sidebar.empty()
        
        # Loop นับถอยหลังให้เห็นตัวเลขขยับ
        for i in range(wait_time, 0, -1):
            timer_placeholder.markdown(f"""
            <div class='cooldown-box'>
                ⛔ ใจเย็นวัยรุ่น!กดเร็วเกิน google จะบล็อค<br>
                ติด Cooldown: <b>{i}</b> วินาที
            </div>
            """, unsafe_allow_html=True)
            time.sleep(1) # หยุดรอ 1 วินาที
            
        # พอนับครบ ลบกล่องแจ้งเตือนออก แล้วบอกว่าพร้อม
        timer_placeholder.empty()
        st.sidebar.success("✅ พร้อมใช้งานแล้ว! กดปุ่มได้เลย")
        
    else:
        # ผ่าน -> บันทึกเวลาล่าสุด และสั่งรัน
        st.session_state.last_run_time = current_time
        st.session_state.run_triggered = True

# ปุ่มดู Trends Ranking (แก้บั๊กแล้ว)
if st.sidebar.button("🔥 เช็คเทรนด์ฮิต (Top Search)"):
    with st.spinner("กำลังดึงข้อมูล..."):
        df_trend, source_type = get_trends_ranking()
        
        st.sidebar.markdown(f"### 🇹🇭 {source_type}")
        if df_trend is not None and not df_trend.empty:
            # เปลี่ยนชื่อหัวตารางให้น่าอ่าน
            df_trend.columns = ['คำค้นหา'] if len(df_trend.columns) == 1 else df_trend.columns
            st.sidebar.dataframe(df_trend, hide_index=True, use_container_width=True)
        else:
            st.sidebar.warning("ไม่สามารถดึงข้อมูลได้ในขณะนี้")

# --- 7. Main Content Area ---
st.title(f"📊 {selected_preset.split('(')[0]}")
st.markdown(f"**พื้นที่:** {selected_province_name} | **เวลา:** {selected_time_name}")

# ส่วนอธิบายการใช้งาน (Manual) แบบย่อ
with st.expander("ℹ️ คำแนะนำการอ่านค่า (คลิกเพื่ออ่าน)"):
    st.markdown("""
    * **Score (0-100):** ไม่ใช่จำนวนคนค้นหา แต่เป็น "ดัชนีความนิยม" เทียบกัน (ใครได้ 100 คือชนะขาดลอย)
    * **กราฟ:** ถ้ากราฟพุ่งสูง แสดงว่าช่วงนั้นมีการค้นหาเยอะผิดปกติ (อาจมีข่าว หรือโปรโมชั่น)
    * **Insight:** คือคำที่คนมักจะพิมพ์ต่อท้าย เช่น ถ้าค้น "AION" แล้วมีคำว่า "ราคา" ตามมาเยอะ แปลว่าลูกค้าสนใจซื้อ
    """)

# ตรวจสอบ Trigger
if 'run_triggered' in st.session_state and st.session_state.run_triggered:
    st.session_state.run_triggered = False 

    with st.spinner('🤖 AI กำลังเจาะข้อมูลคู่แข่ง...'):
        results = get_trends_data(kw_list, timeframe_code, geo_code)
        
        if results["error"]:
            if "429" in results["error"]:
                st.error("⚠️ Google ทำงานหนักเกินไป (Rate Limit) - กรุณารอสัก 1-2 นาที แล้วค่อยกดใหม่")
            else:
                st.error(f"เกิดข้อผิดพลาด: {results['error']}")
        
        elif results["graph"] is not None:
            # --- A. Score Cards ---
            avg_data = results["average"]
            if avg_data:
                st.subheader("🏆 คะแนนความนิยมเฉลี่ย (Market Share Index)")
                cols = st.columns(len(kw_list))
                winner = max(avg_data, key=avg_data.get) if avg_data else None
                
                for i, (key, val) in enumerate(avg_data.items()):
                    with cols[i]:
                        if key == winner:
                            st.markdown(f"""
                            <div class='metric-card metric-winner'>
                                <div style='font-size:24px;'>🥇 ผู้นำตลาด</div>
                                <h3 style='margin:5px 0;'>{key}</h3>
                                <h1 style='margin:0; color:#006064;'>{val}</h1>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div class='metric-card'>
                                <div style='height:24px;'></div>
                                <h3 style='margin:5px 0; color:#555;'>{key}</h3>
                                <h2 style='margin:0; color:#777;'>{val}</h2>
                            </div>
                            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)

            # --- B. Plotly Graph ---
            df = results["graph"]
            fig = px.line(df, x=df.index, y=kw_list, 
                          title=f"📈 เส้นกราฟแสดงการค้นหา: {', '.join(kw_list)}",
                          template="plotly_white", 
                          color_discrete_sequence=px.colors.qualitative.Bold,
                          labels={'value': 'ดัชนีความสนใจ (Interest)', 'date': 'วันที่', 'variable': 'รุ่นรถ'})
            
            fig.update_traces(line=dict(width=3), mode='lines+markers')
            fig.update_layout(hovermode="x unified", height=450, font=dict(family="Prompt"))
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("📂 ดูตารางข้อมูลดิบ (Export Data)"):
                st.dataframe(df.sort_index(ascending=False))

            # --- C. Insight ---
            st.markdown("---")
            st.subheader("🔍 เจาะลึกความต้องการลูกค้า (Customer Intent)")
            
            if results["related"]:
                related = results["related"]
                cols = st.columns(len(kw_list))
                for i, kw in enumerate(kw_list):
                    with cols[i]:
                        st.info(f"คนที่ค้นหา **{kw}** สนใจเรื่องนี้ด้วย:")
                        if kw in related and related[kw]:
                            rising = related[kw]['rising']
                            top = related[kw]['top']
                            
                            tab1, tab2 = st.tabs(["🔥 กำลังมาแรง", "⭐ ยอดนิยม"])
                            with tab1:
                                if rising is not None:
                                    st.dataframe(rising.head(5)[['query', 'value']], hide_index=True)
                                else:
                                    st.caption("- ไม่มีเทรนด์ใหม่ -")
                            with tab2:
                                if top is not None:
                                    st.dataframe(top.head(5)[['query', 'value']], hide_index=True)
                                else:
                                    st.caption("- ไม่มีข้อมูล -")
                        else:
                            st.caption("- ไม่มีข้อมูล -")
            else:
                 st.info("💡 หมายเหตุ: ช่วงเวลานี้ข้อมูลน้อยเกินไป Google จึงไม่แสดง Insight เชิงลึก")
                 
        else:
            st.warning("⚠️ ไม่พบข้อมูลกราฟในช่วงเวลานี้ (ลองเปลี่ยนพื้นที่ หรือขยายช่วงเวลา)")

# --- Footer ---
st.markdown("<div class='footer'>AION Intelligent Dashboard | Developed by <b>oofmakus</b></div>", unsafe_allow_html=True)


