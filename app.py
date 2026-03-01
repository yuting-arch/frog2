import streamlit as st
import pandas as pd
import json

# --- 1. 頁面與全螢幕樣式設定 ---
st.set_page_config(layout="wide", page_title="台灣蛙鳴環境聲景：全螢幕沉浸地圖")

# 強制將 Streamlit 的所有邊距歸零，讓黑色展示框滿版
st.markdown("""
    <style>
        .main > div { padding: 0 !important; }
        iframe { border: none !important; }
        .stApp { background-color: #010101; }
        header { visibility: hidden; }
        footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 資料讀取與處理 ---
@st.cache_data
def load_and_process_data():
    def try_read(file_name):
        for enc in ['utf-8', 'big5', 'cp950', 'utf-8-sig']:
            try: return pd.read_csv(file_name, encoding=enc)
            except: continue
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

# --- 3. 整合式地圖與循環動畫 ---
if not raw_data.empty:
    raw_json = raw_data[['Latitude', 'Longitude', 'Username']].to_dict(orient='records')
    ver_json = verified_data[['Latitude', 'Longitude', 'Review Identity']].to_dict(orient='records')

    html_content = f"""
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <div id="map-container" style="position: absolute; top: 0; left: 0; width: 100vw; height: 100vh; background: #010101; overflow: hidden;">
        <div id="leaflet-map" style="width: 100%; height: 100%; z-index: 1;"></div>
        
        <div style="position: absolute; top: 20px; width: 100%; text-align: center; z-index: 1000; pointer-events: none;">
            <h1 style='color: #C4E1FF; font-weight: 200; letter-spacing: 5px; font-family: sans-serif; margin: 0;'>🌿 台灣蛙鳴環境聲景</h1>
            <p style='color: #888; font-size: 1em; letter-spacing: 1px;'>永續漣漪時序地圖</p>
        </div>
    </div>

    <style>
        @keyframes ripple-slow {{
            0% {{ transform: scale(1); opacity: 0; }}
            10% {{ opacity: 0.7; }}
            100% {{ transform: scale(8); opacity: 0; filter: blur(12px); }}
        }}
        .custom-ripple {{
            position: relative; display: flex; justify-content: center; align-items: center;
        }}
        .ripple-core {{
            width: 6px; height: 6px; background-color: #C4E1FF; 
            border-radius: 50%; box-shadow: 0 0 12px #C4E1FF;
        }}
        .ripple-wave {{
            position: absolute; width: 12px; height: 12px; border-radius: 50%;
            border: 1.5px solid #C4E1FF; 
            animation: ripple-slow 12s cubic-bezier(0.2, 0, 0.3, 1) forwards;
        }}
        .core-yellow {{ background-color: #f1c40f; box-shadow: 0 0 12px #f1c40f; }}
        .wave-yellow {{ border-color: #f1c40f; }}
    </style>

    <script>
        const map = L.map('leaflet-map', {{
            center: [23.6, 120.95],
            zoom: 7.5,
            zoomControl: false,
            dragging: true,
            scrollWheelZoom: true
        }});

        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: ''
        }}).addTo(map);

        const rawData = {json.dumps(raw_json)};
        const verData = {json.dumps(ver_json)};
        let markerLayer = L.layerGroup().addTo(map);

        function startPlayback() {{
            markerLayer.clearLayers();
            let totalDelay = 0;
            const step = 1200;

            rawData.forEach((p, i) => {{
                totalDelay = i * step;
                setTimeout(() => {{
                    addMarker(p.Latitude, p.Longitude, false);
                }}, totalDelay);
            }});

            const verStartDelay = totalDelay + step;
            verData.forEach((p, i) => {{
                setTimeout(() => {{
                    addMarker(p.Latitude, p.Longitude, true);
                }}, verStartDelay + (i * step));
            }});

            const totalCycleTime = verStartDelay + (verData.length * step) + 8000;
            setTimeout(startPlayback, totalCycleTime);
        }}

        function addMarker(lat, lon, isVerified) {{
            const icon = L.divIcon({{
                html: `<div class="custom-ripple">
                        <div class="ripple-core ${{isVerified ? 'core-yellow' : ''}}"></div>
                        <div class="ripple-wave ${{isVerified ? 'wave-yellow' : ''}}"></div>
                       </div>`,
                className: '',
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            }});
            L.marker([lat, lon], {{icon: icon}}).addTo(markerLayer);
        }}

        startPlayback();
    </script>
    """

    # 將 Streamlit 元件設定為充滿視窗的高度
    st.components.v1.html(html_content, height=1000) # 設定足夠大的高度值，內部 JS 會控制 100vh

else:
    st.warning("找不到 CSV 資料。")
