import streamlit as st
import pandas as pd
import json

# --- 1. 頁面與全螢幕樣式設定 ---
st.set_page_config(layout="wide", page_title="台灣蛙鳴環境聲景")

st.markdown("""
    <style>
        .main > div { padding: 0 !important; }
        iframe { border: none !important; }
        .stApp { background-color: #010101; }
        header, footer, #MainMenu { visibility: hidden; }
        [data-testid="stHeader"] { display: none; }
        .block-container { padding: 0 !important; max-width: 100% !important; }
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

# --- 3. 整合式地圖與多重漣漪動畫 ---
if not raw_data.empty:
    raw_json = raw_data[['Latitude', 'Longitude', 'Username']].to_dict(orient='records')
    ver_json = verified_data[['Latitude', 'Longitude', 'Review Identity']].to_dict(orient='records')

    html_content = f"""
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <div id="map-container" style="position: absolute; top: 0; left: 0; width: 100vw; height: 100vh; background: #010101; overflow: hidden;">
        <div id="leaflet-map" style="width: 100%; height: 100%; z-index: 1;"></div>
    </div>

    <style>
        /* 優化：輕柔落點動畫 */
        @keyframes ripple-soft-spread {{
            0% {{ 
                transform: translate(-50%, -50%) scale(0.2); 
                opacity: 0; 
                filter: blur(2px);
            }}
            15% {{ 
                opacity: 0.5; /* 緩慢浮現，不生硬刺眼 */
            }}
            100% {{ 
                transform: translate(-50%, -50%) scale(9); 
                opacity: 0; 
                filter: blur(12px); 
            }}
        }}

        .custom-ripple {{
            position: relative; 
            display: flex; 
            justify-content: center; 
            align-items: center;
        }}

        .ripple-core {{
            width: 4px; height: 4px; 
            background-color: #C4E1FF; 
            border-radius: 50%; 
            box-shadow: 0 0 12px rgba(196, 225, 255, 0.6);
            opacity: 0;
            animation: core-fade 2s ease-out forwards;
        }}

        @keyframes core-fade {{
            0% {{ opacity: 0; }}
            100% {{ opacity: 0.8; }}
        }}

        .ripple-wave {{
            position: absolute; 
            width: 10px; height: 10px; 
            border-radius: 50%;
            border: 0.5px solid #C4E1FF; 
            /* 使用緩入緩出的貝點曲線，讓開頭更輕柔 */
            animation: ripple-soft-spread 12s cubic-bezier(0.15, 0, 0.2, 1) forwards;
            pointer-events: none;
        }}

        .core-yellow {{ background-color: #f1c40f; box-shadow: 0 0 12px rgba(241, 196, 15, 0.6); }}
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
            const step = 1800; // 稍微拉長落點間隔，增加呼吸感

            const allData = [
                ...rawData.map(p => ({{...p, isVer: false}})),
                ...verData.map(p => ({{...p, isVer: true}}))
            ];

            allData.forEach((p, i) => {{
                totalDelay = i * step;
                setTimeout(() => {{
                    addMultiRippleMarker(p.Latitude, p.Longitude, p.isVer);
                }}, totalDelay);
            }});

            const cycleBuffer = 15000; 
            setTimeout(startPlayback, totalDelay + cycleBuffer);
        }}

        function addMultiRippleMarker(lat, lon, isVer) {{
            const colorClass = isVer ? 'wave-yellow' : '';
            const coreClass = isVer ? 'core-yellow' : '';
            
            const icon = L.divIcon({{
                html: `<div class="custom-ripple">
                        <div class="ripple-core ${{coreClass}}"></div>
                        <div class="ripple-wave ${{colorClass}}" style="animation-delay: 0s;"></div>
                        <div class="ripple-wave ${{colorClass}}" style="animation-delay: 3s;"></div>
                        <div class="ripple-wave ${{colorClass}}" style="animation-delay: 6s;"></div>
                       </div>`,
                className: '',
                iconSize: [1, 1], // 縮小容器錨點
                iconAnchor: [0.5, 0.5]
            }});
            L.marker([lat, lon], {{icon: icon}}).addTo(markerLayer);
        }}

        setTimeout(startPlayback, 1000);
    </script>
    """

    st.components.v1.html(html_content, height=1200)

else:
    st.error("無法讀取資料。")
