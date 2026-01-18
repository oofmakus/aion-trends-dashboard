import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import plotly.express as px

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="AION Monitor Pro", page_icon="⚡", layout="wide")

# เชื่อมต่อ Google Trends
# retries และ backoff_factor ช่วยลดโอกาส error
pytrends = TrendReq(hl='th-TH', tz=420, retries=2, backoff_factor=0.1)

# --- ส่วนตั้งค่า (Config) ---
# 1. รายชื่อจังหวัด (คุณสามารถเพิ่มเองได้โดยดูรหัส ISO 3166-2:TH)
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

# 2. ช่วงเวลา (Timeframe)
timeframe_options = {
    "1 ชั่วโมงที่ผ่านมา (ละเอียดสุด)": "now 1-H",
    "4 ชั่วโมงที่ผ่านมา": "now 4-H",
    "1 วันที่ผ่านมา": "now 1-d",
    "7 วันที่ผ่านมา": "now 7-d",
    "30 วันที่ผ่านมา": "today 1-m",
    "90 วันที่ผ่านมา": "today 3-m",
    "12 เดือนที่ผ่านมา": "today 12-m"
}

# 3. Preset คำค้นหา (บันทึกชุดคำที่คุณใช้บ่อยที่นี่)
presets = {
    "1. กำหนดเอง (พิมพ์ใหม่)": [],
    "2. AION vs คู่แข่งหลัก": ["AION", "BYD", "DEEPAL", "MG", "OMODA"],
    "3. เทียบรุ่นเล็ก (ES vs Dolphin)": ["AION UT", "BYD Dolphin", "ORA Good Cat", "MG4" ],
    "4. เทียบรุ่นใหญ่ (Y Plus vs Atto 3)": ["AION V", "BYD Atto 3","jaecoo 5"],
    # คุณสามารถเพิ่มบรรทัดใหม่ตรงนี้ได้เลย เช่น:
    # "5. ชื่อโปรเจกต์ของคุณ": ["คำ1", "คำ2"],
}

# --- ส่วนแสดงผล Sidebar ---
st.sidebar.title("⚡ AION War Room")

# เลือก Preset
selected_preset = st.sidebar.selectbox("เลือกชุดคำค้นหา (Saved Lists):", list(presets.keys()))

# Logic การเลือกคำ
if selected_preset == "1. กำหนดเอง (พิมพ์ใหม่)":
    # ใช้ session_state เพื่อจำค่าที่พิมพ์ไว้ชั่วคราว
    if 'custom_kw' not in st.session_state:
        st.session_state.custom_kw = "AION, BYD"
    user_kw = st.sidebar.text_input("พิมพ์คำค้นหา (คั่นด้วย ,)", st.session_state.custom_kw)
    st.session_state.custom_kw = user_kw # อัปเดตค่า
    kw_list = [x.strip() for x in user_kw.split(',')]
else:
    kw_list = presets[selected_preset]
    st.sidebar.info(f"คำค้นหา: {', '.join(kw_list)}")

# เลือกพื้นที่
selected_province_name = st.sidebar.selectbox("เลือกพื้นที่ (Location):", list(provinces.keys()))
geo_code = provinces[selected_province_name]

# เลือกเวลา
selected_time_name = st.sidebar.selectbox("ช่วงเวลา (Timeframe):", list(timeframe_options.keys()))
timeframe_code = timeframe_options[selected_time_name]

# ปุ่มรัน
run_btn = st.sidebar.button('🚀 วิเคราะห์ข้อมูล', type="primary")

# --- ส่วนแสดงผลหลัก (Main) ---
st.title(f"📈 Trends Analysis: {selected_province_name}")
st.caption(f"ช่วงเวลา: {selected_time_name}")

if run_btn:
    with st.spinner('กำลังดึงข้อมูล...'):
        try:
            # สร้าง Payload
            pytrends.build_payload(kw_list, cat=0, timeframe=timeframe_code, geo=geo_code)
            
            # 1. ดึงข้อมูล Interest Over Time
            data = pytrends.interest_over_time()
            
            if not data.empty:
                data = data.drop(labels=['isPartial'], axis=1)
                
                # สร้างกราฟ
                fig = px.line(data, x=data.index, y=kw_list, 
                              title=f"ปริมาณการค้นหาใน {selected_province_name}",
                              labels={'value': 'ความสนใจ (0-100)', 'date': 'เวลา', 'variable': 'คำค้นหา'})
                st.plotly_chart(fig, use_container_width=True)
                
                # แสดง Dataframe ดิบ (เผื่ออยากดูละเอียด)
                with st.expander("ดูข้อมูลดิบ (Table)"):
                    st.dataframe(data.sort_index(ascending=False))
            else:
                st.warning(f"⚠️ ไม่พบข้อมูลการค้นหาใน '{selected_province_name}' ในช่วงเวลานี้ (ลองขยายเวลาหรือเปลี่ยนพื้นที่)")

            # 2. Related Queries (เฉพาะตอนเลือก Timeframe > 1 วัน ถึงจะแม่นยำ)
            st.markdown("---")
            st.subheader("🔍 คำค้นหาที่เกี่ยวข้อง (Insight)")
            
            # Google Trends บางครั้งไม่ส่ง Related Queries ถ้าเลือกเวลาน้อยกว่า 1 วัน
            if "now" in timeframe_code and "H" in timeframe_code:
                 st.info("💡 หมายเหตุ: การดูข้อมูลรายชั่วโมง (Hourly) Google อาจจะไม่แสดง 'คำค้นหาที่เกี่ยวข้อง' ได้ครบถ้วนเท่าแบบรายวัน")

            related = pytrends.related_queries()
            cols = st.columns(len(kw_list))
            
            for i, kw in enumerate(kw_list):
                with cols[i]:
                    st.markdown(f"**{kw}**")
                    if related.get(kw):
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

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
            st.write("คำแนะนำ: ลองกดปุ่มรันใหม่อีกครั้ง หรือลดจำนวนคำค้นหา")
