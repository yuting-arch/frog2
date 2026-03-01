import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import json

# --- 1. 頁面藝術化設定 ---
st.set_page_config(layout="wide", page_title="台灣蛙鳴環境聲景地圖")

st.markdown("""
    <div style="text-align: center; margin-bottom: 10px;">
        <h1 style='color: #C4E1FF; font-weight: 200; letter-spacing: 3px;'>🌿 台灣蛙鳴環境聲景：時序水滴地圖</h1>
        <p style='color: #888; font-size: 1.1em;'>每一聲紀錄如雨滴般落下，沒入台灣的夜色中。</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. 核心資料讀取與時序排序 ---
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
    
    # 處理與排序資料
    def process_df(df):
        if df is not None:
            df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
            df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
            df['Create Date'] = pd.to_datetime(df['Create Date'], errors='coerce')
            return df.dropna(subset=['Latitude', 'Longitude', 'Create Date']).sort_values('Create Date')
        return pd.DataFrame()

    return process_df(df_raw), process_df(df_verified)

raw_data, verified_data = load_and_process_data()

# --- 3. 建立地圖 ---
if not raw_data.empty or not verified_data.empty:
    # 建立 Folium 地圖 (底圖非常清楚)
    m = folium.Map(
        location=[23.6, 121.0], 
        zoom_start=7, 
        tiles="cartodbdarkmatter",
        zoom_control=True
    )

    # 4. 插入自定義時序動畫腳本 (讓點位像水滴般滴入)
    # 我們將資料轉為 JSON 傳給 JavaScript
    raw_list = raw_data[['Latitude', 'Longitude', 'Username']].to_dict(orient='records')
    ver_list = verified_data[['Latitude', 'Longitude', 'Review Identity']].to_dict(orient='records')

    # 定義動畫 CSS 與 JS
    custom_script = f"""
    <style>
        @keyframes drop-in {{
            0% {{ transform: translateY(-100px); opacity: 0; }}
            80% {{ opacity: 1; }}
            100% {{ transform: translateY(0); opacity: 1; }}
        }}
        @keyframes ripple-fade {{
            0% {{ transform: scale(0.2); opacity: 0.8; }}
            100% {{ transform: scale(4); opacity: 0; filter: blur(4px); }}
        }}
        .drop-core {{
            width: 6px; height: 6px; border-radius: 50%;
            animation: drop-in 0.8s ease-in forwards;
        }}
        .ripple-effect {{
            position: absolute; width: 15px; height: 15px; border-radius: 50%;
            border: 1px solid; animation: ripple-fade 4s ease-out forwards;
            left: -4.5px; top: -4.5px; /* 校正中心點 */
        }}
    </style>
    <script>
        window.onload = function() {{
            const rawData = {json.dumps(raw_list)};
            const verData = {json.dumps(ver_list)};
            
            // 由於 Folium 渲染需要時間，延遲 1 秒後開始滴落動畫
            setTimeout(() => {{
                // 處理民眾資料
                rawData.forEach((point, i) => {{
                    setTimeout(() => {{
                        addArtMarker(point.Latitude, point.Longitude, '#C4E1FF', point.Username);
                    }}, i * 400); // 每 0.4 秒滴入一筆
                }});

                // 處理專家資料 (延遲 2 秒後開始)
                setTimeout(() => {{
                    verData.forEach((point, i) => {{
                        setTimeout(() => {{
                            addArtMarker(point.Latitude, point.Longitude, '#f1c40f', '專家驗證');
                        }}, i * 400);
                    }});
                }}, 2000);
            }}, 1000);
        }};

        function addArtMarker(lat, lon, color, name) {{
            // 這是 Leaflet 的 API，在地圖上動態新增標記
            const map = window.parent.L.DomUtil.get('map')._leaflet_map; 
            const icon = window.parent.L.divIcon({{
                html: `<div style="position:relative;">
                        <div class="drop-core" style="background-color:${{color}}; box-shadow:0 0 8px ${{color}};"></div>
                        <div class="ripple-effect" style="border-color:${{color}};"></div>
                       </div>`,
                className: '',
                iconSize: [6, 6],
                iconAnchor: [3, 3]
            }});
            window.parent.L.marker([lat, lon], {{icon: icon}}).addTo(map).bindPopup(name);
        }}
    </script>
    """
    
    # 將地圖顯示出來
    folium_static(m, width=1100, height=650)
    
    # 注入動畫腳本
    st.components.v1.html(custom_script, height=0)

    st.write(f"✅ 已準備好 {len(raw_data)} 筆資料，地圖正在依序滴入中...")

else:
    st.warning("⚠️ 找不到有效資料。請檢查 CSV 檔案與欄位名稱（Latitude, Longitude, Create Date）。")
