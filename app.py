from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DATA_PATH = APP_DIR / "kanazawa_weather_processed.csv"
MONTH_ORDER = list(range(1, 13))
MONTH_LABELS = {month: f"{month}月" for month in MONTH_ORDER}
SEASON_MONTHS = {
    "すべて": MONTH_ORDER,
    "春": [3, 4, 5],
    "夏": [6, 7, 8],
    "秋": [9, 10, 11],
    "冬": [12, 1, 2],
}


st.set_page_config(
    page_title="金沢 雨雪ダッシュボード",
    page_icon="🌧️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {max-width: 1240px; padding-top: 1.5rem; padding-bottom: 2.5rem;}
    h1, h2, h3 {letter-spacing: 0;}
    [data-testid="stMetric"] {border-top: 3px solid #2f6f9f; padding-top: 0.7rem;}
    [data-testid="stSidebar"] {border-right: 1px solid #d8dee4;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> pd.DataFrame:
    frame = pd.read_csv(DATA_PATH, parse_dates=["date"])
    frame["month_label"] = pd.Categorical(
        frame["month_label"],
        categories=[MONTH_LABELS[month] for month in MONTH_ORDER],
        ordered=True,
    )
    return frame


data = load_data()

st.title("金沢の雨と雪を可視化する")
st.caption("気象庁・金沢観測所の月別データ（2015–2025年）")

with st.sidebar:
    st.header("絞り込み")
    min_year = int(data["year"].min())
    max_year = int(data["year"].max())
    year_range = st.slider(
        "年",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
    )
    season = st.segmented_control(
        "季節",
        options=list(SEASON_MONTHS),
        default="すべて",
        selection_mode="single",
    )
    available_months = SEASON_MONTHS[season or "すべて"]
    selected_months = st.multiselect(
        "月",
        options=available_months,
        default=available_months,
        format_func=lambda month: MONTH_LABELS[month],
    )
    year_metric = st.selectbox(
        "年比較の指標",
        options=[
            "年間降水量",
            "雨日数",
            "年間降雪量",
            "年平均気温",
        ],
    )

filtered = data[
    data["year"].between(year_range[0], year_range[1])
    & data["month"].isin(selected_months)
].copy()

if filtered.empty:
    st.warning("表示する月を1つ以上選択してください。")
    st.stop()

metric_columns = st.columns(4)
metric_columns[0].metric(
    "月平均降水量",
    f"{filtered['precipitation_total_mm'].mean():.1f} mm",
)
metric_columns[1].metric(
    "雨日数（月平均）",
    f"{filtered['rainy_days_1mm'].mean():.1f} 日",
)
metric_columns[2].metric(
    "平均気温",
    f"{filtered['mean_temperature_c'].mean():.1f} ℃",
)
metric_columns[3].metric(
    "月平均降雪量",
    f"{filtered['snowfall_total_cm'].mean():.1f} cm",
)

rain_tab, temperature_tab, snow_tab, comparison_tab = st.tabs(
    ["降水", "気温", "雪", "年比較"]
)

with rain_tab:
    monthly_rain = (
        filtered.groupby(["month", "month_label"], observed=True)
        .agg(
            平均降水量=("precipitation_total_mm", "mean"),
            平均雨日数=("rainy_days_1mm", "mean"),
            強い雨の日数=("heavy_rain_days_10mm", "mean"),
        )
        .reset_index()
        .sort_values("month")
    )
    rain_left, rain_right = st.columns(2)
    with rain_left:
        st.subheader("月別平均降水量")
        precipitation_figure = px.bar(
            monthly_rain,
            x="month_label",
            y="平均降水量",
            labels={"month_label": "月", "平均降水量": "降水量（mm）"},
            color_discrete_sequence=["#2f6f9f"],
            text_auto=".0f",
        )
        precipitation_figure.update_layout(
            height=420,
            margin={"l": 0, "r": 0, "t": 10, "b": 0},
            yaxis={"rangemode": "tozero"},
        )
        st.plotly_chart(precipitation_figure, width="stretch")
    with rain_right:
        st.subheader("月別の雨日数")
        rain_days_long = monthly_rain.melt(
            id_vars=["month", "month_label"],
            value_vars=["平均雨日数", "強い雨の日数"],
            var_name="区分",
            value_name="日数",
        )
        rain_days_figure = px.line(
            rain_days_long,
            x="month_label",
            y="日数",
            color="区分",
            markers=True,
            labels={"month_label": "月", "日数": "日数（日）"},
            color_discrete_sequence=["#187760", "#d9553f"],
        )
        rain_days_figure.update_layout(
            height=420,
            margin={"l": 0, "r": 0, "t": 10, "b": 0},
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.01},
            yaxis={"rangemode": "tozero"},
        )
        st.plotly_chart(rain_days_figure, width="stretch")

with temperature_tab:
    st.subheader("月別平均気温")
    monthly_temperature = (
        filtered.groupby(["month", "month_label"], observed=True)
        .agg(
            日平均=("mean_temperature_c", "mean"),
            日最高の平均=("mean_daily_high_c", "mean"),
            日最低の平均=("mean_daily_low_c", "mean"),
        )
        .reset_index()
        .sort_values("month")
    )
    temperature_long = monthly_temperature.melt(
        id_vars=["month", "month_label"],
        value_vars=["日最高の平均", "日平均", "日最低の平均"],
        var_name="区分",
        value_name="気温",
    )
    temperature_figure = px.line(
        temperature_long,
        x="month_label",
        y="気温",
        color="区分",
        markers=True,
        labels={"month_label": "月", "気温": "気温（℃）"},
        color_discrete_sequence=["#d9553f", "#d9a31a", "#2f6f9f"],
    )
    temperature_figure.update_layout(
        height=470,
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.01},
    )
    st.plotly_chart(temperature_figure, width="stretch")

with snow_tab:
    snow_left, snow_right = st.columns([1.15, 0.85])
    monthly_snow = (
        filtered.groupby(["month", "month_label"], observed=True)
        .agg(
            平均降雪量=("snowfall_total_cm", "mean"),
            平均最深積雪=("max_snow_depth_cm", "mean"),
            平均雪日数=("snow_days", "mean"),
        )
        .reset_index()
        .sort_values("month")
    )
    with snow_left:
        st.subheader("月別平均降雪量")
        snowfall_figure = px.bar(
            monthly_snow,
            x="month_label",
            y="平均降雪量",
            labels={"month_label": "月", "平均降雪量": "降雪量（cm）"},
            color_discrete_sequence=["#6b93c6"],
            text_auto=".1f",
        )
        snowfall_figure.update_layout(
            height=430,
            margin={"l": 0, "r": 0, "t": 10, "b": 0},
            yaxis={"rangemode": "tozero"},
        )
        st.plotly_chart(snowfall_figure, width="stretch")
    with snow_right:
        st.subheader("積雪と雪日数")
        snow_detail = monthly_snow.melt(
            id_vars=["month", "month_label"],
            value_vars=["平均最深積雪", "平均雪日数"],
            var_name="区分",
            value_name="値",
        )
        snow_detail_figure = px.line(
            snow_detail,
            x="month_label",
            y="値",
            color="区分",
            markers=True,
            labels={"month_label": "月"},
            color_discrete_sequence=["#2f6f9f", "#8f6bb3"],
        )
        snow_detail_figure.update_layout(
            height=430,
            margin={"l": 0, "r": 0, "t": 10, "b": 0},
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.01},
            yaxis={"rangemode": "tozero"},
        )
        st.plotly_chart(snow_detail_figure, width="stretch")

with comparison_tab:
    st.subheader("年別比較")
    annual = (
        filtered.groupby("year")
        .agg(
            年間降水量=("precipitation_total_mm", "sum"),
            雨日数=("rainy_days_1mm", "sum"),
            年間降雪量=("snowfall_total_cm", "sum"),
            年平均気温=("mean_temperature_c", "mean"),
        )
        .reset_index()
    )
    units = {
        "年間降水量": "mm",
        "雨日数": "日",
        "年間降雪量": "cm",
        "年平均気温": "℃",
    }
    comparison_figure = px.bar(
        annual,
        x="year",
        y=year_metric,
        labels={"year": "年", year_metric: f"{year_metric}（{units[year_metric]}）"},
        color_discrete_sequence=["#2f6f9f"],
        text_auto=".1f",
    )
    comparison_figure.update_layout(
        height=470,
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        yaxis={"rangemode": "tozero"},
    )
    st.plotly_chart(comparison_figure, width="stretch")

st.subheader("月別データ")
display_data = filtered.sort_values(["year", "month"]).rename(
    columns={
        "year": "年",
        "month_label": "月",
        "precipitation_total_mm": "降水量（mm）",
        "rainy_days_1mm": "雨日数（1mm以上）",
        "mean_temperature_c": "平均気温（℃）",
        "snowfall_total_cm": "降雪量（cm）",
        "max_snow_depth_cm": "最深積雪（cm）",
        "quality_summary": "品質",
    }
)
st.dataframe(
    display_data[
        [
            "年",
            "月",
            "降水量（mm）",
            "雨日数（1mm以上）",
            "平均気温（℃）",
            "降雪量（cm）",
            "最深積雪（cm）",
            "品質",
        ]
    ],
    hide_index=True,
    width="stretch",
)

st.caption(
    "雨日数は月降水量1.0mm以上の日数。2021年7月の雪日数のみ資料不足値を含みます。"
)
st.caption(
    "出典：気象庁『過去の気象データ検索』金沢観測所（47605）。"
    "本分析の11年間平均は気象庁の平年値ではありません。"
)
