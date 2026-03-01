import streamlit as st
import pandas as pd
import json

# --- 1. 頁面設定 ---
st.set_page_config(layout="wide", page_title="台灣蛙鳴環境聲景：永續漣漪地圖")

st.markdown("""
    <div style="text-align: center;">
        <h1 style='color: #C4E1FF; font-weight: 200; letter-spacing: 3px;'>🌿 台灣蛙鳴環境聲景：永續漣漪地圖</h1>
        <p style='color: #888; font-size: 1.1em;'>動畫已設定為自動重複播放。地圖支援滾輪縮放與拖動，高度已增加以呈現完整視野。</p>
    </div>
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
    raw_list = raw_data[['Latitude', 'Longitude', 'Username']].to_dict(orient='records')
    ver_list = verified_data[['Latitude', 'Longitude', 'Review Identity']].to_dict(orient='records')

    html_content = f"""
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <div id="map-container" style="position: relative; width: 95%; height: 750px; background: #010101; border-radius: 15px; overflow: hidden; margin: 0 auto; border: 1px solid #1A3A3A;">
        <div id="leaflet-map" style="width: 100%; height: 100%; z-index: 1;"></div>
    </div>

    <style>
        @keyframes ripple-slow {{
            0% {{ transform: scale(1); opacity: 0; }}
            10% {{ opacity: 0.7; }}
            100% {{ transform: scale(7); opacity: 0; filter: blur(10px); }}
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
            border: 1px solid #C4E1FF; 
            animation: ripple-slow 12s cubic-bezier(0.2, 0, 0.3, 1) forwards;
        }}
        .core-yellow {{ background-color: #f1c40f; box-shadow: 0 0 12px #f1c40f; }}
        .wave-yellow {{ border-color: #f1c40f; }}
    </style>

    <script>
        // 設定中心點與縮放，7.2 在 750px 高度下能完美呈現台灣全島
        const map = L.map('leaflet-map', {{
            center: [23.6, 120.95],
            zoom: 7.2,
            zoomControl: true,
            dragging: true,
            scrollWheelZoom: true
        }});

        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; CARTO'
        }}).addTo(map);

        const rawData = {json.dumps(raw_list)};
        const verData = {json.dumps(ver_list)};
        let markerLayer = L.layerGroup().addTo(map);

        function startPlayback() {{
            markerLayer.clearLayers();
            let totalDelay = 0;
            const step = 1200;

            rawData.forEach((p, i) => {{
                totalDelay = i * step;
                setTimeout(() => {{
                    addMarker(p.Latitude, p.Longitude, false, p.Username);
                }}, totalDelay);
            }});

            const verStartDelay = totalDelay + step;
            verData.forEach((p, i) => {{
                setTimeout(() => {{
                    addMarker(p.Latitude, p.Longitude, true, '專家驗證');
                }}, verStartDelay + (i * step));
            }});

            const totalCycleTime = verStartDelay + (verData.length * step) + 6000;
            setTimeout(startPlayback, totalCycleTime);
        }}

        function addMarker(lat, lon, isVerified, name) {{
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

    # Streamlit 元件高度設為 780 以容納內部的 750px 容器
    st.components.v1.html(html_content, height=780)

    st.sidebar.markdown(f"### 🌊 播放資訊")
    st.sidebar.write("● 模式：自動循環播放")
    st.sidebar.write("● 畫面：擴大高度版 (750px)")
    st.sidebar.write(f"● 總紀錄：{len(raw_data) + len(verified_data)} 筆")
    
else:
    st.warning("找不到 CSV 資料。")
