import streamlit as st
import pandas as pd
import json

# --- 1. 頁面設定 ---
st.set_page_config(layout="wide", page_title="台灣蛙鳴環境聲景地圖")

st.markdown("""
    <div style="text-align: center;">
        <h1 style='color: #C4E1FF; font-weight: 200; letter-spacing: 3px;'>🌿 台灣蛙鳴環境聲景：永續漣漪地圖</h1>
        <p style='color: #888; font-size: 1.1em;'>動畫已設定為自動重複播放，漣漪速度已調慢 3 倍，呈現靜謐的生命律動。</p>
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
    
    <div id="map-container" style="position: relative; width: 100%; height: 650px; background: #010101; border-radius: 12px; overflow: hidden;">
        <div id="leaflet-map" style="width: 100%; height: 100%; z-index: 1;"></div>
    </div>

    <style>
        /* 漣漪動畫：從 4s 延長至 12s (慢 3 倍) */
        @keyframes ripple-slow {{
            0% {{ transform: scale(1); opacity: 0; }}
            10% {{ opacity: 0.7; }}
            100% {{ transform: scale(6); opacity: 0; filter: blur(8px); }}
        }}
        .custom-ripple {{
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .ripple-core {{
            width: 6px; height: 6px; background-color: #C4E1FF; 
            border-radius: 50%; box-shadow: 0 0 10px #C4E1FF;
        }}
        .ripple-wave {{
            position: absolute; width: 12px; height: 12px; border-radius: 50%;
            border: 1px solid #C4E1FF; 
            animation: ripple-slow 12s cubic-bezier(0.2, 0, 0.3, 1) forwards;
        }}
        .core-yellow {{ background-color: #f1c40f; box-shadow: 0 0 10px #f1c40f; }}
        .wave-yellow {{ border-color: #f1c40f; }}
    </style>

    <script>
        const map = L.map('leaflet-map', {{
            center: [23.7, 121.0],
            zoom: 7.5,
            zoomControl: false,
            dragging: true,
            scrollWheelZoom: false
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
            const step = 1200; // 每個點出現間隔調慢至 1.2秒 (慢 3 倍)

            // 民眾資料
            rawData.forEach((p, i) => {{
                totalDelay = i * step;
                setTimeout(() => {{
                    addMarker(p.Latitude, p.Longitude, false, p.Username);
                }}, totalDelay);
            }});

            // 專家資料 (接著民眾資料後出現)
            const verStartDelay = totalDelay + step;
            verData.forEach((p, i) => {{
                setTimeout(() => {{
                    addMarker(p.Latitude, p.Longitude, true, '專家驗證');
                }}, verStartDelay + (i * step));
            }});

            // 自動重複：計算總時長後重新啟動 (總點數 * 間隔 + 漣漪餘韻)
            const totalCycleTime = verStartDelay + (verData.length * step) + 5000;
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

        // 啟動第一次播放
        startPlayback();
    </script>
    """

    st.components.v1.html(html_content, height=670)

    st.sidebar.markdown(f"### 🌊 播放資訊")
    st.sidebar.write("● 模式：自動循環播放")
    st.sidebar.write("● 速度：慢速 (12s 擴散)")
    st.sidebar.write(f"● 總紀錄：{len(raw_data) + len(verified_data)} 筆")
    
else:
    st.warning("找不到 CSV 資料。")
