import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import json

# --- 1. 頁面藝術化設定 ---
st.set_page_config(layout="wide", page_title="台灣蛙鳴環境聲景地圖")

st.markdown("""
    <div style="text-align: center;">
        <h1 style='color: #C4E1FF; font-weight: 200; letter-spacing: 3px;'>🌿 台灣蛙鳴環境聲景：時序沉浸地圖</h1>
        <p style='color: #888; font-size: 1.1em;'>地圖已對齊。資料將依據 Create Date 順序在地圖上泛起 #C4E1FF 的漣漪。</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. 核心資料讀取與時序處理 ---
@st.cache_data
def load_and_process_data():
    def try_read(file_name):
        for enc in ['utf-8', 'big5', 'cp950', 'utf-8-sig']:
            try:
                return pd.read_csv(file_name, encoding=enc)
            except:
                continue
        return None

    df_raw = try_read('raw_data.csv')
    df_verified = try_read('verified_data.csv')
    
    def finalize(df):
        if df is not None:
            df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
            df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
            df['Create Date'] = pd.to_datetime(df['Create Date'], errors='coerce')
            # 依時間排序是動畫的靈魂
            return df.dropna(subset=['Latitude', 'Longitude', 'Create Date']).sort_values('Create Date')
        return pd.DataFrame()

    return finalize(df_raw), finalize(df_verified)

raw_data, verified_data = load_and_process_data()

# --- 3. 建立地圖 ---
if not raw_data.empty:
    # 建立一個基礎地圖，不直接在裡面畫點
    m = folium.Map(
        location=[23.6, 121.0], 
        zoom_start=7, 
        tiles="cartodbdarkmatter"
    )

    # 準備資料與 JavaScript 動畫腳本
    raw_list = raw_data[['Latitude', 'Longitude', 'Username']].to_dict(orient='records')
    ver_list = verified_data[['Latitude', 'Longitude', 'Review Identity']].to_dict(orient='records')

    # CSS 動畫：核心與淡化漣漪
    animation_js = f"""
    <style>
        @keyframes ripple-play {{
            0% {{ transform: scale(1); opacity: 0.8; }}
            100% {{ transform: scale(4.5); opacity: 0; filter: blur(4px); }}
        }}
        .ripple-core {{
            width: 6px; height: 6px; border-radius: 50%;
            position: absolute; transform: translate(-50%, -50%);
        }}
        .ripple-wave {{
            position: absolute; width: 12px; height: 12px; border-radius: 50%;
            border: 1px solid; transform: translate(-50%, -50%) scale(0);
            animation: ripple-play 4s ease-out forwards;
        }}
    </style>
    <script>
        // 等待地圖與視窗完全載入
        window.addEventListener('load', function() {{
            const rawData = {json.dumps(raw_list)};
            const verData = {json.dumps(ver_list)};
            
            // 延遲 2 秒開始，確保 Streamlit 的 iframe 完全穩定
            setTimeout(() => {{
                // 獲取 Leaflet 地圖實例 (關鍵點)
                const maps = [];
                window.parent.L.Map.eachLayer(function(layer) {{
                    if (layer instanceof window.parent.L.Map) maps.push(layer);
                }});
                const leafletMap = maps[0]; 

                if (!leafletMap) return;

                function addAnimatedPoint(p, color, i, stepDelay) {{
                    setTimeout(() => {{
                        const icon = window.parent.L.divIcon({{
                            html: `<div style="position:relative;">
                                    <div class="ripple-core" style="background-color:${{color}}; box-shadow: 0 0 8px ${{color}};"></div>
                                    <div class="ripple-wave" style="border-color:${{color}};"></div>
                                   </div>`,
                            className: '',
                            iconSize: [1, 1]
                        }});
                        window.parent.L.marker([p.Latitude, p.Longitude], {{icon: icon}}).addTo(leafletMap);
                    }}, i * stepDelay);
                }}

                // 按順序播放
                rawData.forEach((p, i) => addAnimatedPoint(p, '#C4E1FF', i, 500));
                setTimeout(() => {{
                    verData.forEach((p, i) => addAnimatedPoint(p, '#f1c40f', i, 500));
                }}, 2000);

            }}, 2000);
        }});
    </script>
    """
    
    # 呈現地圖
    folium_static(m, width=1100, height=650)
    
    # 注入動畫邏輯 (使用 hidden container)
    st.components.v1.html(animation_js, height=0)

    st.sidebar.markdown(f"### 🌙 聲景撥放狀態")
    st.sidebar.write(f"正在依時序播放 {len(raw_data)} 筆紀錄...")
    if st.sidebar.button("🔄 重新播放動畫"):
        st.rerun()
else:
    st.warning("資料載入中，請確保 GitHub 上的 CSV 檔案正確。")
