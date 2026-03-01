import streamlit as st
import pandas as pd
import json

# --- 1. 頁面設定 ---
st.set_page_config(layout="wide", page_title="台灣蛙鳴環境聲景地圖")

st.markdown("""
    <div style="text-align: center;">
        <h1 style='color: #C4E1FF; font-weight: 200; letter-spacing: 3px;'>🌿 台灣蛙鳴環境聲景：時序漣漪地圖</h1>
        <p style='color: #888; font-size: 1.1em;'>底圖已鎖定。資料將依序在精確座標泛起 #C4E1FF 漣漪。</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. 資料讀取與時序排序 ---
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

# --- 3. 生成整合式地圖與動畫 (單一 HTML 容器) ---
if not raw_data.empty:
    raw_list = raw_data[['Latitude', 'Longitude', 'Username']].to_dict(orient='records')
    ver_list = verified_data[['Latitude', 'Longitude', 'Review Identity']].to_dict(orient='records')

    # 這裡我們手動建構一個包含 Leaflet 地圖與 CSS 動畫的完整 HTML
    html_content = f"""
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <div id="map-container" style="position: relative; width: 100%; height: 650px; background: #010101; border-radius: 12px; overflow: hidden;">
        <div id="leaflet-map" style="width: 100%; height: 100%; z-index: 1;"></div>
    </div>

    <style>
        @keyframes ripple-anim {{
            0% {{ transform: scale(1); opacity: 0.8; }}
            100% {{ transform: scale(4.5); opacity: 0; filter: blur(4px); }}
        }}
        .custom-ripple {{
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .ripple-core {{
            width: 6px; height: 6px; background-color: #C4E1FF; 
            border-radius: 50%; box-shadow: 0 0 8px #C4E1FF;
        }}
        .ripple-wave {{
            position: absolute; width: 12px; height: 12px; border-radius: 50%;
            border: 1px solid #C4E1FF; animation: ripple-anim 4s ease-out forwards;
        }}
        .core-yellow {{ background-color: #f1c40f; box-shadow: 0 0 8px #f1c40f; }}
        .wave-yellow {{ border-color: #f1c40f; }}
    </style>

    <script>
        const map = L.map('leaflet-map', {{
            center: [23.6, 120.9],
            zoom: 7,
            zoomControl: false,
            dragging: true,
            scrollWheelZoom: false
        }});

        // 使用 CartoDB Dark Matter 清楚底圖
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap &copy; CARTO'
        }}).addTo(map);

        const rawData = {json.dumps(raw_list)};
        const verData = {json.dumps(ver_list)};

        function addRipple(lat, lon, isVerified, name, delay) {{
            setTimeout(() => {{
                const colorClass = isVerified ? 'yellow' : '';
                const icon = L.divIcon({{
                    html: `<div class="custom-ripple">
                            <div class="ripple-core ${{isVerified ? 'core-yellow' : ''}}"></div>
                            <div class="ripple-wave ${{isVerified ? 'wave-yellow' : ''}}"></div>
                           </div>`,
                    className: '',
                    iconSize: [20, 20],
                    iconAnchor: [10, 10]
                }});
                L.marker([lat, lon], {{icon: icon}}).addTo(map).bindPopup(name);
            }}, delay);
        }}

        // 依序滴入動畫
        rawData.forEach((p, i) => {{
            addRipple(p.Latitude, p.Longitude, false, p.Username, i * 400);
        }});

        setTimeout(() => {{
            verData.forEach((p, i) => {{
                addRipple(p.Latitude, p.Longitude, true, '專家驗證', i * 400);
            }});
        }}, 2000);
    </script>
    """

    st.components.v1.html(html_content, height=670)

    st.sidebar.markdown(f"### 📍 聲景數據")
    st.sidebar.write(f"正在依時序播放 {len(raw_data)} 筆紀錄...")
    if st.sidebar.button("🔄 重新載入動畫"):
        st.rerun()
else:
    st.warning("找不到 CSV 資料。請檢查 GitHub 上的 raw_data.csv 是否正確。")
