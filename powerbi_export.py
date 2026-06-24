import io
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import eda_analysis as eda
from openpyxl.drawing.image import Image as XLImage

_CHART_W = 760
_CHART_H = 320
_ROWS_PER_CHART = 19


def _sname(prefix: str, col: str) -> str:
    """Build a sheet name that fits within Excel's 31-char limit."""
    return f"{prefix}{col}"[:31]


def _fig_to_png(fig) -> io.BytesIO:
    """Render a Plotly figure to a PNG BytesIO buffer via kaleido."""
    raw = pio.to_image(fig, format="png", width=_CHART_W, height=_CHART_H, scale=1.2)
    return io.BytesIO(raw)


def _add_gallery_sheet(writer, chart_specs: list) -> None:
    """Add a visual gallery sheet with embedded chart images for reference."""
    if not chart_specs:
        return

    deduped_specs = []
    seen_groups = set()
    for chart in chart_specs:
        group = chart.get("gallery_group", chart["title"])
        if group in seen_groups:
            continue
        seen_groups.add(group)
        deduped_specs.append(chart)

    workbook = writer.book
    sheet_name = "Chart_Gallery"
    worksheet = workbook.create_sheet(title=sheet_name)
    worksheet["A1"] = "These images mirror the charts shown in the Streamlit dashboard."
    worksheet["A2"] = "Power BI imports the chart data tables, not these embedded images."

    row_cursor = 4
    for chart in deduped_specs:
        worksheet[f"A{row_cursor}"] = chart["title"]
        worksheet[f"A{row_cursor + 1}"] = f"Source table: {chart['source_table']}"
        try:
            image = XLImage(_fig_to_png(chart["figure"]))
            image.width = _CHART_W
            image.height = _CHART_H
            image.anchor = f"A{row_cursor + 2}"
            worksheet.add_image(image)
        except Exception as err:
            # Keep export working even when static image rendering dependencies are missing.
            worksheet[f"A{row_cursor + 2}"] = f"Image render skipped: {err}"
        row_cursor += _ROWS_PER_CHART


def _add_visual_guide_sheet(writer, guide_rows: list) -> None:
    """Add a guide sheet that maps each website chart to a Power BI visual/table."""
    if not guide_rows:
        return

    guide_df = pd.DataFrame(guide_rows)
    guide_df.to_excel(writer, sheet_name="PowerBI_Visual_Guide", index=False)


def _build_histogram_table(df: pd.DataFrame, col: str, bins="auto") -> pd.DataFrame:
    """Return histogram bin data so Power BI can recreate the chart."""
    series = df[col].dropna()
    if series.empty:
        return pd.DataFrame(columns=["column", "bin_start", "bin_end", "count"])

    counts, edges = np.histogram(series.to_numpy(), bins=bins)
    return pd.DataFrame(
        {
            "column": col,
            "bin_start": edges[:-1],
            "bin_end": edges[1:],
            "count": counts,
        }
    )


def _build_boxplot_table(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Return raw values and summary stats for boxplot recreation in Power BI."""
    series = df[col].dropna()
    if series.empty:
        return pd.DataFrame(columns=["column", "value", "min", "q1", "median", "q3", "max"])

    summary = {
        "min": series.min(),
        "q1": series.quantile(0.25),
        "median": series.quantile(0.5),
        "q3": series.quantile(0.75),
        "max": series.max(),
    }
    box_df = pd.DataFrame({"column": col, "value": series.reset_index(drop=True)})
    for key, value in summary.items():
        box_df[key] = value
    return box_df


def _build_category_count_table(df: pd.DataFrame, col: str) -> pd.DataFrame:
    counts = df[col].value_counts(dropna=False).reset_index()
    counts.columns = [col, "count"]
    return counts


def _build_time_series_table(df: pd.DataFrame, date_col: str, value_col: str) -> pd.DataFrame:
    ts_df = df.groupby(date_col)[value_col].sum().reset_index()
    ts_df[date_col] = ts_df[date_col].dt.strftime("%Y-%m-%d")
    return ts_df


def _build_revenue_by_category_table(df: pd.DataFrame, col: str) -> pd.DataFrame:
    return (
        df.groupby(col)["revenue"]
        .sum()
        .reset_index()
        .sort_values("revenue", ascending=False)
    )


def build_powerbi_excel(cleaned_df: pd.DataFrame, metrics: dict) -> bytes:
    """
    Builds a multi-sheet Excel workbook for Power BI containing:
            - Data tables for every analysis view
            - Chart-ready tables matching every chart shown in the Streamlit app
    """
    buffer = io.BytesIO()
    chart_gallery_specs = []
    visual_guide_rows = []
    num_chart_figs = {}
    cat_chart_figs = {}
    ts_chart_figs = None
    corr_fig = None

    if not cleaned_df.empty:
        num_chart_figs = eda.visualize_numerical_distributions(cleaned_df)
        cat_chart_figs = eda.visualize_categorical_counts(cleaned_df)
        if "order_date" in cleaned_df.columns:
            ts_chart_figs = eda.visualize_time_series(cleaned_df, "order_date")
        corr_fig = eda.visualize_correlation_heatmap(cleaned_df)

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:

        # ── 1. Fact_Sales ─────────────────────────────────────────────────────
        cleaned_df.to_excel(writer, sheet_name="Fact_Sales", index=False)

        # ── 2. KPI_Summary ────────────────────────────────────────────────────
        # Additional KPIs beyond the base three
        extra = {}

        if "revenue" in cleaned_df.columns:
            extra["Total Revenue"] = cleaned_df["revenue"].sum()
            extra["Min Order Revenue"] = cleaned_df["revenue"].min()
            extra["Max Order Revenue"] = cleaned_df["revenue"].max()
            extra["Median Order Revenue"] = cleaned_df["revenue"].median()

        if "quantity" in cleaned_df.columns:
            extra["Total Units Sold"] = cleaned_df["quantity"].sum()
            extra["Avg Quantity Per Order"] = cleaned_df["quantity"].mean()

        if "unit_price" in cleaned_df.columns:
            extra["Avg Unit Price"] = cleaned_df["unit_price"].mean()

        if "order_date" in cleaned_df.columns:
            extra["Date Range Start"] = str(cleaned_df["order_date"].min().date())
            extra["Date Range End"] = str(cleaned_df["order_date"].max().date())
            days = (cleaned_df["order_date"].max() - cleaned_df["order_date"].min()).days
            extra["Total Days"] = int(days) if days > 0 else 1
            if "order_id" in cleaned_df.columns and days > 0:
                extra["Avg Orders Per Day"] = round(cleaned_df["order_id"].nunique() / days, 2)

        # Merge base metrics + extra KPIs
        all_kpis = {**metrics, **extra}
        kpi_df = pd.DataFrame(
            [{"KPI": k, "Value": v} for k, v in all_kpis.items()]
        )
        kpi_df.to_excel(writer, sheet_name="KPI_Summary", index=False)

        # ── 3. EDA_Numerical_Stats ────────────────────────────────────────────
        numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns.tolist()
        if "order_id" in numeric_cols:
            numeric_cols.remove("order_id")

        if numeric_cols:
            stats_df = cleaned_df[numeric_cols].describe().T.reset_index()
            stats_df.rename(columns={"index": "column"}, inplace=True)
            stats_df.to_excel(writer, sheet_name="EDA_Numerical_Stats", index=False)

        # ── 4. EDA_Categorical_Counts ─────────────────────────────────────────
        cat_cols = cleaned_df.select_dtypes(include=["object", "category", "string"]).columns.tolist()
        cat_rows = []
        for col in cat_cols:
            if cleaned_df[col].nunique() > 100:
                continue          # skip ultra-high cardinality
            counts = cleaned_df[col].value_counts().reset_index()
            counts.columns = ["value", "count"]
            counts.insert(0, "column", col)
            cat_rows.append(counts)

        if cat_rows:
            cat_df = pd.concat(cat_rows, ignore_index=True)
            cat_df.to_excel(writer, sheet_name="EDA_Categorical_Counts", index=False)

        # ── 5. EDA_Time_Series ────────────────────────────────────────────────
        if "order_date" in cleaned_df.columns and numeric_cols:
            ts_agg = (
                cleaned_df.groupby("order_date")[numeric_cols]
                .sum()
                .reset_index()
            )
            ts_agg["order_date"] = ts_agg["order_date"].dt.strftime("%Y-%m-%d")
            ts_agg.to_excel(writer, sheet_name="EDA_Time_Series", index=False)

            # Monthly aggregation as an additional sheet
            cleaned_df["_year_month"] = cleaned_df["order_date"].dt.to_period("M").astype(str)
            monthly_agg = (
                cleaned_df.groupby("_year_month")[numeric_cols]
                .sum()
                .reset_index()
                .rename(columns={"_year_month": "year_month"})
            )
            monthly_agg.to_excel(writer, sheet_name="EDA_Monthly_Trend", index=False)
            cleaned_df.drop(columns=["_year_month"], inplace=True)

        # ── 6. EDA_Correlation_Matrix ─────────────────────────────────────────
        if len(numeric_cols) >= 2:
            corr_df = cleaned_df[numeric_cols].corr().reset_index()
            corr_df.rename(columns={"index": "column"}, inplace=True)
            corr_df.to_excel(writer, sheet_name="EDA_Correlation_Matrix", index=False)

        # ── 7. Revenue_By_Category ────────────────────────────────────────────
        if "revenue" in cleaned_df.columns and cat_cols:
            rev_sheets_written = 0
            for col in cat_cols:
                if cleaned_df[col].nunique() > 50:
                    continue
                rev_by_cat = (
                    cleaned_df.groupby(col)["revenue"]
                    .agg(total_revenue="sum", avg_revenue="mean", order_count="count")
                    .reset_index()
                    .sort_values("total_revenue", ascending=False)
                )
                sheet_name = f"Rev_By_{col}"[:31]   # Excel sheet name limit = 31 chars
                rev_by_cat.to_excel(writer, sheet_name=sheet_name, index=False)
                rev_sheets_written += 1
                if rev_sheets_written >= 5:           # cap at 5 category sheets
                    break

        # ── 8. Chart-ready tables (mirror every chart shown in the Streamlit app) ──
        for col in numeric_cols:
            hist_df = _build_histogram_table(cleaned_df, col)
            if not hist_df.empty:
                hist_sheet = _sname("Cht_Dist_", col)
                hist_df.to_excel(writer, sheet_name=hist_sheet, index=False)
                hist_fig = num_chart_figs[col]["histogram"]
                chart_gallery_specs.append(
                    {
                        "title": f"Distribution of {col}",
                        "source_table": hist_sheet,
                        "figure": hist_fig,
                        "gallery_group": "histogram",
                    }
                )
                visual_guide_rows.append(
                    {
                        "dashboard_section": "EDA Numerical Analysis",
                        "chart_title": f"Distribution of {col}",
                        "powerbi_visual": "Clustered column chart",
                        "source_table": hist_sheet,
                        "axis_field": "bin_start or bin_end",
                        "value_field": "count",
                        "notes": "Represents the histogram shown on the website.",
                    }
                )

            box_df = _build_boxplot_table(cleaned_df, col)
            if not box_df.empty:
                box_sheet = _sname("Box_", col)
                box_df.to_excel(writer, sheet_name=box_sheet, index=False)
                box_fig = num_chart_figs[col]["boxplot"]
                chart_gallery_specs.append(
                    {
                        "title": f"Box Plot of {col}",
                        "source_table": box_sheet,
                        "figure": box_fig,
                        "gallery_group": "boxplot",
                    }
                )
                visual_guide_rows.append(
                    {
                        "dashboard_section": "EDA Numerical Analysis",
                        "chart_title": f"Box Plot of {col}",
                        "powerbi_visual": "Box and whisker visual",
                        "source_table": box_sheet,
                        "axis_field": "column",
                        "value_field": "value",
                        "notes": "Use the custom box-and-whisker visual or summarize with min/q1/median/q3/max.",
                    }
                )

        for col in cat_cols:
            if cleaned_df[col].nunique() > 20:
                continue
            cat_df = _build_category_count_table(cleaned_df, col)
            if not cat_df.empty:
                cat_sheet = _sname("Cht_Cat_", col)
                cat_df.to_excel(writer, sheet_name=cat_sheet, index=False)
                cat_fig = cat_chart_figs[col]
                chart_gallery_specs.append(
                    {
                        "title": f"Count of {col}",
                        "source_table": cat_sheet,
                        "figure": cat_fig,
                        "gallery_group": "categorical",
                    }
                )
                visual_guide_rows.append(
                    {
                        "dashboard_section": "EDA Categorical Analysis",
                        "chart_title": f"Count of {col}",
                        "powerbi_visual": "Clustered column chart",
                        "source_table": cat_sheet,
                        "axis_field": col,
                        "value_field": "count",
                        "notes": "Matches the website categorical count chart.",
                    }
                )

        if "order_date" in cleaned_df.columns:
            for col in numeric_cols:
                ts_df = _build_time_series_table(cleaned_df, "order_date", col)
                if not ts_df.empty:
                    ts_sheet = _sname("Cht_TS_", col)
                    ts_df.to_excel(writer, sheet_name=ts_sheet, index=False)
                    ts_fig = ts_chart_figs[col] if ts_chart_figs else None
                    if ts_fig is None:
                        continue
                    chart_gallery_specs.append(
                        {
                            "title": f"{col} Over Time",
                            "source_table": ts_sheet,
                            "figure": ts_fig,
                            "gallery_group": "time_series",
                        }
                    )
                    visual_guide_rows.append(
                        {
                            "dashboard_section": "EDA Time Series Analysis",
                            "chart_title": f"{col} Over Time",
                            "powerbi_visual": "Line chart",
                            "source_table": ts_sheet,
                            "axis_field": "order_date",
                            "value_field": col,
                            "notes": "Daily trend matching the website time-series chart.",
                        }
                    )

        if len(numeric_cols) >= 2:
            corr_df.to_excel(writer, sheet_name="Cht_Correlation", index=False)
            if corr_fig:
                chart_gallery_specs.append(
                    {
                        "title": "Correlation Heatmap",
                        "source_table": "Cht_Correlation",
                        "figure": corr_fig,
                        "gallery_group": "correlation",
                    }
                )
                visual_guide_rows.append(
                    {
                        "dashboard_section": "EDA Correlation Analysis",
                        "chart_title": "Correlation Heatmap",
                        "powerbi_visual": "Matrix or heatmap custom visual",
                        "source_table": "Cht_Correlation",
                        "axis_field": "column",
                        "value_field": "numeric correlation columns",
                        "notes": "Use a matrix-style heatmap visual in Power BI.",
                    }
                )

        if "order_date" in cleaned_df.columns and "revenue" in cleaned_df.columns:
            revenue_trend_df = _build_time_series_table(cleaned_df, "order_date", "revenue")
            revenue_trend_df.to_excel(writer, sheet_name="Cht_Revenue_Trend", index=False)
            revenue_fig = px.line(
                revenue_trend_df,
                x="order_date",
                y="revenue",
                title="Revenue Trend",
                template="plotly_dark",
                markers=True,
            )
            chart_gallery_specs.append(
                {
                    "title": "Revenue Trend",
                    "source_table": "Cht_Revenue_Trend",
                    "figure": revenue_fig,
                    "gallery_group": "revenue_trend",
                }
            )
            visual_guide_rows.append(
                {
                    "dashboard_section": "KPI Dashboard",
                    "chart_title": "Revenue Trend",
                    "powerbi_visual": "Line chart",
                    "source_table": "Cht_Revenue_Trend",
                    "axis_field": "order_date",
                    "value_field": "revenue",
                    "notes": "Matches the KPI dashboard revenue trend chart.",
                }
            )

        if "revenue" in cleaned_df.columns:
            rev_chart_count = 0
            for col in cat_cols:
                if cleaned_df[col].nunique() > 50:
                    continue
                rev_by_cat = _build_revenue_by_category_table(cleaned_df, col)
                if not rev_by_cat.empty:
                    rev_sheet = _sname("Cht_Rev_", col)
                    rev_by_cat.to_excel(writer, sheet_name=rev_sheet, index=False)
                    rev_fig = px.bar(
                        rev_by_cat,
                        x=col,
                        y="revenue",
                        title=f"Revenue by {col}",
                        template="plotly_dark",
                        color="revenue",
                        color_continuous_scale="Viridis",
                    )
                    chart_gallery_specs.append(
                        {
                            "title": f"Revenue by {col}",
                            "source_table": rev_sheet,
                            "figure": rev_fig,
                            "gallery_group": "revenue_by_category",
                        }
                    )
                    visual_guide_rows.append(
                        {
                            "dashboard_section": "KPI Dashboard",
                            "chart_title": f"Revenue by {col}",
                            "powerbi_visual": "Clustered column chart",
                            "source_table": rev_sheet,
                            "axis_field": col,
                            "value_field": "revenue",
                            "notes": "Revenue-by-category analysis exported from the KPI area.",
                        }
                    )
                    rev_chart_count += 1
                if rev_chart_count >= 5:
                    break

        _add_gallery_sheet(writer, chart_gallery_specs)
        _add_visual_guide_sheet(writer, visual_guide_rows)

    buffer.seek(0)
    return buffer.read()
