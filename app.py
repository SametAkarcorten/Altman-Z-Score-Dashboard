import marimo

app = marimo.App(title="Altman Z-Score Dashboard", width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import io
    from compute import compute_altman_z
    return mo, pd, go, make_subplots, io, compute_altman_z


@app.cell
def _(mo):
    mo.md("# 📊 Altman Z-Score Dashboard")


@app.cell
def _(mo):
    file = mo.ui.file(label="Upload CSV", filetypes=[".csv"])
    mo.vstack([file, mo.md("`company, working_capital, total_assets, retained_earnings, ebit, market_value_equity, total_liabilities, sales`")])


@app.cell
def _(file, pd, mo, compute_altman_z, io):
    uploaded = file.value
    if not uploaded:
        result = None
    else:
        try:
            result = compute_altman_z(pd.read_csv(io.BytesIO(uploaded[0].contents)))
        except Exception as e:
            mo.stop(True, mo.callout(mo.md(f"**Error:** {e}"), kind="danger"))
            result = None
    result


@app.cell
def _(result, mo):
    if result is None:
        mo.stop(True, mo.callout(mo.md("Upload a CSV to begin."), kind="info"))

    n = len(result)
    avg_z = result["z_score"].mean()
    counts = result["risk_zone"].value_counts()

    mo.hstack([
        mo.stat(label="Companies",   value=str(n)),
        mo.stat(label="Avg Z-Score", value=f"{avg_z:.2f}"),
        mo.stat(label="Safe",        value=str(counts.get("Safe", 0))),
        mo.stat(label="Grey Zone",   value=str(counts.get("Grey", 0))),
        mo.stat(label="Distress",    value=str(counts.get("Distress", 0))),
    ])


@app.cell
def _(result, mo):
    if result is None:
        mo.stop(True)
    zone_filter = mo.ui.dropdown(["All", "Safe", "Grey", "Distress"], value="All", label="Zone")
    sort_by = mo.ui.dropdown(["Z-Score ↓", "Z-Score ↑", "Company A→Z"], value="Z-Score ↓", label="Sort")
    mo.hstack([zone_filter, sort_by])


@app.cell
def _(result, zone_filter, sort_by, mo):
    if result is None:
        mo.stop(True)
    filtered = result if zone_filter.value == "All" else result[result["risk_zone"] == zone_filter.value]
    filtered = filtered.sort_values(
        "z_score", ascending=(sort_by.value == "Z-Score ↑")
    ) if "Z-Score" in sort_by.value else filtered.sort_values("company")
    filtered


@app.cell
def _(filtered, go, make_subplots, mo):
    if filtered is None or len(filtered) == 0:
        mo.stop(True)

    COLORS = {"Safe": "#639922", "Grey": "#888780", "Distress": "#E24B4A"}
    srt = filtered.sort_values("z_score", ascending=True)

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=("Z-Score by Company", "Risk Zones", "Distribution"),
        column_widths=[0.5, 0.25, 0.25],
        horizontal_spacing=0.06,
    )

    fig.add_trace(go.Bar(
        x=srt["z_score"], y=srt["company"], orientation="h",
        marker_color=[COLORS[z] for z in srt["risk_zone"]],
        text=srt["z_score"].round(2), textposition="outside",
        cliponaxis=False, showlegend=False,
    ), row=1, col=1)
    for thresh, col in [(1.81, "#E24B4A"), (2.99, "#639922")]:
        fig.add_shape(type="line", x0=thresh, x1=thresh, y0=-0.5, y1=len(srt)-0.5,
                      line=dict(color=col, width=1.5, dash="dot"), row=1, col=1)

    vc = filtered["risk_zone"].value_counts()
    fig.add_trace(go.Pie(
        labels=vc.index, values=vc.values,
        marker_colors=[COLORS[z] for z in vc.index],
        hole=0.55, textinfo="label+percent", showlegend=False,
    ), row=1, col=2)

    fig.add_trace(go.Histogram(
        x=filtered["z_score"], nbinsx=10,
        marker_color="#378ADD", marker_line_color="white", marker_line_width=1.5,
        showlegend=False,
    ), row=1, col=3)

    fig.update_layout(
        height=max(320, len(srt) * 34 + 100),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=40, t=50, b=20), bargap=0.18,
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", zeroline=False)
    fig.update_yaxes(showgrid=False)

    mo.ui.plotly(fig)


@app.cell
def _(result, mo):
    if result is None:
        mo.stop(True)
    mo.download(result.to_csv(index=False).encode(), filename="altman_z_results.csv", label="⬇️ Download results CSV")