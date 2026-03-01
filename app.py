import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static

# --- 1. 頁面藝術化論述設定 ---
st.set_page_config(layout="wide", page_title="台灣蛙鳴環境聲景地圖")

st.markdown("""
    <h1 style='text-align: center; color: #C4E1FF; font-weight: 200; letter-spacing: 3px;'>
        🌿 台灣蛙鳴環境聲景：沉浸式地圖
    </h1>
    <p style='text-align: center; color: #888; font-size: 1.1em;'>
        每一聲紀錄如雨滴般落下，泛起 #C4E1FF 的柔和漣漪。
    </p>
""", unsafe_allow_html=True)

# --- 2. 核心資料讀取 ---
@st.cache_data
def load_data():
    def try_read(file_name):
        for enc in ['utf-8', 'big5', 'cp950', 'utf-8-sig']:
            try:
                return pd.read_csv(file_name, encoding=enc)
            except:
                continue
        return pd.read_csv(file_name, encoding='latin1')

    try:
        df_raw = try_read('raw_data.csv')
        df_verified = try_read('verified_data.csv')
        for df in [df_raw, df_verified]:
            df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
            df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
        return df_raw.dropna(subset=['Latitude', 'Longitude']), df_verified.dropna(subset=['Latitude', 'Longitude'])
    except:
        return pd.DataFrame(), pd.DataFrame()

raw_data, verified_data = load_data()

# --- 3. 建立地圖與藝術化點位 ---
if not raw_data.empty:
    # 建立地圖：使用 CartoDB Dark Matter 呈現台灣輪廓
    m = folium.Map(
        location=[23.6, 121.0], 
        zoom_start=7, 
        tiles="cartodbdarkmatter",
        dragging=True
    )

    # 定義藝術化漣漪 CSS (針對 #C4E1FF)
    ripple_style = """
    <style>
        @keyframes art_ripple {
            0% { transform: scale(1); opacity: 0.8; }
            100% { transform: scale(4); opacity: 0; filter: blur(3px); }
        }
        .ripple-container {
            display: flex; justify-content: center; align-items: center;
            width: 40px; height: 40px;
        }
        .core-6px {
            width: 6px; height: 6px; border-radius: 50%; z-index: 10;
        }
        .ripple-wave {
            position: absolute; width: 12px; height: 12px;
            border: 1px solid; border-radius: 50%;
            animation: art_ripple 4s infinite ease-out;
        }
    </style>
    """
    st.markdown(ripple_style, unsafe_allow_html=True)

    # 繪製民眾紀錄 (#C4E1FF)
    for _, row in raw_data.iterrows():
        html = f"""
        <div class="ripple-container">
            <div class="core-6px" style="background-color: #C4E1FF; box-shadow: 0 0 8px #C4E1FF;"></div>
            <div class="ripple-wave" style="border-color: #C4E1FF;"></div>
            <div class="ripple-wave" style="border-color: #C4E1FF; animation-delay: 2s;"></div>
        </div>
        """
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            icon=folium.DivIcon(html=html, icon_size=(40,40), icon_anchor=(20,20)),
            popup=row.get('Username', '匿名紀錄')
        ).add_to(m)

    # 繪製專家驗證 (#f1c40f)
    for _, row in verified_data.iterrows():
        html = f"""
        <div class="ripple-container">
            <div class="core-6px" style="background-color: #f1c40f; box-shadow: 0 0 8px #f1c40f;"></div>
        </div>
        """
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            icon=folium.DivIcon(html=html, icon_size=(40,40), icon_anchor=(20,20)),
            popup=row.get('Review Identity', '專家驗證')
        ).add_to(m)

    # 顯示地圖
    folium_static(m, width=1100, height=650)

else:
    st.info("請確保專案目錄中有 raw_data.csv")
