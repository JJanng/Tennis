import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import os
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title="테니스 볼 관리자", layout="wide")

# 테마 및 모바일 대응 CSS
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
        
        /* 버튼 높이 조절 (기존 3.5rem -> 3.0rem으로 축소) */
        height: 3.0rem !important; 
        
        /* 글자 크기 조절 (기존 18px -> 30px로 확대) */
        font-size: 30px !important;
        
        /* 글자가 버튼 중앙에 잘 오도록 정렬 */
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 10px;
    }
    
    /* 버튼에 마우스를 올렸을 때 효과 (선택 사항) */
    .stButton>button:hover {
        background-color: #1B5E20;
        border: 2px solid #A5D6A7;
    }
            
    /* 기존 CSS 안에 추가 */
    iframe[title="plotly.graph_objs._figure.Figure"] {
        touch-action: pan-y !important;
    }

    .js-plotly-plot .plotly .nsewdrag {
        touch-action: pan-y !important;
    }
    /* 차트 영역 자체에서 발생하는 모든 터치 간섭을 최소화 */
    .js-plotly-plot .plotly .draglayer {
        pointer-events: all;
        touch-action: pan-y !important;
    }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ballusage.db"

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY AUTOINCREMENT, member TEXT UNIQUE)")
    cur.execute("CREATE TABLE IF NOT EXISTS usage (id INTEGER PRIMARY KEY AUTOINCREMENT, member TEXT NOT NULL, date TEXT NOT NULL, quantity INTEGER)")
    conn.commit()
    conn.close()

def load_all_data():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM usage", conn)
    conn.close()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date']).dt.normalize()
        df['연월_표시'] = df['date'].dt.strftime('%Y년 %m월')
        df['연월_정렬'] = df['date'].dt.strftime('%Y-%m')
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
        df = df.sort_values(by='date')
    return df

def load_members():
    conn = get_connection()
    members = [m[0] for m in conn.execute("SELECT member FROM members ORDER BY member").fetchall()]
    conn.close()
    return members

# DB 초기화 및 데이터 로드 (핵심: 코드 상단에서 먼저 정의)
init_db()
df_all = load_all_data()
members_list = load_members()

# 세션 상태 초기화 (관리자 인증 유지용)
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

st.markdown('<p class="main-title">🎾 테니스 볼 사용량 관리 APP</p>', unsafe_allow_html=True)

# --- 사이드바: 관리자 인증 ---
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
                        conn = get_connection()
                        try:
                            conn.execute("INSERT INTO members (member) VALUES (?)", (new_member.strip(),))
                            conn.commit()
                            st.rerun()
                        except: st.error("이미 존재합니다.")
                        finally: conn.close()
                
                members = load_members()
                del_mem = st.selectbox("삭제할 회원", ["선택"] + members)
                if st.button("회원 삭제") and del_mem != "선택":
                    conn = get_connection()
                    conn.execute("DELETE FROM usage WHERE member=?", (del_mem,))
                    conn.execute("DELETE FROM members WHERE member=?", (del_mem,))
                    conn.commit()
                    conn.close()
                    st.rerun()
        else:
            st.session_state['authenticated'] = False
            if admin_pwd: st.error("비밀번호가 틀렸습니다.")
    else:
        st.session_state['authenticated'] = False

# --- 데이터 입력 섹션 ---
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
        target_qty = st.number_input("수량", min_value=0, value=0, step=1)

    if st.button("🟡 테니스 볼 사용량 저장"):
        if target_member and str(target_member).strip():
            save_name = str(target_member).strip()
            conn = get_connection()
            conn.execute("INSERT INTO usage (member, date, quantity) VALUES (?, ?, ?)", 
                         (save_name, str(target_date), int(target_qty)))
            conn.commit()
            conn.close()
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
            
            # 데이터 개수에 따른 동적 설정 계산
            num_unique_days = len(df_day['date_str'].unique())
            dynamic_font_size = 16 if num_unique_days <= 5 else 12
            dynamic_bargap = 0.7 if num_unique_days <= 2 else 0.3

            fig_day = px.bar(df_day, x='date_str', y='quantity', color='member', 
                             barmode='group', text='quantity', height=320)
            
            fig_day.update_traces(
                textposition='outside', 
                textfont=dict(size=14, family="Arial Black", color="black"),
                cliponaxis=False
            )
            
            fig_day.update_layout(
                xaxis_title=None, 
                yaxis_title="사용량(개)",
                xaxis={
                    'type': 'category', 
                    'fixedrange': True,
                    'tickfont': {'size': dynamic_font_size, 'family': "Arial Black"}
                },
                yaxis={
                    'fixedrange': True, 
                    'dtick': 1, 
                    'gridcolor': '#DCDCDC',
                    'showgrid': True
                },
                bargap=dynamic_bargap,
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                dragmode=False,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, title=None)
            )

            # 1. 일별 기록 차트 부분
            st.plotly_chart(
                fig_day, 
                width='stretch',  # 최신 가이드라인 반영
                config={
                    'displayModeBar': False, 
                    'scrollZoom': False,  # 터치 줌 방지로 스크롤 간섭 최소화
                }
            )
          
            st.subheader("📈 월간 추이")
            # 데이터 정렬 확인
            monthly_display = monthly_summary.sort_values('연월_정렬')
            
            if not monthly_display.empty:
                # 1. 최대 수량에 따른 적절한 그리드 간격(dtick) 계산
                max_val = monthly_display['quantity'].max()
                if max_val <= 10:
                    dynamic_dtick = 2
                elif max_val <= 20:
                    dynamic_dtick = 5
                elif max_val <= 30:
                    dynamic_dtick = 10
                else:
                    dynamic_dtick = 20
                
                # Y축 범위도 글자가 안 잘리게 최대값보다 25% 정도 더 높게 설정
                y_range = [0, max_val * 1.25]
            else:
                dynamic_dtick = 1
                y_range = [0, 10]

            fig_month = px.line(monthly_display, x='연월_표시', y='quantity', 
                                markers=True, text='quantity', height=320)
            
            fig_month.update_traces(
                line_color='#2E7D32', 
                line_width=3,
                marker=dict(size=12, symbol="circle", color="#2E7D32", line=dict(width=2, color="white")), 
                textposition="top center", 
                cliponaxis=False, # 글자 잘림 방지
                textfont=dict(size=15, family="Arial Black", color="black")
            )
            
            fig_month.update_layout(
                xaxis_title=None, 
                yaxis_title="사용량(개)",
                xaxis={
                    'type': 'category', 
                    'fixedrange': True,
                    'tickfont': {'size': 14, 'family': "Arial Black"},
                    'showgrid': False,
                    'showline': True,
                    'linewidth': 2,
                    'linecolor': '#A5D6A7',
                    'mirror': True
                },
                yaxis={
                    'fixedrange': True, 
                    'showgrid': True,
                    'dtick': dynamic_dtick,   # 계산된 동적 간격 적용
                    'gridcolor': '#DCDCDC',
                    'gridwidth': 1,
                    'griddash': 'dot',
                    'zeroline': True,
                    'zerolinecolor': '#A5D6A7',
                    'showline': True,
                    'linewidth': 2,
                    'linecolor': '#A5D6A7',
                    'mirror': True,
                    'range': y_range          # 동적 범위 적용
                },
                margin=dict(l=10, r=10, t=60, b=10), # 상단 여백 넉넉히 유지
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(255,255,255,0.5)',
                dragmode=False
            )
            
            # 2. 월간 추이 차트 부분도 동일하게 적용
            st.plotly_chart(
                fig_month, 
                width='stretch',  # 최신 가이드라인 반영
                config={
                    'displayModeBar': False, 
                    'scrollZoom': False
                }
            )

with tab2:
    if st.session_state['authenticated']:
        st.subheader("📝 기록 수정 및 삭제")
        if not df_all.empty:
            df_edit = df_all.copy()
            df_edit['date'] = df_edit['date'].dt.date
            df_edit = df_edit.sort_values(by=['date', 'member'], ascending=[False, True]).reset_index(drop=True)
            
            st.info("💡 표에서 직접 내용을 수정하거나 행을 삭제한 후 저장 버튼을 누르세요.")
            edited_df = st.data_editor(df_edit[['member', 'date', 'quantity']], num_rows="dynamic", key="data_editor", hide_index=True)

            if st.button("💾 변경사항 최종 저장"):
                final_df = edited_df.dropna(subset=['member', 'date'])
                conn = get_connection()
                try:
                    conn.execute("DELETE FROM usage")
                    if not final_df.empty:
                        save_df = final_df[['member', 'date', 'quantity']]
                        save_df['date'] = save_df['date'].astype(str)
                        save_df.to_sql("usage", conn, if_exists="append", index=False)
                    conn.commit()
                    st.success("데이터베이스 업데이트 완료!")
                    st.rerun()
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")
                finally:
                    conn.close()
        else:
            st.info("수정할 기록이 없습니다.")
    else:
        st.warning("🔒 이 기능은 관리자 전용입니다.")
        st.info("왼쪽 사이드바에서 '관리자 모드 활성화' 후 비밀번호를 입력해 주세요.")

# 하단 다운로드 버튼 (df_all이 정의되어 있으므로 오류 없이 작동)
if not df_all.empty:
    csv_data = df_all.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 전체 기록 내보내기 (CSV)", data=csv_data, file_name=f"tennis_backup_{date.today()}.csv", mime="text/csv")
