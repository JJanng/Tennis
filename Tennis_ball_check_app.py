import streamlit as st
import pandas as pd
from datetime import date
import os
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
import json
from google.oauth2 import service_account

sa_json_str = st.secrets["GCP"]["service_account"].strip()
sa_info = json.loads(sa_json_str)
credentials = service_account.Credentials.from_service_account_info(sa_info)

print("GCP project:", sa_info["project_id"])  # 화면에는 안 뜸

# =========================================================
# [1] 페이지 설정 및 레이아웃 최적화
# =========================================================
st.set_page_config(
    page_title="테니스 볼 사용량 관리자", 
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# [2] 테마 및 모바일 대응 맞춤형 CSS (원본 디테일 100%)
# =========================================================
st.markdown("""
    <style>
    /* 전체 배경색 및 컨테이너 여백 설정 */
    .block-container {
        padding-top: 3.5rem !important; 
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .main { background-color: #F1F8E9; }
    
    /* 메인 타이틀 스타일 */
    .main-title {
        font-size: 22px !important;
        color: #2E7D32;
        font-weight: bold;
        text-align: center;
        margin-top: 0px;
        margin-bottom: 25px;
        line-height: 1.2;
        background: #E8F5E9;
        padding: 15px;
        border-radius: 15px;
        border: 2px solid #A5D6A7;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    
    /* 헤더 및 메트릭 텍스트 색상 */
    h1, h2, h3 { color: #2E7D32; margin-top: 10px; margin-bottom: 5px; }
    [data-testid="stMetricValue"] { color: #EF6C00; font-weight: bold; }
    
    /* 탭 메뉴 폰트 크기 조정 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stWidgetLabel"] p {
        font-size: 16px;
        font-weight: 600;
    }
            
    /* 입력 버튼 스타일링 (모바일 클릭 편의성) */
    .stButton>button { 
        background-color: #2E7D32; 
        color: white; 
        border-radius: 12px; 
        font-weight: bold; 
        width: 100%; 
        height: 3.5rem !important; 
        font-size: 24px !important;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 10px;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #1B5E20;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: translateY(-2px);
    }

    /* --- [중요] 모바일 차트 스크롤 및 터치 레이어 해결 --- */
    /* 1. Plotly iframe의 세로 스크롤(터치 액션) 허용 */
    iframe[title="plotly.graph_objs._figure.Figure"] {
        touch-action: pan-y !important;
    }

    /* 2. 차트 드래그 레이어 무력화: 모바일에서 차트 위를 밀어도 페이지 스크롤이 되도록 함 */
    .js-plotly-plot .plotly .draglayer,
    .js-plotly-plot .plotly .nsewdrag {
        pointer-events: none !important;
        touch-action: pan-y !important;
    }

    /* 3. 툴팁 및 데이터 포인트 클릭 기능은 유지 */
    .js-plotly-plot .plotly .points,
    .js-plotly-plot .plotly .barlayer,
    .js-plotly-plot .plotly .lineLayer {
        pointer-events: all !important;
    }
    
    /* 사이드바 스타일 커스텀 */
    [data-testid="stSidebar"] {
        background-color: #E8F5E9;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# [3] 구글 시트 엔진 및 데이터 핸들링 로직 (FIXED VERSION)
# =========================================================

@st.cache_resource
def get_connection():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    # 🔹 Secrets에서 GCP JSON 문자열 읽기
    sa_json_str = st.secrets["GCP"]["service_account"].strip()
    sa_info = json.loads(sa_json_str)

    # 🔹 파일 없이 credentials 생성
    creds = service_account.Credentials.from_service_account_info(sa_info, scopes=scope)

    # 🔹 Gspread 클라이언트 생성
    client = gspread.authorize(creds)

    # 🔹 스프레드시트 열기
    spreadsheet = client.open_by_key("17aJtYUZVC8K-zan4q9LM-5vApbMZA2yZH-uVUB9978w")

    return spreadsheet

# 🔹 사용
conn = get_connection()


@st.cache_data(ttl=60)
def load_all_data():
    try:
        sh = conn.worksheet("usage")
        data = sh.get_all_records()
        df = pd.DataFrame(data)

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.normalize()
            df = df.dropna(subset=['date'])

            df['연월_표시'] = df['date'].dt.strftime('%Y년 %m월')
            df['연월_정렬'] = df['date'].dt.strftime('%Y-%m')

            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0).astype(int)

        return df

    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return pd.DataFrame(columns=['member', 'date', 'quantity'])


@st.cache_data(ttl=300)
def load_members():
    try:
        sh = conn.worksheet("members")
        data = sh.get_all_records()
        df = pd.DataFrame(data)

        if not df.empty:
            return sorted(df['member'].dropna().unique().tolist())

        return []

    except Exception as e:
        st.warning(f"회원 목록 로드 실패: {e}")
        return []


# 데이터 로드 실행
df_all = load_all_data()
members_list = load_members()


# 세션 상태 초기화
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False


# 앱 헤더 출력
st.markdown('<p class="main-title">🎾 테니스 볼 사용량 관리 시스템</p>', unsafe_allow_html=True)

# =========================================================
# [4] 사이드바: 관리자 도구 및 마스터 데이터 관리
# =========================================================
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    is_admin = st.checkbox("관리자 권한 활성화", help="기록 삭제 및 회원 관리를 위해 체크하세요.")
    
    if is_admin:
        admin_pwd = st.text_input("관리자 비밀번호", type="password")
        if admin_pwd == "2612":
            st.session_state['authenticated'] = True
            st.success("🔓 관리자 인증 성공")
            
            # --- 회원 명단 관리 섹션 ---
            with st.expander("👤 회원 명단 수정", expanded=False):
                new_member_name = st.text_input("신규 등록 성함", placeholder="예: 홍길동")
                if st.button("회원 추가하기", use_container_width=True):
                    if new_member_name.strip():
                        current_m = load_members()
                        if new_member_name.strip() not in current_m:
                            # 새 회원을 포함한 데이터프레임 구성
                            updated_m_df = pd.DataFrame({"member": current_m + [new_member_name.strip()]})
                            # [PATCH] 마스터 테이블은 반드시 update(덮어쓰기) 수행
                            spreadsheet = get_connection()
                            members_ws = spreadsheet.worksheet("members")

                            members_ws.clear()

                            members_ws.update(
                                [updated_m_df.columns.values.tolist()] +
                                updated_m_df.values.tolist()
                            )

                            st.cache_data.clear() # 캐시 강제 무효화
                            st.success(f"{new_member_name}님 등록 완료!")
                            st.rerun()
                        else:
                            st.error("이미 등록된 이름입니다.")
                
                st.divider()
                
                # 회원 삭제 로직
                members_for_del = load_members()
                selected_del_mem = st.selectbox("영구 삭제할 이름", ["선택"] + members_for_del)
                if st.button("회원 정보 삭제", type="secondary", use_container_width=True):
                    if selected_del_mem != "선택":
                        # 1. 명단에서 제거
                        updated_m_df = pd.DataFrame({"member": [m for m in members_for_del if m != selected_del_mem]})
                        spreadsheet = get_connection()
                        members_ws = spreadsheet.worksheet("members")

                        members_ws.clear()

                        members_ws.update(
                            [updated_m_df.columns.values.tolist()] +
                            updated_m_df.values.tolist()
                        )

                        # 2. [중요] 사용 기록 시트에서도 해당 데이터 제거
                        spreadsheet = get_connection()
                        usage_ws = spreadsheet.worksheet("usage")

                        data = usage_ws.get_all_records()
                        df_usage = pd.DataFrame(data)

                        filtered_usage = df_usage[df_usage['member'] != selected_del_mem]

                        usage_ws.clear()
                        usage_ws.update(
                            [filtered_usage.columns.values.tolist()] +
                            filtered_usage.values.tolist()
                        )
                      
                        st.cache_data.clear()
                        st.warning(f"{selected_del_mem}님 관련 모든 정보 파기 완료")
                        st.rerun()
        else:
            st.session_state['authenticated'] = False
            if admin_pwd:
                st.error("🔑 비밀번호가 일치하지 않습니다.")
    else:
        st.session_state['authenticated'] = False

# =========================================================
# [5] 데이터 입력 인터페이스 (메인 화면 상단)
# =========================================================
st.subheader("📝 사용량 기록하기")
with st.container():
    input_mode = st.radio("입력 방식 선택", ["기존 회원 선택", "신규/직접 입력"], horizontal=True)
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if input_mode == "기존 회원 선택":
            target_member = st.selectbox("이름 검색", members_list, index=None, placeholder="성함을 검색하세요")
        else:
            target_member = st.text_input("성함 입력", placeholder="명단에 없는 이름 입력")

    with col2:
        target_date = st.date_input("날짜", date.today())

    with col3:
        # 모든 인자를 정수(0, 1)로 설정하여 소수점 모드(0.0)를 완전히 차단합니다.
        target_qty = st.number_input(
            "수량", 
            min_value=0,    # 0.0이 아닌 0으로 설정
            value=0,        # 초기 표시값을 0으로 설정
            step=1,         # 증감 단위를 1로 설정
            format="%d"     # 표시 형식을 정수(%d)로 강제
        )

    # --- 입력값 검증 로직 추가 ---
    # 사용자가 타이핑 중 소수점 등을 섞어 넣으면 float로 인식될 수 있으므로 체크합니다.
    is_valid_qty = isinstance(target_qty, int)

    if st.button("🟡 테니스 볼 사용량 저장"):
        if not is_valid_qty:
            st.error("⚠️ 수량은 정수(0, 1, 2...)로만 입력해 주세요!")
        elif target_member and str(target_member).strip():
            save_name = str(target_member).strip()
            spreadsheet = get_connection()
            usage_ws = spreadsheet.worksheet("usage")

            usage_ws.append_row([
                save_name,
                str(target_date),
                int(target_qty)
            ])

            st.cache_data.clear()
            st.success(f"✅ {save_name}님 저장 완료!")
            st.rerun()
        else:
            st.warning("⚠️ 성함을 입력하거나 선택해 주세요.")

st.divider()

# --- 탭 구성 ---
tab1, tab2 = st.tabs(["📊 통계 및 그래프", "📝 기록 수정 (관리자)"])

with tab1:
    if df_all.empty:
        st.info("기록이 없습니다.")
    else:
        monthly_summary = df_all.groupby(['연월_정렬', '연월_표시'])['quantity'].sum().reset_index()
        monthly_summary = monthly_summary.sort_values('연월_정렬')
        
        col_a, col_b = st.columns([1, 2])
        with col_a:
            st.subheader("👤 개인 통계")
            view_mode = st.radio("조회 방식", ["회원 선택", "직접 입력"], horizontal=True, key="view_mode")
            if view_mode == "회원 선택":
                stat_member = st.selectbox("조회할 이름", members_list, index=None, placeholder="검색...", key="s_select")
            else:
                stat_member = st.text_input("조회할 이름 입력", placeholder="이름 입력", key="s_input")
            
            if stat_member and str(stat_member).strip():
                df_stat = df_all[df_all['member'] == str(stat_member).strip()]
                if not df_stat.empty:
                    current_month = date.today().strftime('%Y-%m')
                    this_month_qty = df_stat[df_stat['연월_정렬'] == current_month]['quantity'].sum()
                    total_qty = df_stat['quantity'].sum()
                    st.metric(f"{stat_member}님 이번 달", f"{this_month_qty} 개")
                    st.metric("전체 누적", f"{total_qty} 개")
                else:
                    st.warning("기록이 없습니다.")
            
            st.subheader("🗓️ 월별 합계")
            summary_display = monthly_summary.sort_values('연월_정렬', ascending=False)
            st.table(summary_display.rename(columns={'연월_표시': '날짜', 'quantity': '합계'})[['날짜', '합계']].set_index('날짜'))

with col_b:
            st.subheader("📊 일별 기록")
            df_day = df_all.groupby(['date', 'member'])['quantity'].sum().reset_index()
            df_day = df_day.sort_values('date')
            df_day['date_str'] = df_day['date'].dt.strftime('%m-%d')
            
            # 데이터 개수에 따른 동적 설정 계산 (X축)
            num_unique_days = len(df_day['date_str'].unique())
            dynamic_font_size = 16 if num_unique_days <= 5 else 12
            dynamic_bargap = 0.7 if num_unique_days <= 2 else 0.3

            # --- Y축 동적 눈금(dtick) 계산 추가 ---
            if not df_day.empty:
                max_day_val = df_day['quantity'].max()
                if max_day_val <= 5:
                    day_dtick = 1
                elif max_day_val <= 15:
                    day_dtick = 2
                elif max_day_val <= 30:
                    day_dtick = 5
                else:
                    day_dtick = 10
                day_y_range = [0, max_day_val * 1.2] # 상단 여백 확보
            else:
                day_dtick = 1
                day_y_range = [0, 10]

            fig_day = px.bar(df_day, x='date_str', y='quantity', color='member', 
                            barmode='group', text='quantity', height=320)
            
            fig_day.update_traces(
                textposition='outside', 
                textfont=dict(size=14, family="Arial Black", color="black"),
                cliponaxis=False
            )
            
            fig_day.update_layout(
                    xaxis_title=None, 
                    yaxis_title=None,
                    xaxis={
                        'type': 'category', 
                        'fixedrange': True,
                        'tickfont': {'size': dynamic_font_size, 'family': "Arial Black"}
                    },
                    yaxis={
                        'fixedrange': True, 
                        'dtick': day_dtick,
                        'range': day_y_range,
                        'gridcolor': '#DCDCDC',
                        'showgrid': True,
                        'title': None
                    },
                    bargap=dynamic_bargap,
                    margin=dict(l=5, r=10, t=40, b=10), # 왼쪽 여백 축소로 공간 확보
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',
                    dragmode=False,
                    hovermode='x unified',
                    showlegend=True,
                    # --- 범례(Legend) 설정 수정 ---
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="left",
                        x=-0.05,            # 왼쪽으로 살짝 더 밀어서 공간을 더 확보 (음수값 활용)
                        title=None,
                        font=dict(size=11), # 글자 크기를 10으로 줄여 잘림 방지
                        
                        # 고정 비율(entrywidth) 대신 가로 간격을 직접 조절합니다.
                        itemwidth=30,       # 범례 아이콘(색상박스) 너비 축소
                        itemsizing="constant",
                        
                        # 항목 사이의 여백을 조절 (열을 늘리는 핵심)
                        # entrywidth를 지우면 이름 길이에 맞춰 다닥다닥 붙게 됩니다.
                    )
                )

            st.plotly_chart(
                fig_day, 
                width='stretch', 
                config={'displayModeBar': False, 'scrollZoom': False}
            )
          
            st.subheader("📈 월간 추이")
            # 데이터 정렬 확인 및 X축 형식 변경
            monthly_display = monthly_summary.sort_values('연월_정렬').copy()
            
            if not monthly_display.empty:
                # X축 표시 형식을 '26/02 형태로 변경
                # '연월_정렬'은 '2026-02' 형식이므로 이를 슬라이싱하여 변환합니다.
                monthly_display['short_date'] = monthly_display['연월_정렬'].apply(
                    lambda x: f"'{x[2:4]}/{x[5:7]}"
                )

                # 데이터 수에 따른 동적 글자 크기 계산
                num_months = len(monthly_display)
                if num_months <= 6:
                    month_font_size = 14
                elif num_months <= 12:
                    month_font_size = 12
                else:
                    month_font_size = 10

                # 1. 최대 수량에 따른 적절한 그리드 간격(dtick) 계산
                max_val = monthly_display['quantity'].max()
                if max_val <= 10: dynamic_dtick = 2
                elif max_val <= 20: dynamic_dtick = 5
                elif max_val <= 30: dynamic_dtick = 10
                else: dynamic_dtick = 20
                
                y_range = [0, max_val * 1.25]
            else:
                month_font_size = 14
                dynamic_dtick = 1
                y_range = [0, 10]

            # x축을 새로 만든 'short_date'로 설정
            fig_month = px.line(monthly_display, x='short_date', y='quantity', 
                                markers=True, text='quantity', height=320)
            
            fig_month.update_traces(
                line_color='#2E7D32', 
                line_width=3,
                marker=dict(size=12, symbol="circle", color="#2E7D32", line=dict(width=2, color="white")), 
                textposition="top center", 
                cliponaxis=False,
                textfont=dict(size=15, family="Arial Black", color="black")
            )
            
            fig_month.update_layout(
                xaxis_title=None, 
                yaxis_title=None,
                xaxis={
                    'type': 'category', 
                    'fixedrange': True,
                    'tickfont': {'size': month_font_size, 'family': "Arial Black"}, # 동적 폰트 적용
                    'showgrid': False,
                    'showline': True,
                    'linewidth': 2,
                    'linecolor': '#A5D6A7',
                    'mirror': True
                },
                yaxis={
                    'fixedrange': True, 
                    'showgrid': True,
                    'dtick': dynamic_dtick,
                    'gridcolor': '#DCDCDC',
                    'gridwidth': 1,
                    'griddash': 'dot',
                    'zeroline': True,
                    'zerolinecolor': '#A5D6A7',
                    'showline': True,
                    'linewidth': 2,
                    'linecolor': '#A5D6A7',
                    'mirror': True,
                    'range': y_range,
                    'title': None
                },
                margin=dict(l=5, r=10, t=60, b=10),
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(255,255,255,0.5)',
                dragmode=False,
                hovermode='x unified'
            )
            
            st.plotly_chart(
                fig_month, 
                width='stretch', 
                config={'displayModeBar': False, 'scrollZoom': False}
            )

with tab2:
    if st.session_state.get('authenticated', False):
        st.subheader("📝 기록 수정 및 삭제")
        
        if not df_all.empty:
            # 원본 복사 및 정렬
            df_edit = df_all.copy()
            df_edit['date'] = df_edit['date'].dt.date  # datetime → date
            df_edit = df_edit.sort_values(by=['date', 'member'], ascending=[False, True]).reset_index(drop=True)

            st.info("💡 표에서 직접 내용을 수정하거나 행을 삭제한 후 '💾 변경사항 최종 저장' 버튼을 누르세요.")
            
            # 데이터 에디터
            edited_df = st.data_editor(
                df_edit[['member', 'date', 'quantity']],
                num_rows="dynamic",
                key="data_editor",
                hide_index=True
            )

            if st.button("💾 변경사항 최종 저장"):
                final_df = edited_df.dropna(subset=['member', 'date'])

                if final_df.empty:
                    st.warning("⚠️ 저장할 데이터가 없습니다.")
                else:
                    try:
                        # Gspread 연결
                        spreadsheet = get_connection()
                        worksheet = spreadsheet.sheet1

                        # 기존 데이터 삭제
                        worksheet.clear()

                        # 저장용 데이터 처리
                        save_df = final_df[['member', 'date', 'quantity']].copy()
                        save_df['date'] = save_df['date'].astype(str)

                        # 전체 데이터 업데이트
                        worksheet.update([save_df.columns.values.tolist()] + save_df.values.tolist())

                        # 캐시 무효화
                        st.cache_data.clear()

                        # 🔹 최신 데이터 재로드
                        df_all_new = load_all_data()

                        # 🔹 기존 전역 df_all 덮어쓰기
                        df_all = df_all_new.copy()

                        st.success("✅ 데이터베이스 업데이트 완료! 차트 및 테이블이 갱신됩니다.")

                    except Exception as e:
                        st.error(f"❌ 데이터베이스 저장 중 오류가 발생했습니다: {e}")
        else:
            st.info("수정할 기록이 없습니다.")
    else:
        st.warning("🔒 이 기능은 관리자 전용입니다.")
        st.info("왼쪽 사이드바에서 '관리자 모드 활성화' 후 비밀번호를 입력해 주세요.")


# 하단 다운로드 버튼 (df_all이 정의되어 있으므로 오류 없이 작동)
if not df_all.empty:
    csv_data = df_all.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 전체 기록 내보내기 (CSV)", data=csv_data, file_name=f"tennis_backup_{date.today()}.csv", mime="text/csv")
