import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import datetime

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 & 스타일
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Macroeconomic Radar",
    page_icon="📈",
    layout="wide"
)

# 커스텀 CSS (카드 디자인)
st.markdown("""
<style>
    /* 카드 디자인 */
    .metric-card {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    
    /* 코드 블록 줄바꿈 */
    div[data-testid="stCodeBlock"] pre {
        white-space: pre-wrap !important;
        word-break: break-word !important;
    }

    /* 📱 모바일 최적화: CSS Grid를 사용한 강력한 2열 강제 */
    @media (max-width: 640px) {
        /* 컬럼들을 감싸는 컨테이너를 Grid 모드로 변경 */
        div[data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important; /* 1:1 비율로 2개 강제 */
            gap: 10px !important;
            flex-direction: row !important; /* 기존 세로 정렬 무시 */
        }

        /* 개별 컬럼의 너비 강제 초기화 */
        div[data-testid="column"] {
            width: auto !important;
            flex: 1 1 auto !important;
            min-width: 0 !important; /* 내용이 넘쳐도 깨지지 않게 방지 */
        }
        
        /* 텍스트 크기 등 미세 조정 (선택사항) */
        div[data-testid="metric-container"] label {
            font-size: 12px !important; /* 모바일에서 글씨 너무 크면 줄임 */
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("📟 경제 모니터링")
st.divider()

# -----------------------------------------------------------------------------
# 2. 데이터 수집 및 차트 생성 함수들
# -----------------------------------------------------------------------------

# (1) 데일리 데이터 함수 (수정됨: ^TNX 차단 시 FRED로 우회)
@st.cache_data(ttl=3600)
def get_daily_data(ticker, period="6mo"):
    # 🌟 [수정 포인트] 미국 10년물 금리(^TNX)는 클라우드에서 야후 차단이 심하므로 FRED 공식 데이터(DGS10) 사용
    if ticker == "^TNX":
        # FRED에서 DGS10(일일 10년물 금리) 가져오기
        df = get_macro_data("DGS10")
        if df is None or df.empty:
            return None, None, None
        
        # 데이터 정리 (FRED는 가끔 '.' 같은 문자가 섞임 -> 숫자 변환)
        series = df['DGS10'].dropna().astype(float)
        
        last_price = series.iloc[-1]
        prev_price = series.iloc[-2]
        delta = last_price - prev_price
        
        return last_price, delta, series

    # 나머지 일반 주식/환율 등은 기존대로 야후 파이낸스 사용
    try:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if df.empty:
            return None, None, None
        
        last_price = df['Close'].iloc[-1].item()
        prev_price = df['Close'].iloc[-2].item()
        delta = last_price - prev_price
        
        return last_price, delta, df['Close']
    except Exception as e:
        return None, None, None

# (2) 월간 매크로 데이터 (기간 확대)
@st.cache_data(ttl=86400) 
def get_macro_data(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        df = pd.read_csv(url, index_col=0, parse_dates=True, na_values='.')
        df.columns = [series_id] 
        df = df.dropna()
        # ⭐ 수정됨: 2020년 -> 2000년으로 변경하여 장기 데이터 확보
        df = df[df.index > '2000-01-01']
        return df
    except Exception as e:
        return None

def create_sparkline_chart(data, color="red"):
    fig = go.Figure()
    y_vals = data.to_numpy().flatten()
    y_min = float(y_vals.min())
    y_max = float(y_vals.max())
    y_range = y_max - y_min
    buffer = y_range * 0.1 if y_range != 0 else 0.01 
    
    fig.add_trace(go.Scatter(
        x=data.index, y=y_vals, mode='lines', 
        line=dict(color=color, width=2), hoverinfo='x+y'
    ))
    
    fig.update_layout(
        height=120, margin=dict(l=0, r=0, t=15, b=20),
        xaxis=dict(visible=True, showgrid=False, tickformat="%m/%d", nticks=5),
        yaxis=dict(visible=False, range=[y_min - buffer, y_max + buffer]),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# (4) 메인 매크로 차트 생성 함수 (버튼 추가)
def create_macro_chart(df, col_name, title, color, target_line=None):
    fig = go.Figure()
    y_vals = df[col_name].to_numpy().flatten()
    
    # ... (기존 y_min, y_max 계산 로직 동일) ...
    y_min = float(y_vals.min())
    y_max = float(y_vals.max())
    if target_line is not None:
        y_min = min(y_min, target_line)
        y_max = max(y_max, target_line)
    y_range = y_max - y_min
    buffer = y_range * 0.1 if y_range != 0 else 0.1

    fig.add_trace(go.Scatter(
        x=df.index, y=y_vals, mode='lines', name=title,
        line=dict(color=color, width=3)
    ))
    
    if target_line is not None:
        fig.add_hline(y=target_line, line_dash="dash", line_color="green", annotation_text=f"Target ({target_line}%)")

    # 오늘 날짜 기준 5년 전 계산 (기본 뷰 설정을 위해)
    five_years_ago = datetime.datetime.now() - datetime.timedelta(days=365*5)

    fig.update_layout(
        title=title, height=350, margin=dict(l=20, r=20, t=60, b=20),
        yaxis=dict(range=[y_min - buffer, y_max + buffer], gridcolor='rgba(128,128,128,0.2)'),
        
        # ⭐ [핵심 추가] X축에 기간 선택 버튼 및 초기 범위 설정
        xaxis=dict(
            gridcolor='rgba(128,128,128,0.2)',
            
            # 1. 기간 선택 버튼 (Range Selector)
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1년", step="year", stepmode="backward"),
                    dict(count=5, label="5년", step="year", stepmode="backward"),
                    dict(count=10, label="10년", step="year", stepmode="backward"),
                    dict(step="all", label="전체")
                ]),
                bgcolor="#f9f9f9", # 버튼 배경색
                activecolor="#e5e5e5", # 선택된 버튼 색
                font=dict(color="black")
            ),
            
            # 2. 초기 화면은 최근 5년만 보여주기 (너무 길면 안 보이니까)
            range=[five_years_ago, datetime.datetime.now()]
        ),
        
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'   
    )
    return fig

# -----------------------------------------------------------------------------
# 3. UI 구성: Section 1 - Market Pulse (Daily)
# -----------------------------------------------------------------------------
st.subheader("실시간 시장 동향")

# 8개 지표 정의
metrics = {
    # [1열: 핵심 지표]
    "🇺🇸 미국 10년물 금리": {"ticker": "^TNX", "suffix": "%"},
    "🇰🇷 원/달러 환율": {"ticker": "KRW=X", "suffix": "원"},
    "😨 VIX (공포지수)": {"ticker": "^VIX", "suffix": ""},
    "🇺🇸 나스닥 100": {"ticker": "^IXIC", "suffix": ""},
    
    # [2열: 글로벌 & 리스크]
    "🇺🇸 S&P 500": {"ticker": "^GSPC", "suffix": ""},    
    "🇯🇵 닛케이 225": {"ticker": "^N225", "suffix": ""},
    "🌏 신흥국 ETF (EEM)": {"ticker": "EEM", "suffix": ""},
    "🇰🇷 코스피 지수": {"ticker": "^KS11", "suffix": ""},    
}

metrics_list = list(metrics.items())
data_summary = ""

# 4개씩 끊어서 두 줄(Row)로 표시
for i in range(0, len(metrics_list), 4):
    row_metrics = metrics_list[i:i+4]
    cols = st.columns(4)
    
    for col, (name, info) in zip(cols, row_metrics):
        with col:
            current, delta, history = get_daily_data(info['ticker'])
            
            if current is not None:
                # 🌟 [추가됨] 등락률(%) 계산 로직
                prev_price = current - delta
                pct_change = 0
                if prev_price != 0:
                    pct_change = (delta / prev_price) * 100
                
                # 1. Delta 텍스트 만들기 (등락폭 + 퍼센트)
                # 기본 포맷: "변동값 (퍼센트%)" -> 예: +5.20 (+1.5%)
                delta_text = f"{delta:,.2f} ({pct_change:+.2f}%)"
                
                if name == "😨 VIX (공포지수)":
                    daily_vol = current / 16
                    # VIX는 내용이 기니까 '예상변동'을 조금 짧게 줄여서 표시 (공간 확보)
                    delta_text = f"{delta:,.2f} (예상변동률 ±{daily_vol:.2f}%)"
                    data_summary += f"- {name}: {current:,.2f} (등락: {pct_change:+.2f}%) -> [오늘예상변동: ±{daily_vol:.2f}%]\n"
                else:
                    data_summary += f"- {name}: {current:,.2f}{info['suffix']} (전일대비: {delta:+.2f} / {pct_change:+.2f}%)\n"

                # 2. 메트릭 표시
                st.metric(
                    label=name,
                    value=f"{current:,.2f}{info['suffix']}",
                    delta=delta_text
                )
                
                # 3. 차트 표시
                line_color = '#ff4b4b' if delta > 0 else '#4b88ff'
                fig = create_sparkline_chart(history.tail(90), color=line_color)
                # width='content'는 경고가 뜰 수 있으니 use_container_width=True 권장 (경고 무시 코드 넣으셨다면 OK)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
            else:
                st.warning(f"{name} Load Fail")
    
    # 줄바꿈 간격
    if i == 0 :
        st.markdown("---")

# -----------------------------------------------------------------------------
# 4. UI 구성: Section 2 - Macro Health (Monthly)
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("거시경제 흐름")
st.caption("지난 25년간의 장기 추세를 통해 현재 경제 사이클의 위치를 파악합니다.")

# 1. 인플레이션 (CPI) 차트
st.markdown("#### 📉 인플레이션 추이 (CPI YoY)")
cpi_data = get_macro_data("CPIAUCSL")

if cpi_data is not None:
    # 전년 대비 상승률(YoY) 계산
    cpi_yoy = cpi_data.pct_change(periods=12) * 100
    
    # 차트 그리기
    fig_cpi = create_macro_chart(cpi_yoy, 'CPIAUCSL', "미국 소비자 물가 지수 (YoY)", '#ef553b', target_line=2.0)
    st.plotly_chart(fig_cpi, use_container_width=True)
    
    # 요약 데이터 누적
    last_cpi = cpi_yoy['CPIAUCSL'].iloc[-1]
    data_summary += f"- 미국 소비자 물가 지수(CPI, YoY): {last_cpi:.2f}%\n"
else:
    st.warning("CPI 데이터 로드 실패")

# 차트 간 구분선
st.divider()

# 2. 실업률 (Unemployment) 차트
st.markdown("#### 🏭 고용지표 (실업률)")
unrate_data = get_macro_data("UNRATE")

if unrate_data is not None:
    # 차트 그리기
    fig_unrate = create_macro_chart(unrate_data, 'UNRATE', "미국 실업률 (%)", '#ffa15a')
    st.plotly_chart(fig_unrate, use_container_width=True)
    
    # 요약 데이터 누적
    last_unrate = unrate_data['UNRATE'].iloc[-1]
    data_summary += f"- 미국 실업률: {last_unrate:.2f}%\n"
else:
    st.warning("실업률 데이터 로드 실패")

# -----------------------------------------------------------------------------
# 5. UI 구성: Section 3 - Gemini Prompt Generator
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("📝 프롬프트 가이드")
st.info("아래 박스 우측 상단의 '복사' 버튼을 눌러 AI 서비스에 붙여 넣으세요!")

# 오늘 날짜
today = datetime.datetime.now().strftime("%Y년 %m월 %d일")

# 완성된 프롬프트 텍스트
final_prompt = f"""
[역할]
당신은 월가에서 20년 경력을 가진 거시경제 애널리스트이자, 나의 친절한 투자 멘토입니다.

[상황]
오늘은 {today}입니다. 수집된 최신 시장 데이터는 아래와 같습니다.

[데이터 리포트]
{data_summary}

[요청사항]
1. 시장 분위기 3줄 요약: 현재 시장이 탐욕 구간인지, 공포 구간인지, 관망세인지 명확히 진단해줘.
2. 핵심 지표 해석: 국채 금리와 환율의 움직임이 현재 주식 시장(S&P 500)에 어떤 압력을 주고 있는지 분석해줘.
3. 리스크 점검: 물가와 실업률 추세를 볼 때 '연준(Fed)'의 정책 방향이 어떻게 될지 예측해줘.
4. 투자 조언: 주식 시장 전체에 대한 투자 조언을 해줘. 주식,채권, 원자재 등등 지금 시점에서 
            개인 투자자는 '현금 비중'을 늘려야 할지 아니면 '매수'를 하는게 좋을지.

전문 용어를 쓰되 이해하기 쉽게 존대말로 설명해줘.
"""

# 코드 블록으로 표시하여 원클릭 복사 지원
st.code(final_prompt, language="text")