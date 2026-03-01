import streamlit as st
import pandas as pd
import json

# --- 1. 頁面與全螢幕樣式設定 ---
st.set_page_config(layout="wide", page_title="Identifrog: Frog Voiceprint Identification Project")

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

# --- 3. 整合式地圖與科技感漣漪動畫 ---
if not raw_data.empty:
    raw_json = raw_data[['Latitude', 'Longitude', 'Username']].to_dict(orient='records')
    ver_json = verified_data[['Latitude', 'Longitude', 'Review Identity']].to_dict(orient='records')

    html_content = f"""
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <div id="map-container" style="position: absolute; top: 0; left: 0; width: 100vw; height: 100vh; background: #010101; overflow: hidden;">
        <div style="position: absolute; top: 35px; width: 100%; text-align: center; z-index: 1000; pointer-events: none;">
            <h1 style='color: #C4E1FF; font-weight: 100; letter-spacing: 5px; font-family: "Helvetica Neue", Arial, sans-serif; margin: 0; opacity: 0.9;'>
                IDENTIFROG
            </h1>
            <p style='color: #666; font-size: 0.8em; letter-spacing: 2px; margin-top: 8px; font-family: sans-serif; font-weight: 200;'>
                Frog Voiceprint Identification Project
            </p>
        </div>
        <div id="leaflet-map" style="width: 100%; height: 100%; z-index: 1;"></div>
    </div>

    <style>
        /* 核心科技感動畫：模擬影片中的立體發光波紋 */
        @keyframes tech-ripple-spread {{
            0% {{ 
                transform: scale(0.5); 
                opacity: 0; 
                box-shadow: 0 0 0px 0px rgba(196, 225, 255, 0);
            }}
            20% {{ 
                opacity: 0.8; 
                box-shadow: 0 0 20px 2px rgba(196, 225, 255, 0.4);
            }}
            100% {{ 
                transform: scale(10); 
                opacity: 0; 
                filter: blur(4px);
                box-shadow: 0 0 50px 10px rgba(196, 225, 255, 0);
            }}
        }}

        .custom-ripple {{
            position: relative; display: flex; justify-content: center; align-items: center;
        }}

        /* 能量核心點 */
        .ripple-core {{
            width: 4px; height: 4px; 
            background-color: #fff; 
            border-radius: 50%; 
            box-shadow: 0 0 15px 3px #C4E1FF, 0 0 30px 5px rgba(196, 225, 255, 0.3);
            z-index: 10;
        }}

        /* 科技發光環：使用徑向漸層營造立體感 */
        .ripple-wave {{
            position: absolute; width: 15px; height: 15px; border-radius: 50%;
            /* 模擬影片中的光環質感 */
            background: radial-gradient(circle, transparent 40%, rgba(196, 225, 255, 0.2) 60%, rgba(196, 225, 255, 0.6) 85%, transparent 100%);
            border: 0.5px solid rgba(196, 225, 255, 0.3);
            animation: tech-ripple-spread 8s cubic-bezier(0.1, 0.4, 0.2, 1) forwards;
            pointer-events: none;
        }}

        .core-yellow {{ box-shadow: 0 0 15px 3px #f1c40f, 0 0 30px 5px rgba(241, 196, 15, 0.3); }}
        .wave-yellow {{ background: radial-gradient(circle, transparent 40%, rgba(241, 196, 15, 0.1) 60%, rgba(241, 196, 15, 0.5) 85%, transparent 100%); border-color: rgba(241, 196, 15, 0.3); }}
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
            const step = 2000; 

            const allData = [
                ...rawData.map(p => ({{...p, isVer: false}})),
                ...verData.map(p => ({{...p, isVer: true}}))
            ];

            allData.forEach((p, i) => {{
                totalDelay = i * step;
                setTimeout(() => {{
                    addTechRipple(p.Latitude, p.Longitude, p.isVer);
                }}, totalDelay);
            }});

            const cycleBuffer = 15000; 
            setTimeout(startPlayback, totalDelay + cycleBuffer);
        }}

        function addTechRipple(lat, lon, isVer) {{
            const colorClass = isVer ? 'wave-yellow' : '';
            const coreClass = isVer ? 'core-yellow' : '';
            
            const icon = L.divIcon({{
                html: `<div class="custom-ripple">
                        <div class="ripple-core ${{coreClass}}"></div>
                        <div class="ripple-wave ${{colorClass}}" style="animation-delay: 0s;"></div>
                        <div class="ripple-wave ${{colorClass}}" style="animation-delay: 1.5s;"></div>
                        <div class="ripple-wave ${{colorClass}}" style="animation-delay: 3s;"></div>
                       </div>`,
                className: '',
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            }});
            L.marker([lat, lon], {{icon: icon}}).addTo(markerLayer);
        }}

        setTimeout(startPlayback, 1000);
    </script>
    """

    st.components.v1.html(html_content, height=1200)

else:
    st.error("無法讀取 CSV 資料。")
