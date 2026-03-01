import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static

# --- 1. 頁面藝術化設定 ---
st.set_page_config(layout="wide", page_title="台灣蛙鳴環境聲景地圖")

st.markdown("""
    <div style="text-align: center;">
        <h1 style='color: #C4E1FF; font-weight: 200; letter-spacing: 3px;'>🌿 台灣蛙鳴環境聲景：沉浸式地圖</h1>
        <p style='color: #888; font-size: 1.1em;'>每一聲紀錄如雨滴般落下，泛起 #C4E1FF 的柔和漣漪。</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. 核心資料讀取 (強化容錯) ---
@st.cache_data
def load_data():
    def try_read(file_name):
        for enc in ['utf-8', 'big5', 'cp950', 'utf-8-sig']:
            try:
                return pd.read_csv(file_name, encoding=enc)
            except:
                continue
        return None

    df_raw = try_read('raw_data.csv')
    df_verified = try_read('verified_data.csv')
    
    processed_dfs = []
    for df in [df_raw, df_verified]:
        if df is not None:
            # 確保經緯度欄位名稱正確且為數字
            df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
            df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
            processed_dfs.append(df.dropna(subset=['Latitude', 'Longitude']))
        else:
            processed_dfs.append(pd.DataFrame())
    
    return processed_dfs[0], processed_dfs[1]

raw_data, verified_data = load_data()

# --- 3. 建立地圖與藝術化點位 ---
if not raw_data.empty or not verified_data.empty:
    # 建立地圖底圖
    m = folium.Map(
        location=[23.6, 121.0], 
        zoom_start=7, 
        tiles="cartodbdarkmatter"
    )

    # 動態漣漪 CSS
    ripple_style = """
    <style>
        @keyframes art_ripple {
            0% { transform: scale(1); opacity: 0.8; }
            100% { transform: scale(4); opacity: 0; filter: blur(3px); }
        }
        .ripple-container { display: flex; justify-content: center; align-items: center; width: 40px; height: 40px; }
        .core-6px { width: 6px; height: 6px; border-radius: 50%; z-index: 10; }
        .ripple-wave { position: absolute; width: 12px; height: 12px; border: 1px solid; border-radius: 50%; animation: art_ripple 4s infinite ease-out; }
    </style>
    """
    st.markdown(ripple_style, unsafe_allow_html=True)

    # 紀錄所有點位的座標，用來自動縮放地圖
    all_locations = []

    # 繪製民眾紀錄 (#C4E1FF)
    for _, row in raw_data.iterrows():
        loc = [row['Latitude'], row['Longitude']]
        all_locations.append(loc)
        html = f"""<div class="ripple-container">
            <div class="core-6px" style="background-color: #C4E1FF; box-shadow: 0 0 8px #C4E1FF;"></div>
            <div class="ripple-wave" style="border-color: #C4E1FF;"></div>
        </div>"""
        folium.Marker(
            location=loc,
            icon=folium.DivIcon(html=html, icon_size=(40,40), icon_anchor=(20,20)),
            popup=f"紀錄者: {row.get('Username', '匿名')}"
        ).add_to(m)

    # 繪製專家驗證 (#f1c40f)
    for _, row in verified_data.iterrows():
        loc = [row['Latitude'], row['Longitude']]
        all_locations.append(loc)
        html = f"""<div class="ripple-container">
            <div class="core-6px" style="background-color: #f1c40f; box-shadow: 0 0 8px #f1c40f;"></div>
        </div>"""
        folium.Marker(
            location=loc,
            icon=folium.DivIcon(html=html, icon_size=(40,40), icon_anchor=(20,20)),
            popup="專家驗證"
        ).add_to(m)

    # 如果有點位，自動將地圖縮放到包含所有點位的範圍
    if all_locations:
        m.fit_bounds(all_locations)

    # 顯示地圖
    folium_static(m, width=1100, height=650)
    
    # 底部狀態檢查
    st.write(f"✅ 成功載入 {len(raw_data)} 筆民眾紀錄與 {len(verified_data)} 筆專家驗證。")

else:
    st.warning("⚠️ 找不到任何有效的點位資料。請檢查 `raw_data.csv` 的 Latitude 與 Longitude 欄位內容是否正確。")
    st.write("目前讀取到的資料預覽：", raw_data.head())
