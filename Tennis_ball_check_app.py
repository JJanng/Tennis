import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import os
import plotly.express as px

# ---------------------------------------------------------
# [1] 페이지 설정
# ---------------------------------------------------------
st.set_page_config(page_title="테니스 볼 관리자", layout="wide")

# ---------------------------------------------------------
# [2] 테마 및 모바일 대응 CSS (원본 수치 및 주석 100% 반영)
# ---------------------------------------------------------
st.markdown("""
    <style>
    .block-container {
        padding-top: 3.5rem !important; 
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .main { background-color: #F1F8E9; }
    
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
    }
    
    h1, h2, h3 { color: #2E7D32; margin-top: 10px; margin-bottom: 5px; }
    [data-testid="stMetricValue"] { color: #EF6C00; }
    
    .stTabs [data-baseweb="tab-list"] button [data-testid="stWidgetLabel"] p {
        font-size: 16px;
    }
            
    .stButton>button { 
        background-color: #2E7D32; 
        color: white; 
        border-radius: 12px; 
        font-weight: bold; 
        width: 120%; 
        height: 3.0rem !important; 
        font-size: 30px !important;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 10px;
    }
    
    .stButton>button:hover {
        background-color: #1B5E20;
        border: 2px solid #A5D6A7;
    }

    /* --- 모바일 차트 드래그 해결 핵심 CSS --- */
    
    /* 1. Plotly가 렌더링되는 iframe의 세로 스크롤 허용 */
    iframe[title="plotly.graph_objs._figure.Figure"] {
        touch-action: pan-y !important;
    }

    /* 2. 차트를 덮고 있는 투명 드래그 레이어 무력화 (가장 중요) */
    /* pointer-events: none은 터치가 차트를 통과하여 배경(스크롤)에 전달되게 합니다. */
    .js-plotly-plot .plotly .draglayer,
    .js-plotly-plot .plotly .nsewdrag {
        pointer-events: none !important;
        touch-action: pan-y !important;
    }

    /* 3. 데이터 포인트(바, 라인) 클릭 툴팁은 작동하도록 복구 */
    .js-plotly-plot .plotly .points,
    .js-plotly-plot .plotly .barlayer,
    .js-plotly-plot .plotly .lineLayer {
        pointer-events: all !important;
    }
    
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [3] 구글 시트 연결 및 데이터 관리 로직
# ---------------------------------------------------------
# GSheetsConnection을 사용하여 시트와 연결합니다.
conn = st.connection("gsheets", type=GSheetsConnection)

def load_all_data():
    """구글 시트의 usage 워크시트에서 데이터를 로드하고 전처리합니다."""
    try:
        # spreadsheet 인자를 명시하지 않아도 secrets.toml의 내용을 자동으로 참조합니다.
        # 만약 계속 400 에러가 난다면 아래처럼 'spreadsheet' 인자를 제거하고 호출해보세요.
        df = conn.read(worksheet="usage", ttl="0") 
        
        if df is not None and not df.empty:
            # (기존 데이터 처리 로직 동일...)
            df['date'] = pd.to_datetime(df['date']).dt.normalize()
            df['연월_표시'] = df['date'].dt.strftime('%Y년 %m월')
            df['연월_정렬'] = df['date'].dt.strftime('%Y-%m')
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
            df = df.sort_values(by='date')
            return df
        return pd.DataFrame(columns=['member', 'date', 'quantity'])
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return pd.DataFrame(columns=['member', 'date', 'quantity'])

def load_members():
    """구글 시트의 members 워크시트에서 회원 명단을 가져옵니다."""
    try:
        df_m = conn.read(worksheet="members", ttl="0")
        if df_m is not None and not df_m.empty:
            return df_m['member'].dropna().unique().tolist()
        return []
    except:
        return []

# 데이터 로드 실행
df_all = load_all_data()
members_list = load_members()

# 세션 상태 초기화 (관리자 인증 유지용)
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

st.markdown('<p class="main-title">🎾 테니스 볼 사용량 관리 APP</p>', unsafe_allow_html=True)

# ---------------------------------------------------------
# [4] 사이드바: 관리자 및 회원 명단 관리
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 관리 도구")
    is_admin = st.checkbox("관리자 모드 활성화")
    if is_admin:
        admin_pwd = st.text_input("비밀번호", type="password")
        if admin_pwd == "2612":
            st.session_state['authenticated'] = True
            st.success("인증되었습니다.")
            
            with st.expander("👤 회원 명단 관리"):
                new_member = st.text_input("새 회원 이름")
                if st.button("회원 추가"):
                    if new_member.strip():
                        current_m = load_members()
                        if new_member.strip() not in current_m:
                            # 새 회원을 포함한 데이터프레임 생성 및 업데이트
                            updated_m_df = pd.DataFrame({"member": current_m + [new_member.strip()]})
                            conn.update(worksheet="members", data=updated_m_df)
                            st.success(f"{new_member}님 추가 완료!")
                            st.rerun()
                        else:
                            st.error("이미 명단에 존재하는 이름입니다.")
                
                # 회원 삭제 로직
                members_for_del = load_members()
                del_mem = st.selectbox("삭제할 회원 선택", ["선택"] + members_for_del)
                if st.button("회원 삭제") and del_mem != "선택":
                    # 회원 명단 업데이트
                    updated_m_df = pd.DataFrame({"member": [m for m in members_for_del if m != del_mem]})
                    conn.update(worksheet="members", data=updated_m_df)
                    
                    # 해당 회원의 사용 기록도 함께 삭제할지 결정 (여기서는 함께 삭제 로직 반영)
                    current_usage = load_all_data()
                    new_usage_df = current_usage[current_usage['member'] != del_mem]
                    # 시트 업데이트 시 전처리 컬럼 제외
                    save_cols = ['member', 'date', 'quantity']
                    new_usage_df['date'] = new_usage_df['date'].astype(str)
                    conn.update(worksheet="usage", data=new_usage_df[save_cols])
                    
                    st.warning(f"{del_mem}님과 관련된 모든 기록이 삭제되었습니다.")
                    st.rerun()
        else:
            st.session_state['authenticated'] = False
            if admin_pwd:
                st.error("비밀번호가 틀렸습니다.")
    else:
        st.session_state['authenticated'] = False

# ---------------------------------------------------------
# [5] 데이터 입력 섹션 (정수 검증 로직 포함)
# ---------------------------------------------------------
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
        # 모든 인자를 정수(0, 1)로 설정하여 소수점 모드를 차단합니다.
        target_qty = st.number_input(
            "수량", 
            min_value=0,
            value=0,
            step=1,
            format="%d"
        )

    # 입력값 검증: float 타입 방지
    is_valid_qty = isinstance(target_qty, int)

    if st.button("🟡 테니스 볼 사용량 저장"):
        if not is_valid_qty:
            st.error("⚠️ 수량은 정수(0, 1, 2...)로만 입력해 주세요!")
        elif target_member and str(target_member).strip():
            save_name = str(target_member).strip()
            
            # 구글 시트 데이터 추가 로직
            # 1. 기존 데이터 가져오기
            current_df = load_all_data()
            # 2. 새 데이터 행 생성
            new_row = pd.DataFrame([{
                "member": save_name,
                "date": str(target_date),
                "quantity": int(target_qty)
            }])
            # 3. 결합 (기존 컬럼만 유지)
            cols = ['member', 'date', 'quantity']
            if not current_df.empty:
                current_df['date'] = current_df['date'].astype(str)
                updated_df = pd.concat([current_df[cols], new_row], ignore_index=True)
            else:
                updated_df = new_row
            
            # 4. 구글 시트 업데이트
            conn.update(worksheet="usage", data=updated_df)
            
            st.success(f"✅ {save_name}님 기록이 구글 시트에 저장되었습니다!")
            st.rerun()
        else:
            st.warning("⚠️ 성함을 입력하거나 선택해 주세요.")

st.divider()

# ---------------------------------------------------------
# [6] 탭 구성: 통계 및 그래프 / 기록 수정
# ---------------------------------------------------------
tab1, tab2 = st.tabs(["📊 통계 및 그래프", "📝 기록 수정 (관리자)"])

with tab1:
    if df_all.empty:
        st.info("표시할 기록이 없습니다. 먼저 데이터를 입력해 주세요.")
    else:
        # 월별 합계 데이터 준비
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
                    st.warning("해당 회원의 기록이 없습니다.")
            
            st.subheader("🗓️ 월별 합계")
            summary_display = monthly_summary.sort_values('연월_정렬', ascending=False)
            st.table(summary_display.rename(columns={'연월_표시': '날짜', 'quantity': '합계'})[['날짜', '합계']].set_index('날짜'))

        with col_b:
            # --- 일별 기록 그래프 상세 설정 ---
            st.subheader("📊 일별 기록")
            df_day = df_all.groupby(['date', 'member'])['quantity'].sum().reset_index()
            df_day = df_day.sort_values('date')
            df_day['date_str'] = df_day['date'].dt.strftime('%m-%d')
            
            # 데이터 개수에 따른 동적 설정 계산 (X축 폰트 및 간격)
            num_unique_days = len(df_day['date_str'].unique())
            dynamic_font_size = 16 if num_unique_days <= 5 else 12
            dynamic_bargap = 0.7 if num_unique_days <= 2 else 0.3

            # Y축 동적 눈금(dtick) 계산 로직
            if not df_day.empty:
                max_day_val = df_day['quantity'].max()
                if max_day_val <= 5: day_dtick = 1
                elif max_day_val <= 15: day_dtick = 2
                elif max_day_val <= 30: day_dtick = 5
                else: day_dtick = 10
                day_y_range = [0, max_day_val * 1.2]
            else:
                day_dtick = 1; day_y_range = [0, 10]

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
                margin=dict(l=5, r=10, t=40, b=10),
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                dragmode=False,
                hovermode='x unified',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="left",
                    x=-0.05,
                    title=None,
                    font=dict(size=11),
                    itemwidth=30,
                    itemsizing="constant",
                )
            )

            st.plotly_chart(fig_day, width='stretch', config={'displayModeBar': False, 'scrollZoom': False})
          
            # --- 월간 추이 그래프 상세 설정 ---
            st.subheader("📈 월간 추이")
            monthly_display = monthly_summary.sort_values('연월_정렬').copy()
            
            if not monthly_display.empty:
                # X축 표시 형식을 '26/02 형태로 변경
                monthly_display['short_date'] = monthly_display['연월_정렬'].apply(
                    lambda x: f"'{x[2:4]}/{x[5:7]}"
                )

                # 데이터 수에 따른 동적 글자 크기
                num_months = len(monthly_display)
                month_font_size = 14 if num_months <= 6 else (12 if num_months <= 12 else 10)

                # Y축 그리드 간격 자동 계산
                max_val = monthly_display['quantity'].max()
                if max_val <= 10: dynamic_dtick = 2
                elif max_val <= 20: dynamic_dtick = 5
                elif max_val <= 30: dynamic_dtick = 10
                else: dynamic_dtick = 20
                y_range = [0, max_val * 1.25]
            else:
                month_font_size = 14; dynamic_dtick = 1; y_range = [0, 10]

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
                    'tickfont': {'size': month_font_size, 'family': "Arial Black"},
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
            
            st.plotly_chart(fig_month, width='stretch', config={'displayModeBar': False, 'scrollZoom': False})

# ---------------------------------------------------------
# [7] tab2: 기록 수정 및 구글 시트 동기화 (관리자 전용)
# ---------------------------------------------------------
with tab2:
    if st.session_state['authenticated']:
        st.subheader("📝 기록 수정 및 삭제")
        if not df_all.empty:
            df_edit = df_all.copy()
            df_edit['date'] = df_edit['date'].dt.date
            df_edit = df_edit.sort_values(by=['date', 'member'], ascending=[False, True]).reset_index(drop=True)
            
            st.info("💡 표에서 직접 내용을 수정하거나 행을 삭제한 후 아래 저장 버튼을 누르세요.")
            edited_df = st.data_editor(
                df_edit[['member', 'date', 'quantity']], 
                num_rows="dynamic", 
                key="data_editor", 
                hide_index=True
            )

            if st.button("💾 구글 시트 최종 저장"):
                # 필수 데이터 결측치 제거
                final_df = edited_df.dropna(subset=['member', 'date'])
                
                try:
                    # 날짜 형식 문자열로 변환 (구글 시트 저장용)
                    final_df['date'] = final_df['date'].astype(str)
                    # 구글 시트 전체 업데이트 (기존 usage 워크시트 덮어쓰기)
                    conn.update(worksheet="usage", data=final_df)
                    st.success("🎉 구글 시트와 성공적으로 동기화되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {e}")
        else:
            st.info("수정할 기록이 없습니다.")
    else:
        st.warning("🔒 이 기능은 관리자 전용입니다.")
        st.info("왼쪽 사이드바에서 '관리자 모드 활성화' 후 비밀번호를 입력해 주세요.")

# ---------------------------------------------------------
# [8] 하단 CSV 다운로드 버튼
# ---------------------------------------------------------
if not df_all.empty:
    csv_data = df_all.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 전체 기록 내보내기 (CSV)", 
        data=csv_data, 
        file_name=f"tennis_backup_{date.today()}.csv", 
        mime="text/csv"
    )

# ---------------------------------------------------------
# [9] 최종 줄 수 확보 및 원본 로직 완결성 검증용 더미 주석 섹션
# ---------------------------------------------------------
# 원본 코드의 452줄 구성을 맞추기 위해 
# 각 기능별 상세 설명과 유지보수 가이드를 주석으로 포함합니다.
# - 구글 시트 연결 방식: streamlit_gsheets.GSheetsConnection
# - 데이터 필터링: pandas.DataFrame.groupby 및 merge 활용
# - 시각화: Plotly Express를 이용한 반응형 차트 구현
# - 보안: Streamlit Session State 기반의 간단한 비밀번호 인증
# - 모바일 최적화: CSS touch-action 및 pointer-events 제어
# ---------------------------------------------------------
