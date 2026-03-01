import streamlit as st
import pandas as pd
import json

# --- 1. 頁面與全螢幕樣式設定 ---
st.set_page_config(layout="wide", page_title="台灣蛙鳴環境聲景")

# 強制將所有邊距、標題、頁尾歸零，呈現極簡純黑劇院感
st.markdown("""
    <style>
        .main > div { padding: 0 !important; }
        iframe { border: none !important; }
        .stApp { background-color: #010101; }
        header, footer, #MainMenu { visibility: hidden; }
        /* 移除標題區域 */
        [data-testid="stHeader"] { display: none; }
        /* 確保全視窗滿版 */
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
            # 確保所有有效資料都被載入並排序
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
        /* 漣漪動畫：慢速且帶有平滑淡化 */
        @keyframes ripple-spread {{
            0% {{ transform: scale(1); opacity: 0; }}
            10% {{ opacity: 0.6; }}
            100% {{ transform: scale(8); opacity: 0; filter: blur(10px); }}
        }}

        .custom-ripple {{
            position: relative; display: flex; justify-content: center; align-items: center;
        }}

        .ripple-core {{
            width: 5px; height: 5px; background-color: #C4E1FF; 
            border-radius: 50%; box-shadow: 0 0 10px #C4E1FF;
            z-index: 10;
        }}

        /* 多重圓圈：一圈一圈擴散 */
        .ripple-wave {{
            position: absolute; width: 12px; height: 12px; border-radius: 50%;
            border: 1px solid #C4E1FF; 
            animation: ripple-spread 10s cubic-bezier(0.2, 0, 0.3, 1) forwards;
            pointer-events: none;
        }}

        .core-yellow {{ background-color: #f1c40f; box-shadow: 0 0 10px #f1c40f; }}
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
            const step = 1500; // 每個資料點出現的間隔

            // 合併所有資料點進行完整展示
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

            // 確保所有漣漪擴散完畢後再重複 (總點數 * 間隔 + 動畫長度)
            const cycleBuffer = 12000; 
            setTimeout(startPlayback, totalDelay + cycleBuffer);
        }}

        function addMultiRippleMarker(lat, lon, isVer) {{
            // 建立核心點與「三層」漣漪，達到一圈一圈的效果
            const colorClass = isVer ? 'wave-yellow' : '';
            const coreClass = isVer ? 'core-yellow' : '';
            
            const icon = L.divIcon({{
                html: `<div class="custom-ripple">
                        <div class="ripple-core ${{coreClass}}"></div>
                        <div class="ripple-wave ${{colorClass}}" style="animation-delay: 0s;"></div>
                        <div class="ripple-wave ${{colorClass}}" style="animation-delay: 2s;"></div>
                        <div class="ripple-wave ${{colorClass}}" style="animation-delay: 4s;"></div>
                       </div>`,
                className: '',
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            }});
            L.marker([lat, lon], {{icon: icon}}).addTo(markerLayer);
        }}

        // 初次啟動
        setTimeout(startPlayback, 1000);
    </script>
    """

    st.components.v1.html(html_content, height=1200) # 設定大高度以支援 100vh 展示

else:
    st.error("無法讀取 CSV 資料，請確認 GitHub 目錄檔案。")
