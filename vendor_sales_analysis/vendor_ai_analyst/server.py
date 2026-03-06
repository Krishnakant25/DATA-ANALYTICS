"""
Data Deep-Dive MCP Server
Upgraded with custom professional chart tools matching original analysis quality.
"""

import json
import io
import traceback
import sqlite3
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from sqlalchemy import create_engine, text
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
import asyncio

# ── Global state ──────────────────────────────────────────────────────────────
_df: pd.DataFrame | None = None
_source_label: str = ""
_engine = None
DB_PATH = "D:\\Resume_Projects\\VendorMCP\\data-deepdive-mcp\\inventory.db"
OUTPUT_DIR = Path("./mcp_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

app = Server("data-deepdive")

# ── Helpers ───────────────────────────────────────────────────────────────────
def _require_df() -> pd.DataFrame:
    if _df is None:
        raise ValueError("No dataset loaded. Call load_dataset() first.")
    return _df

def _fig_to_path(fig: plt.Figure, name: str) -> str:
    path = OUTPUT_DIR / name
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    return str(path.resolve())

def _get_db_engine():
    return create_engine(f"sqlite:///{DB_PATH}")


# ══════════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        # ── Original 8 tools ─────────────────────────────────────────────────
        types.Tool(
            name="load_dataset",
            description="Load a CSV, SQLite table, or PostgreSQL table into memory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "CSV file path, SQLite path, or SQLAlchemy connection string."},
                    "table":  {"type": "string", "description": "Table name (required for SQLite/PostgreSQL)."},
                    "limit":  {"type": "integer", "description": "Max rows to load (default: all)."}
                },
                "required": ["source"]
            }
        ),
        types.Tool(
            name="profile_data",
            description="Profile the loaded dataset: shape, dtypes, nulls, descriptive stats.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="detect_outliers",
            description="Detect outliers in numeric columns using IQR and Z-score methods.",
            inputSchema={
                "type": "object",
                "properties": {
                    "columns": {"type": "array", "items": {"type": "string"}, "description": "Columns to check (default: all numeric)."},
                    "method":  {"type": "string", "enum": ["iqr", "zscore", "both"], "description": "Detection method (default: both)."}
                }
            }
        ),
        types.Tool(
            name="correlation_matrix",
            description="Compute correlations between numeric columns and save a heatmap.",
            inputSchema={
                "type": "object",
                "properties": {
                    "method":    {"type": "string", "enum": ["pearson", "spearman", "kendall"]},
                    "threshold": {"type": "number", "description": "Only show pairs above this |correlation|."}
                }
            }
        ),
        types.Tool(
            name="run_sql_query",
            description="Run an ad-hoc SQL query. For inventory.db tables use table names directly: sales, purchases, begin_inventory, end_inventory, purchase_prices, vendor_invoice.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query to run."},
                    "use_db": {"type": "boolean", "description": "If true, query runs against inventory.db directly. If false, queries in-memory loaded dataframe as table 'data'."}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="generate_chart",
            description="Generate a basic chart (histogram, scatter, bar, box, line) and save to disk.",
            inputSchema={
                "type": "object",
                "properties": {
                    "chart_type": {"type": "string", "enum": ["histogram", "scatter", "bar", "box", "line", "heatmap"]},
                    "x":     {"type": "string", "description": "Column for X axis."},
                    "y":     {"type": "string", "description": "Column for Y axis (where applicable)."},
                    "hue":   {"type": "string", "description": "Column for color grouping (optional)."},
                    "title": {"type": "string", "description": "Chart title."}
                },
                "required": ["chart_type", "x"]
            }
        ),
        types.Tool(
            name="hypothesis_test",
            description="Run a statistical hypothesis test on the dataset.",
            inputSchema={
                "type": "object",
                "properties": {
                    "test":          {"type": "string", "enum": ["ttest_ind", "ttest_1samp", "chi2", "anova", "mannwhitney"]},
                    "column":        {"type": "string", "description": "Numeric column to test."},
                    "group_column":  {"type": "string", "description": "Categorical column defining groups."},
                    "expected_mean": {"type": "number", "description": "Expected mean for one-sample t-test."},
                    "alpha":         {"type": "number", "description": "Significance level (default: 0.05)."}
                },
                "required": ["test", "column"]
            }
        ),
        types.Tool(
            name="summarize_findings",
            description="Return a structured JSON summary of the loaded dataset and all saved charts.",
            inputSchema={"type": "object", "properties": {}}
        ),

        # ── New custom professional chart tools ───────────────────────────────
        types.Tool(
            name="chart_correlation_heatmap",
            description="Generate a professional styled correlation heatmap matching original analysis quality. Uses the loaded dataset or inventory.db table.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {"type": "string", "description": "Table name from inventory.db to use (optional, uses loaded df if not provided)."},
                    "method": {"type": "string", "enum": ["pearson", "spearman", "kendall"], "description": "Correlation method (default: pearson)."}
                }
            }
        ),
        types.Tool(
            name="chart_brand_scatter",
            description="Generate a professional scatter plot identifying brands for promotional or pricing adjustments — high margin but low sales brands highlighted in red.",
            inputSchema={
                "type": "object",
                "properties": {
                    "margin_col":    {"type": "string", "description": "Column name for profit margin (default: ProfitMargin)."},
                    "sales_col":     {"type": "string", "description": "Column name for total sales (default: TotalSalesDollars)."},
                    "margin_threshold": {"type": "number", "description": "High margin threshold % (default: 65)."},
                    "sales_threshold":  {"type": "number", "description": "Low sales threshold in $ (default: 1000)."}
                }
            }
        ),
        types.Tool(
            name="chart_confidence_interval",
            description="Generate a professional confidence interval comparison chart between two vendor groups — shows profit margin distributions with mean and CI lines overlaid.",
            inputSchema={
                "type": "object",
                "properties": {
                    "margin_col":       {"type": "string", "description": "Column name for profit margin (default: ProfitMargin)."},
                    "group_col":        {"type": "string", "description": "Column to define vendor groups (default: VendorName)."},
                    "top_n_vendors":    {"type": "integer", "description": "Number of top vendors by count to define 'Top Vendors' group (default: 10)."},
                    "alpha":            {"type": "number", "description": "Significance level for CI (default: 0.05)."}
                }
            }
        ),
        types.Tool(
            name="chart_pareto_vendor",
            description="Generate a professional Pareto chart showing cumulative vendor contribution to total purchases.",
            inputSchema={
                "type": "object",
                "properties": {
                    "vendor_col":    {"type": "string", "description": "Column name for vendor (default: VendorName)."},
                    "purchase_col":  {"type": "string", "description": "Column name for purchase amount (default: TotalPurchaseDollars)."},
                    "top_n":         {"type": "integer", "description": "Number of top vendors to display (default: 15)."}
                }
            }
        ),
        types.Tool(
            name="chart_bulk_purchasing",
            description="Generate a professional scatter plot showing the impact of bulk purchasing on unit price — reveals the diminishing returns curve.",
            inputSchema={
                "type": "object",
                "properties": {
                    "quantity_col":  {"type": "string", "description": "Column for order quantity (default: TotalPurchaseQuantity)."},
                    "price_col":     {"type": "string", "description": "Column for unit purchase price (default: PurchasePrice)."}
                }
            }
        ),
        types.Tool(
            name="chart_top_vendors_brands",
            description="Generate a professional side-by-side bar chart showing top vendors and top brands by total sales dollars.",
            inputSchema={
                "type": "object",
                "properties": {
                    "top_n": {"type": "integer", "description": "Number of top vendors/brands to show (default: 10)."}
                }
            }
        ),
    ]


# ══════════════════════════════════════════════════════════════════════════════
# TOOL IMPLEMENTATIONS
# ══════════════════════════════════════════════════════════════════════════════

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    global _df, _source_label, _engine

    try:

        # ── 1. load_dataset ───────────────────────────────────────────────────
        if name == "load_dataset":
            source = arguments["source"]
            table  = arguments.get("table")
            limit  = arguments.get("limit")

            if source.endswith(".csv"):
                _df = pd.read_csv(source, nrows=limit)
                _source_label = Path(source).name

            elif source.endswith((".db", ".sqlite")):
                if not table:
                    raise ValueError("Provide 'table' name for SQLite sources.")
                con = f"sqlite:///{source}"
                q = f"SELECT * FROM {table}" + (f" LIMIT {limit}" if limit else "")
                _df = pd.read_sql(q, create_engine(con))
                _source_label = f"{Path(source).name}::{table}"

            else:
                if not table:
                    raise ValueError("Provide 'table' name for database sources.")
                _engine = create_engine(source)
                q = f"SELECT * FROM {table}" + (f" LIMIT {limit}" if limit else "")
                _df = pd.read_sql(q, _engine)
                _source_label = f"db::{table}"

            result = {
                "status": "loaded",
                "source": _source_label,
                "rows": len(_df),
                "columns": list(_df.columns),
                "dtypes": _df.dtypes.astype(str).to_dict()
            }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


        # ── 2. profile_data ───────────────────────────────────────────────────
        elif name == "profile_data":
            df = _require_df()
            numeric = df.select_dtypes(include="number")
            profile = {
                "shape": {"rows": len(df), "columns": len(df.columns)},
                "dtypes": df.dtypes.astype(str).to_dict(),
                "null_counts": df.isnull().sum().to_dict(),
                "null_percent": (df.isnull().mean() * 100).round(2).to_dict(),
                "numeric_stats": json.loads(numeric.describe().round(4).to_json()),
                "cardinality": {c: int(df[c].nunique()) for c in df.columns},
                "sample_values": {c: df[c].dropna().head(5).tolist() for c in df.columns}
            }
            return [types.TextContent(type="text", text=json.dumps(profile, indent=2))]


        # ── 3. detect_outliers ────────────────────────────────────────────────
        elif name == "detect_outliers":
            df = _require_df()
            cols   = arguments.get("columns") or df.select_dtypes(include="number").columns.tolist()
            method = arguments.get("method", "both")
            results = {}

            for col in cols:
                series = df[col].dropna()
                col_result = {}

                if method in ("iqr", "both"):
                    Q1, Q3 = series.quantile(0.25), series.quantile(0.75)
                    IQR = Q3 - Q1
                    mask = (series < Q1 - 1.5 * IQR) | (series > Q3 + 1.5 * IQR)
                    col_result["iqr"] = {
                        "outlier_count": int(mask.sum()),
                        "outlier_pct": round(mask.mean() * 100, 2),
                        "bounds": {"lower": round(Q1 - 1.5 * IQR, 4), "upper": round(Q3 + 1.5 * IQR, 4)}
                    }

                if method in ("zscore", "both"):
                    z = np.abs(stats.zscore(series))
                    mask_z = z > 3
                    col_result["zscore"] = {
                        "outlier_count": int(mask_z.sum()),
                        "outlier_pct": round(mask_z.mean() * 100, 2),
                        "threshold": 3
                    }

                results[col] = col_result

            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]


        # ── 4. correlation_matrix ─────────────────────────────────────────────
        elif name == "correlation_matrix":
            df     = _require_df()
            method = arguments.get("method", "pearson")
            threshold = arguments.get("threshold", 0.0)

            numeric = df.select_dtypes(include="number")
            corr = numeric.corr(method=method).round(4)

            fig, ax = plt.subplots(figsize=(max(6, len(corr) * 0.8), max(5, len(corr) * 0.7)))
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm",
                        center=0, square=True, linewidths=0.5, ax=ax)
            ax.set_title(f"{method.capitalize()} Correlation Matrix")
            chart_path = _fig_to_path(fig, "correlation_matrix.png")

            pairs = []
            cols = corr.columns.tolist()
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    val = corr.iloc[i, j]
                    if abs(val) >= threshold:
                        pairs.append({"col1": cols[i], "col2": cols[j], "correlation": float(val)})
            pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

            result = {
                "method": method,
                "matrix": json.loads(corr.to_json()),
                "strong_pairs": pairs[:20],
                "chart_saved_to": chart_path
            }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


        # ── 5. run_sql_query ──────────────────────────────────────────────────
        elif name == "run_sql_query":
            query  = arguments["query"]
            use_db = arguments.get("use_db", True)

            if use_db:
                engine = _get_db_engine()
            else:
                df = _require_df()
                engine = create_engine("sqlite:///:memory:")
                df.to_sql("data", engine, index=False, if_exists="replace")

            with engine.connect() as conn:
                result_df = pd.read_sql(text(query), conn)

            result = {
                "rows_returned": len(result_df),
                "columns": list(result_df.columns),
                "data": json.loads(result_df.head(500).to_json(orient="records"))
            }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


        # ── 6. generate_chart ─────────────────────────────────────────────────
        elif name == "generate_chart":
            df         = _require_df()
            chart_type = arguments["chart_type"]
            x          = arguments["x"]
            y          = arguments.get("y")
            hue        = arguments.get("hue")
            title      = arguments.get("title", f"{chart_type.capitalize()} — {x}")

            fig, ax = plt.subplots(figsize=(10, 6))
            sns.set_theme(style="whitegrid")

            if chart_type == "histogram":
                sns.histplot(df, x=x, hue=hue, kde=True, ax=ax)
            elif chart_type == "scatter":
                if not y:
                    raise ValueError("'y' required for scatter.")
                sns.scatterplot(df, x=x, y=y, hue=hue, alpha=0.7, ax=ax)
            elif chart_type == "bar":
                if y:
                    sns.barplot(df, x=x, y=y, hue=hue, ax=ax)
                else:
                    df[x].value_counts().head(20).plot.bar(ax=ax)
            elif chart_type == "box":
                if y:
                    sns.boxplot(df, x=x, y=y, hue=hue, ax=ax)
                else:
                    sns.boxplot(df, y=x, ax=ax)
            elif chart_type == "line":
                if not y:
                    raise ValueError("'y' required for line.")
                sns.lineplot(df, x=x, y=y, hue=hue, ax=ax)
            elif chart_type == "heatmap":
                pivot = df.pivot_table(values=y, index=x, columns=hue, aggfunc="mean") \
                    if (y and hue) else df.select_dtypes("number").corr()
                sns.heatmap(pivot, annot=True, fmt=".2f", cmap="YlOrRd", ax=ax)

            ax.set_title(title)
            fname = f"chart_{chart_type}_{x}.png"
            path  = _fig_to_path(fig, fname)

            return [types.TextContent(type="text", text=json.dumps({
                "status": "chart_saved", "path": path, "chart_type": chart_type
            }, indent=2))]


        # ── 7. hypothesis_test ────────────────────────────────────────────────
        elif name == "hypothesis_test":
            df       = _require_df()
            test     = arguments["test"]
            col      = arguments["column"]
            group_col = arguments.get("group_column")
            alpha    = arguments.get("alpha", 0.05)
            series   = df[col].dropna()

            result = {"test": test, "column": col, "alpha": alpha}

            if test == "ttest_1samp":
                mu = arguments.get("expected_mean", 0)
                stat, p = stats.ttest_1samp(series, mu)
                result.update({"statistic": round(stat, 6), "p_value": round(p, 6),
                               "expected_mean": mu, "sample_mean": round(series.mean(), 6)})

            elif test in ("ttest_ind", "mannwhitney", "anova"):
                if not group_col:
                    raise ValueError(f"'group_column' required for {test}.")
                groups = [g.dropna().values for _, g in df.groupby(group_col)[col]]
                if test == "ttest_ind":
                    if len(groups) != 2:
                        raise ValueError("ttest_ind requires exactly 2 groups.")
                    stat, p = stats.ttest_ind(*groups)
                elif test == "mannwhitney":
                    if len(groups) != 2:
                        raise ValueError("mannwhitney requires exactly 2 groups.")
                    stat, p = stats.mannwhitneyu(*groups)
                elif test == "anova":
                    stat, p = stats.f_oneway(*groups)
                result.update({"statistic": round(float(stat), 6), "p_value": round(float(p), 6),
                               "group_column": group_col, "groups": len(groups)})

            elif test == "chi2":
                if not group_col:
                    raise ValueError("'group_column' required for chi2.")
                ct = pd.crosstab(df[col], df[group_col])
                stat, p, dof, _ = stats.chi2_contingency(ct)
                result.update({"statistic": round(stat, 6), "p_value": round(p, 6), "dof": dof})

            result["reject_null"] = result["p_value"] < alpha
            result["interpretation"] = (
                f"Reject H₀ at α={alpha} (p={result['p_value']})" if result["reject_null"]
                else f"Fail to reject H₀ at α={alpha} (p={result['p_value']})"
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


        # ── 8. summarize_findings ─────────────────────────────────────────────
        elif name == "summarize_findings":
            df = _df
            summary = {
                "dataset": _source_label or "none",
                "shape": {"rows": len(df), "columns": len(df.columns)} if df is not None else None,
                "columns": list(df.columns) if df is not None else [],
                "numeric_columns": list(df.select_dtypes("number").columns) if df is not None else [],
                "categorical_columns": list(df.select_dtypes(["object", "category"]).columns) if df is not None else [],
                "null_summary": df.isnull().sum().to_dict() if df is not None else {},
                "outputs_directory": str(OUTPUT_DIR.resolve()),
                "saved_charts": [str(p) for p in OUTPUT_DIR.glob("*.png")]
            }
            return [types.TextContent(type="text", text=json.dumps(summary, indent=2))]


        # ══════════════════════════════════════════════════════════════════════
        # NEW PROFESSIONAL CHART TOOLS
        # ══════════════════════════════════════════════════════════════════════

        # ── 9. chart_correlation_heatmap ──────────────────────────────────────
        elif name == "chart_correlation_heatmap":
            table  = arguments.get("table")
            method = arguments.get("method", "pearson")

            if table:
                engine = _get_db_engine()
                df = pd.read_sql(f"SELECT * FROM {table}", engine)
            else:
                df = _require_df()

            numeric = df.select_dtypes(include="number")
            corr = numeric.corr(method=method)

            fig, ax = plt.subplots(figsize=(16, 13))
            mask = np.zeros_like(corr, dtype=bool)

            sns.heatmap(
                corr,
                annot=True,
                fmt=".2f",
                cmap="RdBu_r",
                center=0,
                vmin=-1, vmax=1,
                square=True,
                linewidths=0.5,
                linecolor="white",
                annot_kws={"size": 9, "weight": "bold"},
                cbar_kws={"shrink": 0.8, "aspect": 30},
                ax=ax
            )

            ax.set_title("correlation Heatmap", fontsize=16, fontweight="bold", pad=20)
            ax.tick_params(axis="x", rotation=45, labelsize=9)
            ax.tick_params(axis="y", rotation=0,  labelsize=9)
            plt.tight_layout()

            path = _fig_to_path(fig, "professional_correlation_heatmap.png")
            return [types.TextContent(type="text", text=json.dumps({
                "status": "chart_saved",
                "chart": "Professional Correlation Heatmap",
                "path": path,
                "note": f"Used {method} correlation on {len(numeric.columns)} numeric columns"
            }, indent=2))]


        # ── 10. chart_brand_scatter ───────────────────────────────────────────
        elif name == "chart_brand_scatter":
            margin_col        = arguments.get("margin_col", "ProfitMargin")
            sales_col         = arguments.get("sales_col", "TotalSalesDollars")
            margin_threshold  = arguments.get("margin_threshold", 65)
            sales_threshold   = arguments.get("sales_threshold", 1000)

            # Try loaded df first, fall back to purchase_prices table
            if _df is not None and margin_col in _df.columns and sales_col in _df.columns:
                df = _df.copy()
            else:
                engine = _get_db_engine()
                # Join purchases with sales to get margin + sales data
                query = """
                    SELECT pp.Description, pp.PurchasePrice,
                           SUM(s.SalesQuantity * s.SalesPrice) as TotalSalesDollars,
                           AVG((s.SalesPrice - pp.PurchasePrice) / NULLIF(s.SalesPrice, 0) * 100) as ProfitMargin
                    FROM purchase_prices pp
                    LEFT JOIN sales s ON pp.Description = s.Description
                    WHERE s.SalesPrice > 0 AND pp.PurchasePrice > 0
                    GROUP BY pp.Description, pp.PurchasePrice
                    HAVING ProfitMargin > 0
                """
                df = pd.read_sql(query, engine)
                margin_col = "ProfitMargin"
                sales_col  = "TotalSalesDollars"

            df = df.dropna(subset=[margin_col, sales_col])
            df = df[df[margin_col] > 0]

            # Identify target brands
            target_mask = (df[margin_col] > margin_threshold) & (df[sales_col] < sales_threshold)
            target_count = target_mask.sum()

            fig, ax = plt.subplots(figsize=(14, 8))

            # All brands — blue
            ax.scatter(
                df.loc[~target_mask, sales_col],
                df.loc[~target_mask, margin_col],
                alpha=0.3, s=30, color="#6B8DD6", label="All Brands", zorder=2
            )

            # Target brands — red
            ax.scatter(
                df.loc[target_mask, sales_col],
                df.loc[target_mask, margin_col],
                alpha=0.85, s=60, color="#E8162B", label="Target Brands",
                edgecolors="darkred", linewidths=0.5, zorder=3
            )

            # Threshold lines
            ax.axhline(y=margin_threshold, color="black", linestyle="--",
                       linewidth=1.5, label="High Margin Threshold", zorder=4)
            ax.axvline(x=sales_threshold, color="black", linestyle="--",
                       linewidth=1.5, label="Low Sales Threshold", zorder=4)

            ax.set_xlabel("Total Sales ($)", fontsize=12)
            ax.set_ylabel("Profit Margin (%)", fontsize=12)
            ax.set_title("Brands for Promotional or Pricing Adjustments", fontsize=14, fontweight="bold")
            ax.legend(loc="upper right", fontsize=10, framealpha=0.9)
            ax.grid(True, alpha=0.3)
            ax.set_xlim(left=0)
            ax.set_ylim(bottom=0)

            plt.tight_layout()
            path = _fig_to_path(fig, "professional_brand_scatter.png")

            return [types.TextContent(type="text", text=json.dumps({
                "status": "chart_saved",
                "chart": "Brand Promotional Scatter Plot",
                "path": path,
                "target_brands_identified": int(target_count),
                "margin_threshold": margin_threshold,
                "sales_threshold": sales_threshold,
                "note": f"{target_count} brands have margin > {margin_threshold}% but sales < ${sales_threshold}"
            }, indent=2))]


        # ── 11. chart_confidence_interval ─────────────────────────────────────
        elif name == "chart_confidence_interval":
            margin_col    = arguments.get("margin_col", "ProfitMargin")
            group_col     = arguments.get("group_col", "VendorName")
            top_n_vendors = arguments.get("top_n_vendors", 10)
            alpha         = arguments.get("alpha", 0.05)

            if _df is not None and margin_col in _df.columns and group_col in _df.columns:
                df = _df.copy()
            else:
                engine = _get_db_engine()
                query = f"""
                    SELECT pp.VendorName,
                           AVG((s.SalesPrice - pp.PurchasePrice) / NULLIF(s.SalesPrice, 0) * 100) as ProfitMargin,
                           COUNT(*) as RecordCount
                    FROM purchase_prices pp
                    LEFT JOIN sales s ON pp.Description = s.Description
                    WHERE s.SalesPrice > 0 AND pp.PurchasePrice > 0
                    GROUP BY pp.VendorName
                    HAVING ProfitMargin > 0 AND ProfitMargin < 100
                """
                df = pd.read_sql(query, engine)
                margin_col = "ProfitMargin"
                group_col  = "VendorName"

            df = df.dropna(subset=[margin_col, group_col])
            df = df[df[margin_col].between(0, 100)]

            # Split into top and low vendor groups
            vendor_counts = df[group_col].value_counts()
            top_vendors   = vendor_counts.head(top_n_vendors).index.tolist()

            top_group = df[df[group_col].isin(top_vendors)][margin_col].dropna()
            low_group = df[~df[group_col].isin(top_vendors)][margin_col].dropna()

            def ci(data, alpha):
                n    = len(data)
                mean = data.mean()
                se   = stats.sem(data)
                t    = stats.t.ppf(1 - alpha / 2, df=n - 1)
                return mean, mean - t * se, mean + t * se

            top_mean, top_lo, top_hi = ci(top_group, alpha)
            low_mean, low_lo, low_hi = ci(low_group, alpha)

            # ── Plot ──
            fig, ax = plt.subplots(figsize=(14, 7))

            # Histograms
            bins = np.linspace(0, 100, 51)
            ax.hist(top_group, bins=bins, alpha=0.5, color="#4472C4",
                    label="Top Vendors", edgecolor="black", linewidth=0.3)
            ax.hist(low_group, bins=bins, alpha=0.5, color="#E8162B",
                    label="Low Vendors", edgecolor="black", linewidth=0.3)

            # KDE curves
            from scipy.stats import gaussian_kde
            for data, color in [(top_group, "#1F3F8F"), (low_group, "#8B0000")]:
                kde  = gaussian_kde(data, bw_method=0.3)
                x_range = np.linspace(0, 100, 300)
                y_kde   = kde(x_range)
                scale   = len(data) * (bins[1] - bins[0])
                ax.plot(x_range, y_kde * scale, color=color, linewidth=2.5)

            # CI lines — Top vendors (blue dashed)
            ax.axvline(top_lo,   color="#4472C4", linestyle="--", linewidth=1.5,
                       label=f"Top Lower: {top_lo:.2f}")
            ax.axvline(top_hi,   color="#4472C4", linestyle="--", linewidth=1.5,
                       label=f"Top Upper: {top_hi:.2f}")
            ax.axvline(top_mean, color="#4472C4", linestyle="-",  linewidth=2,
                       label=f"Top Mean: {top_mean:.2f}")

            # CI lines — Low vendors (red dashed)
            ax.axvline(low_lo,   color="#E8162B", linestyle="--", linewidth=1.5,
                       label=f"Low Lower: {low_lo:.2f}")
            ax.axvline(low_hi,   color="#E8162B", linestyle="--", linewidth=1.5,
                       label=f"Low Upper: {low_hi:.2f}")
            ax.axvline(low_mean, color="#E8162B", linestyle="-",  linewidth=2,
                       label=f"Low Mean: {low_mean:.2f}")

            ax.set_xlabel("Profit Margin (%)", fontsize=12)
            ax.set_ylabel("Frequency", fontsize=12)
            ax.set_title(
                f"Confidence Interval Comparison: Top vs. Low Vendors (Profit Margin)",
                fontsize=13, fontweight="bold"
            )
            ax.legend(loc="upper right", fontsize=8.5, framealpha=0.9,
                      ncol=2, bbox_to_anchor=(1.0, 1.0))
            ax.grid(True, alpha=0.3)
            plt.tight_layout()

            path = _fig_to_path(fig, "professional_confidence_interval.png")

            # t-test
            t_stat, p_val = stats.ttest_ind(top_group, low_group)

            return [types.TextContent(type="text", text=json.dumps({
                "status": "chart_saved",
                "chart": "Confidence Interval Comparison",
                "path": path,
                "top_vendors": {
                    "mean": round(top_mean, 2),
                    "ci_lower": round(top_lo, 2),
                    "ci_upper": round(top_hi, 2),
                    "n": len(top_group)
                },
                "low_vendors": {
                    "mean": round(low_mean, 2),
                    "ci_lower": round(low_lo, 2),
                    "ci_upper": round(low_hi, 2),
                    "n": len(low_group)
                },
                "hypothesis_test": {
                    "t_statistic": round(float(t_stat), 4),
                    "p_value": round(float(p_val), 6),
                    "reject_null": bool(p_val < alpha),
                    "interpretation": "Significant difference in margins" if p_val < alpha else "No significant difference"
                }
            }, indent=2))]


        # ── 12. chart_pareto_vendor ───────────────────────────────────────────
        elif name == "chart_pareto_vendor":
            vendor_col   = arguments.get("vendor_col", "VendorName")
            purchase_col = arguments.get("purchase_col", "TotalPurchaseDollars")
            top_n        = arguments.get("top_n", 15)

            if _df is not None and vendor_col in _df.columns and purchase_col in _df.columns:
                df = _df.copy()
            else:
                engine = _get_db_engine()
                query = f"""
                    SELECT VendorName,
                           SUM(Dollars) as TotalPurchaseDollars
                    FROM purchases
                    GROUP BY VendorName
                    ORDER BY TotalPurchaseDollars DESC
                    LIMIT {top_n}
                """
                df = pd.read_sql(query, engine)
                vendor_col   = "VendorName"
                purchase_col = "TotalPurchaseDollars"

            df = df.groupby(vendor_col)[purchase_col].sum().reset_index()
            df = df.sort_values(purchase_col, ascending=False).head(top_n)
            df["pct"]        = df[purchase_col] / df[purchase_col].sum() * 100
            df["cumulative"] = df["pct"].cumsum()

            fig, ax1 = plt.subplots(figsize=(16, 7))
            ax2 = ax1.twinx()

            bars = ax1.bar(range(len(df)), df["pct"], color="#4472C4", alpha=0.85, edgecolor="black", linewidth=0.5)
            ax2.plot(range(len(df)), df["cumulative"], color="#E8162B",
                     marker="o", markersize=5, linewidth=2, label="Cumulative %")
            ax2.axhline(y=80, color="gray", linestyle="--", linewidth=1, alpha=0.7)

            # Value labels on bars
            for i, (bar, pct) in enumerate(zip(bars, df["pct"])):
                ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                         f"{pct:.1f}%", ha="center", va="bottom", fontsize=7.5, fontweight="bold")

            ax1.set_xticks(range(len(df)))
            ax1.set_xticklabels(df[vendor_col], rotation=45, ha="right", fontsize=9)
            ax1.set_xlabel("Vendors", fontsize=11)
            ax1.set_ylabel("Purchase Contribution (%)", fontsize=11, color="#4472C4")
            ax2.set_ylabel("Cumulative Contribution (%)", fontsize=11, color="#E8162B")
            ax2.set_ylim(0, 110)
            ax1.set_title("Pareto Chart: Vendor Contribution to Total Purchases", fontsize=13, fontweight="bold")
            ax2.legend(loc="center right", fontsize=10)
            ax1.grid(axis="y", alpha=0.3)
            plt.tight_layout()

            path = _fig_to_path(fig, "professional_pareto_vendor.png")
            return [types.TextContent(type="text", text=json.dumps({
                "status": "chart_saved",
                "chart": "Pareto Vendor Contribution",
                "path": path,
                "top_vendor": df.iloc[0][vendor_col],
                "top_vendor_pct": round(df.iloc[0]["pct"], 2),
                "top_3_cumulative_pct": round(df.head(3)["pct"].sum(), 2),
                "top_10_cumulative_pct": round(df.head(10)["pct"].sum(), 2)
            }, indent=2))]


        # ── 13. chart_bulk_purchasing ─────────────────────────────────────────
        elif name == "chart_bulk_purchasing":
            quantity_col = arguments.get("quantity_col", "TotalPurchaseQuantity")
            price_col    = arguments.get("price_col", "PurchasePrice")

            if _df is not None and quantity_col in _df.columns and price_col in _df.columns:
                df = _df.copy()
            else:
                engine = _get_db_engine()
                query = """
                    SELECT Quantity as TotalPurchaseQuantity,
                           Dollars / NULLIF(Quantity, 0) as PurchasePrice
                    FROM purchases
                    WHERE Quantity > 0 AND Dollars > 0
                """
                df = pd.read_sql(query, engine)
                quantity_col = "TotalPurchaseQuantity"
                price_col    = "PurchasePrice"

            df = df.dropna(subset=[quantity_col, price_col])
            df = df[(df[price_col] > 0) & (df[quantity_col] > 0)]

            # Categorize order size
            q33, q66 = df[quantity_col].quantile(0.33), df[quantity_col].quantile(0.66)
            df["OrderSize"] = pd.cut(
                df[quantity_col],
                bins=[-np.inf, q33, q66, np.inf],
                labels=["Small", "Medium", "Large"]
            )

            fig, ax = plt.subplots(figsize=(12, 7))

            colors = {"Small": "#E8162B", "Medium": "#4472C4", "Large": "#70AD47"}
            for size, color in colors.items():
                mask = df["OrderSize"] == size
                ax.scatter(
                    df.loc[mask, quantity_col],
                    df.loc[mask, price_col],
                    alpha=0.4, s=20, color=color, label=size
                )

            ax.set_xlabel("Order Quantity", fontsize=12)
            ax.set_ylabel("Average Unit Purchase Price", fontsize=12)
            ax.set_title("Impact of Bulk Purchasing on Unit Price", fontsize=13, fontweight="bold")
            ax.legend(title="Order Size", fontsize=10, title_fontsize=10)
            ax.grid(True, alpha=0.3)

            # Cap y-axis at 95th percentile for readability
            ax.set_ylim(0, df[price_col].quantile(0.95) * 1.1)
            plt.tight_layout()

            path = _fig_to_path(fig, "professional_bulk_purchasing.png")
            return [types.TextContent(type="text", text=json.dumps({
                "status": "chart_saved",
                "chart": "Bulk Purchasing Impact",
                "path": path,
                "order_size_boundaries": {
                    "small_max": round(q33, 0),
                    "medium_max": round(q66, 0)
                }
            }, indent=2))]


        # ── 14. chart_top_vendors_brands ──────────────────────────────────────
        elif name == "chart_top_vendors_brands":
            top_n = arguments.get("top_n", 10)
            engine = _get_db_engine()

            vendor_query = f"""
                SELECT VendorName, SUM(SalesDollars) as TotalSales
                FROM sales
                GROUP BY VendorName
                ORDER BY TotalSales DESC
                LIMIT {top_n}
            """
            brand_query = f"""
                SELECT Description, SUM(SalesDollars) as TotalSales
                FROM sales
                GROUP BY Description
                ORDER BY TotalSales DESC
                LIMIT {top_n}
            """

            try:
                vendor_df = pd.read_sql(vendor_query, engine)
                brand_df  = pd.read_sql(brand_query, engine)
            except Exception:
                # Try alternate column names
                vendor_query = vendor_query.replace("SalesDollars", "Dollars")
                brand_query  = brand_query.replace("SalesDollars", "Dollars")
                vendor_df = pd.read_sql(vendor_query, engine)
                brand_df  = pd.read_sql(brand_query, engine)

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

            # Top Vendors
            vendor_df_sorted = vendor_df.sort_values("TotalSales")
            ax1.barh(vendor_df_sorted.iloc[:, 0], vendor_df_sorted["TotalSales"] / 1e6,
                     color="#4472C4", edgecolor="black", linewidth=0.5)
            for i, val in enumerate(vendor_df_sorted["TotalSales"] / 1e6):
                ax1.text(val + 0.2, i, f"{val:.2f}M", va="center", fontsize=9)
            ax1.set_xlabel("Total Sales ($M)", fontsize=11)
            ax1.set_title(f"Top {top_n} Vendors by Sales", fontsize=12, fontweight="bold")
            ax1.grid(axis="x", alpha=0.3)

            # Top Brands
            brand_df_sorted = brand_df.sort_values("TotalSales")
            ax2.barh(brand_df_sorted.iloc[:, 0], brand_df_sorted["TotalSales"] / 1e6,
                     color="#E8162B", edgecolor="black", linewidth=0.5)
            for i, val in enumerate(brand_df_sorted["TotalSales"] / 1e6):
                ax2.text(val + 0.05, i, f"{val:.2f}M", va="center", fontsize=9)
            ax2.set_xlabel("Total Sales ($M)", fontsize=11)
            ax2.set_title(f"Top {top_n} Brands by Sales", fontsize=12, fontweight="bold")
            ax2.grid(axis="x", alpha=0.3)

            plt.suptitle("Top Vendors & Brands Performance Overview", fontsize=14,
                         fontweight="bold", y=1.02)
            plt.tight_layout()

            path = _fig_to_path(fig, "professional_top_vendors_brands.png")
            return [types.TextContent(type="text", text=json.dumps({
                "status": "chart_saved",
                "chart": "Top Vendors & Brands",
                "path": path,
                "top_vendor": vendor_df.iloc[0, 0] if len(vendor_df) > 0 else "N/A",
                "top_brand":  brand_df.iloc[0, 0]  if len(brand_df)  > 0 else "N/A"
            }, indent=2))]


        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        error = {"error": str(e), "traceback": traceback.format_exc()}
        return [types.TextContent(type="text", text=json.dumps(error, indent=2))]


# ── Entry point ───────────────────────────────────────────────────────────────
async def main():
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())