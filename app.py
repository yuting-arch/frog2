import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import json

# --- 1. 頁面設定 ---
st.set_page_config(layout="wide", page_title="台灣蛙鳴聲景地圖")

st.markdown("""
    <div style="text-align: center;">
        <h1 style='color: #C4E1FF; font-weight: 200; letter-spacing: 3px;'>🌿 台灣蛙鳴環境聲景：時序沉浸地圖</h1>
        <p style='color: #888; font-size: 1.1em;'>底圖清晰呈現，資料將依據 Create Date 順序泛起 #C4E1FF 的漣漪。</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. 資料讀取與時序處理 ---
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
            return df.dropna(subset=['Latitude', 'Longitude', 'Create Date']).sort_values('Create Date')
        return pd.DataFrame()

    return finalize(df_raw), finalize(df_verified)

raw_data, verified_data = load_and_process_data()

# --- 3. 繪製地圖與注入動畫腳本 ---
if not raw_data.empty:
    # 建立地圖 (底圖非常清楚)
    m = folium.Map(
        location=[23.6, 121.0], 
        zoom_start=7, 
        tiles="cartodbdarkmatter"
    )

    # 準備 JSON 數據
    raw_list = raw_data[['Latitude', 'Longitude', 'Username']].to_dict(orient='records')
    ver_list = verified_data[['Latitude', 'Longitude', 'Review Identity']].to_dict(orient='records')

    # 動畫 CSS 與控制邏輯
    # 這裡讓點位直接出現並泛起漣漪，移除掉落感以維持地圖穩定度
    custom_script = f"""
    <style>
        @keyframes ripple-art {{
            0% {{ transform: scale(1); opacity: 0.8; }}
            100% {{ transform: scale(4.5); opacity: 0; filter: blur(4px); }}
        }}
        .art-core {{
            width: 6px; height: 6px; border-radius: 50%;
            position: absolute; transform: translate(-50%, -50%);
        }}
        .art-ripple {{
            position: absolute; width: 12px; height: 12px; border-radius: 50%;
            border: 1px solid; transform: translate(-50%, -50%) scale(0);
            animation: ripple-art 4s ease-out forwards;
            pointer-events: none;
        }}
    </style>
    <script>
        window.onload = function() {{
            const rawData = {json.dumps(raw_list)};
            const verData = {json.dumps(ver_list)};
            
            // 獲取 Leaflet 地圖實例
            const mapElement = window.parent.document.querySelector('.leaflet-container');
            if (!mapElement) return;

            // 這裡使用延遲確保地圖載入完成
            setTimeout(() => {{
                const leafletMap = window.parent.L.DomUtil.get('map')._leaflet_map;

                // 播放函數
                function dropRipple(data, color, delayStep) {{
                    data.forEach((p, i) => {{
                        setTimeout(() => {{
                            const icon = window.parent.L.divIcon({{
                                html: `<div style="position:relative;">
                                        <div class="art-core" style="background-color:${{color}}; box-shadow: 0 0 8px ${{color}};"></div>
                                        <div class="art-ripple" style="border-color:${{color}};"></div>
                                       </div>`,
                                className: '',
                                iconSize: [1, 1]
                            }});
                            window.parent.L.marker([p.Latitude, p.Longitude], {{icon: icon}}).addTo(leafletMap);
                        }}, i * delayStep);
                    }});
                }}

                dropRipple(rawData, '#C4E1FF', 400); // 每一筆間隔 0.4 秒
                setTimeout(() => dropRipple(verData, '#f1c40f', 400), 2000);
            }}, 1500);
        }};
    </script>
    """
    
    # 顯示 Folium 地圖
    folium_static(m, width=1100, height=650)
    
    # 注入動畫控制層 (隱形元件)
    st.components.v1.html(custom_script, height=0)
    
    st.sidebar.success(f"已依時序載入 {len(raw_data)} 筆紀錄")
    if st.sidebar.button("重新播放時序"):
        st.rerun()
else:
    st.warning("請檢查 CSV 檔案路徑與資料內容。")
