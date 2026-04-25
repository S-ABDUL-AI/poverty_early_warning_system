"""
report_generator.py
McKinsey-style PDF report for Safety Net Risk Monitor
Built by Sherriff Abdul-Hamid
"""

import io
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph,
    Spacer, Table, TableStyle, Image, KeepTogether,
    HRFlowable, PageBreak,
)
from reportlab.pdfgen import canvas as rl_canvas

# ── DESIGN TOKENS ──────────────────────────────────────────────
NAVY     = colors.HexColor("#0A1F44")
NAVY_MID = colors.HexColor("#152B5C")
GOLD     = colors.HexColor("#C9A84C")
GOLD_LT  = colors.HexColor("#FDF6E3")
INK      = colors.HexColor("#1A1A1A")
BODY_C   = colors.HexColor("#2C3E50")
MUTED    = colors.HexColor("#6B7280")
RED_C    = colors.HexColor("#C8382A")
RED_LT   = colors.HexColor("#FEF2F2")
GREEN_C  = colors.HexColor("#1A7A2E")
GREEN_LT = colors.HexColor("#F0FDF4")
AMBER_C  = colors.HexColor("#B8560A")
AMBER_LT = colors.HexColor("#FFFBEB")
RULE_C   = colors.HexColor("#E2E6EC")
WHITE_C  = colors.white
LIGHT_BG = colors.HexColor("#F7F9FC")

BAND_RLCOLOR = {"High": RED_C,   "Medium": AMBER_C,   "Low": GREEN_C}
BAND_RLBG    = {"High": RED_LT,  "Medium": AMBER_LT,  "Low": GREEN_LT}

W, H = A4
ML, MR = 18*mm, 18*mm
CONTENT_W = W - ML - MR


# ── STYLES ────────────────────────────────────────────────────
def _S():
    def ps(name, **kw):
        return ParagraphStyle(name, **kw)
    return {
        "eyebrow":    ps("eyebrow",    fontName="Helvetica-Bold", fontSize=7,
                          textColor=GOLD, leading=10, spaceAfter=2),
        "cover_h1":   ps("cover_h1",   fontName="Times-Bold", fontSize=24,
                          textColor=WHITE_C, leading=28, spaceAfter=8),
        "cover_sub":  ps("cover_sub",  fontName="Helvetica", fontSize=10,
                          textColor=colors.HexColor("#CADCFC"), leading=14, spaceAfter=4),
        "cover_meta": ps("cover_meta", fontName="Helvetica", fontSize=8,
                          textColor=GOLD, leading=11),
        "h2":         ps("h2",         fontName="Times-Bold", fontSize=15,
                          textColor=INK, leading=19, spaceAfter=3),
        "h3":         ps("h3",         fontName="Helvetica-Bold", fontSize=10,
                          textColor=NAVY, leading=13, spaceAfter=2),
        "label":      ps("label",      fontName="Helvetica-Bold", fontSize=7,
                          textColor=MUTED, leading=9, spaceAfter=2),
        "body":       ps("body",       fontName="Helvetica", fontSize=9,
                          textColor=BODY_C, leading=13, spaceAfter=4),
        "body_sm":    ps("body_sm",    fontName="Helvetica", fontSize=8,
                          textColor=MUTED, leading=11, spaceAfter=2),
        "italic_sm":  ps("italic_sm",  fontName="Helvetica-Oblique", fontSize=8,
                          textColor=MUTED, leading=10),
        "kpi_val":    ps("kpi_val",    fontName="Times-Bold", fontSize=21,
                          textColor=INK, leading=23, spaceAfter=0),
        "kpi_lbl":    ps("kpi_lbl",    fontName="Helvetica-Bold", fontSize=7,
                          textColor=MUTED, leading=9, spaceAfter=1),
        "kpi_sub":    ps("kpi_sub",    fontName="Helvetica", fontSize=7,
                          textColor=MUTED, leading=9, spaceAfter=0),
        "tbl_head":   ps("tbl_head",   fontName="Helvetica-Bold", fontSize=7,
                          textColor=WHITE_C, leading=9),
        "tbl_cell":   ps("tbl_cell",   fontName="Helvetica", fontSize=8,
                          textColor=BODY_C, leading=10),
        "tbl_bold":   ps("tbl_bold",   fontName="Helvetica-Bold", fontSize=8,
                          textColor=INK, leading=10),
        "insight_r":  ps("insight_r",  fontName="Helvetica-Bold", fontSize=9,
                          textColor=INK, leading=12),
        "insight_w":  ps("insight_w",  fontName="Helvetica", fontSize=8,
                          textColor=BODY_C, leading=11),
        "action":     ps("action",     fontName="Helvetica-Bold", fontSize=8,
                          textColor=NAVY, leading=11),
        "footer":     ps("footer",     fontName="Helvetica", fontSize=7,
                          textColor=MUTED, leading=9),
        "right":      ps("right",      fontName="Helvetica", fontSize=8,
                          textColor=BODY_C, leading=10, alignment=TA_RIGHT),
        "center":     ps("center",     fontName="Helvetica", fontSize=8,
                          textColor=BODY_C, leading=10, alignment=TA_CENTER),
    }


# ── HEADER / FOOTER CALLBACK ──────────────────────────────────
class _HF:
    def __init__(self, report_date, n_regions, model_match):
        self.report_date = report_date
        self.n_regions   = n_regions
        self.model_match = model_match

    def __call__(self, canv, doc):
        canv.saveState()
        canv.setStrokeColor(GOLD)
        canv.setLineWidth(2.5)
        canv.line(ML, H - 11*mm, W - MR, H - 11*mm)
        canv.setFont("Helvetica-Bold", 7)
        canv.setFillColor(NAVY)
        canv.drawString(ML, H - 9*mm, "SAFETY NET RISK MONITOR")
        canv.setFont("Helvetica", 7)
        canv.setFillColor(MUTED)
        canv.drawRightString(W - MR, H - 9*mm,
                             f"CONFIDENTIAL  |  {self.report_date}")
        canv.setStrokeColor(RULE_C)
        canv.setLineWidth(0.5)
        canv.line(ML, 13*mm, W - MR, 13*mm)
        canv.setFont("Helvetica", 6.5)
        canv.setFillColor(MUTED)
        canv.drawString(ML, 9.5*mm,
            "Built by Sherriff Abdul-Hamid  |  Obama Foundation Leader  |  USAID  UNDP  UKAID")
        canv.drawRightString(W - MR, 9.5*mm,
            f"Page {canv.getPageNumber()}  |  {self.n_regions} regions  |  "
            f"{self.model_match}% model match rate")
        canv.restoreState()


# ── CHARTS ────────────────────────────────────────────────────
def _vuln_chart(df) -> Image:
    df_c = df.sort_values("vulnerability_score")
    clr_map = {"High": "#C8382A", "Medium": "#B8560A", "Low": "#1A7A2E"}
    bar_colors = [clr_map[b] for b in df_c["risk_band"]]
    avg = df["vulnerability_score"].mean()
    n   = len(df_c)
    fig_h = max(3.8, n * 0.42)
    fig, ax = plt.subplots(figsize=(7.4, fig_h))
    bars = ax.barh(df_c["region"], df_c["vulnerability_score"],
                   color=bar_colors, height=0.62, zorder=3)
    for bar, val in zip(bars, df_c["vulnerability_score"]):
        ax.text(val + 0.8, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}", va="center", ha="left",
                fontsize=7.5, color="#1A1A1A", fontweight="bold")
    ax.axvline(avg, color="#6B7280", linestyle="--", linewidth=0.9, zorder=2)
    ax.text(avg + 0.3, n - 0.3, f"Avg {avg:.1f}",
            fontsize=7, color="#6B7280", va="top")
    ax.set_xlim(0, df["vulnerability_score"].max() * 1.22)
    ax.set_xlabel("Vulnerability Score (0-100)", fontsize=8, color="#6B7280")
    ax.tick_params(axis="y", labelsize=8)
    ax.tick_params(axis="x", labelsize=7.5)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.spines[["top", "right", "left"]].set_visible(False)
    patches = [mpatches.Patch(color=c, label=l)
               for l, c in [("High","#C8382A"),("Medium","#B8560A"),("Low","#1A7A2E")]]
    ax.legend(handles=patches, loc="lower right", fontsize=7,
              framealpha=0.9, edgecolor="#E2E6EC")
    plt.tight_layout(pad=0.5)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    img_h = max(58*mm, n * 10*mm)
    return Image(buf, width=CONTENT_W, height=img_h)


def _weight_chart() -> Image:
    indicators = ["Food price pressure (35%)", "Employment gap (30%)",
                  "Income pressure (25%)", "Housing cost (10%)"]
    weights = [0.35, 0.30, 0.25, 0.10]
    fig, ax = plt.subplots(figsize=(5.8, 2.4))
    bars = ax.barh(indicators, weights, color="#0A1F44", height=0.55)
    for bar, w in zip(bars, weights):
        ax.text(w + 0.005, bar.get_y() + bar.get_height() / 2,
                f"{w*100:.0f}%", va="center", ha="left",
                fontsize=9, color="#1A1A1A", fontweight="bold")
    ax.set_xlim(0, 0.48)
    ax.set_xlabel("Relative Weight", fontsize=8, color="#6B7280")
    ax.tick_params(labelsize=8.5)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.spines[["top", "right", "left"]].set_visible(False)
    plt.tight_layout(pad=0.4)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=CONTENT_W * 0.62, height=46*mm)


# ── HELPERS ───────────────────────────────────────────────────
def _rule(story):
    story.append(HRFlowable(width="100%", thickness=0.5, color=RULE_C,
                             spaceAfter=4, spaceBefore=2))

def _section(story, label, title, sub, S):
    story.append(Spacer(1, 6*mm))
    if label:
        story.append(Paragraph(label.upper(), S["label"]))
    story.append(Paragraph(title, S["h2"]))
    if sub:
        story.append(Paragraph(sub, S["body_sm"]))
    _rule(story)

def _kpi_row(story, kpis, S, accents=None):
    n = len(kpis)
    cw = CONTENT_W / n
    accents = accents or [NAVY] * n
    cells = []
    for (lbl, val, sub), acc in zip(kpis, accents):
        cells.append([
            Paragraph(lbl.upper(), S["kpi_lbl"]),
            Paragraph(val, S["kpi_val"]),
            Paragraph(sub, S["kpi_sub"]),
        ])
    tbl = Table([cells], colWidths=[cw] * n)
    border_cmds = [("LINEBELOW", (i, 0), (i, 0), 3.5, acc)
                   for i, acc in enumerate(accents)]
    tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND",    (0, 0), (-1, -1), WHITE_C),
        ("BOX",           (0, 0), (-1, -1), 0.5, RULE_C),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, RULE_C),
    ] + border_cmds))
    story.append(tbl)


# ── MAIN ──────────────────────────────────────────────────────
def build_report_bytes(df, model_match=81) -> bytes:
    buf         = io.BytesIO()
    report_date = date.today().strftime("%B %d, %Y")
    n_regions   = len(df)
    S           = _S()

    n_high   = int((df["risk_band"] == "High").sum())
    n_medium = int((df["risk_band"] == "Medium").sum())
    n_low    = int((df["risk_band"] == "Low").sum())
    pop_high = int(df[df["risk_band"] == "High"]["population"].sum())
    top_r    = df.iloc[0]
    pct_high = n_high / n_regions * 100
    pct_med  = (n_high + n_medium) / n_regions * 100
    top3food = df.head(3)["avg_food_price_index"].mean()
    top_action = top_r["recommended_action"].split("+")[0].strip()

    hf = _HF(report_date, n_regions, model_match)
    frame = Frame(ML, 17*mm, CONTENT_W, H - 17*mm - 15*mm, id="body")
    template = PageTemplate(id="main", frames=[frame], onPage=hf)
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=ML, rightMargin=MR,
        topMargin=15*mm, bottomMargin=17*mm,
    )
    doc.addPageTemplates([template])
    story = []

    # ─────────────────────────────────────────────────────────
    # PAGE 1: COVER
    # ─────────────────────────────────────────────────────────
    cover_inner = Table([[
        [Paragraph("SAFETY NET RISK MONITOR  |  SNAP &amp; FOOD SECURITY TARGETING",
                   S["eyebrow"]),
         Spacer(1, 3*mm),
         Paragraph("Community Vulnerability<br/>&amp; SNAP Risk Report", S["cover_h1"]),
         Spacer(1, 3*mm),
         Paragraph(
             "A proactive targeting brief for SNAP outreach coordinators, state food "
             "security program officers, and federal poverty reduction administrators. "
             "Combines food price pressure, employment rates, income levels, and housing "
             "costs into a composite vulnerability score with structured policy recommendations.",
             S["cover_sub"]),
         Spacer(1, 4*mm),
         Paragraph(
             f"{n_regions} regions  |  4 indicators  |  {model_match}% model match rate  |  "
             f"Report date: {report_date}",
             S["cover_meta"]),
         ]
    ]], colWidths=[CONTENT_W - 10*mm])
    cover_inner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("TOPPADDING",    (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LINEBEFORE",    (0, 0), (0, -1),  6, GOLD),
    ]))
    story.append(cover_inner)
    story.append(Spacer(1, 5*mm))

    # KPI row 1
    _kpi_row(story, [
        ("High-Vulnerability Regions", str(n_high),
         f"Score >= 65 -- priority SNAP action"),
        ("People in High-Risk Regions", f"~{pop_high/1e6:.0f}M",
         "Estimated population in highest band"),
        ("Top Focus Region", top_r["region"],
         f"Score: {top_r['vulnerability_score']}"),
        ("Model Match Rate", f"{model_match}%",
         "Held-out validation accuracy"),
    ], S, accents=[RED_C, GOLD, NAVY, GREEN_C])

    story.append(Spacer(1, 3*mm))

    # Band distribution table
    band_data = [
        [Paragraph("PRIORITY BAND", S["tbl_head"]),
         Paragraph("COUNT", S["tbl_head"]),
         Paragraph("% PANEL", S["tbl_head"]),
         Paragraph("RECOMMENDED STATUS", S["tbl_head"])],
        [Paragraph("HIGH", ParagraphStyle("h_", fontName="Helvetica-Bold",
                    fontSize=8, textColor=RED_C, leading=10)),
         Paragraph(str(n_high), S["tbl_cell"]),
         Paragraph(f"{n_high/n_regions*100:.0f}%", S["tbl_cell"]),
         Paragraph("Priority SNAP outreach -- act within 30 days", S["tbl_cell"])],
        [Paragraph("MEDIUM", ParagraphStyle("m_", fontName="Helvetica-Bold",
                    fontSize=8, textColor=AMBER_C, leading=10)),
         Paragraph(str(n_medium), S["tbl_cell"]),
         Paragraph(f"{n_medium/n_regions*100:.0f}%", S["tbl_cell"]),
         Paragraph("Expand eligibility outreach + monthly monitoring", S["tbl_cell"])],
        [Paragraph("LOW", ParagraphStyle("l_", fontName="Helvetica-Bold",
                    fontSize=8, textColor=GREEN_C, leading=10)),
         Paragraph(str(n_low), S["tbl_cell"]),
         Paragraph(f"{n_low/n_regions*100:.0f}%", S["tbl_cell"]),
         Paragraph("Sustain existing programs + early warning monitoring", S["tbl_cell"])],
    ]
    band_tbl = Table(band_data,
                     colWidths=[30*mm, 20*mm, 22*mm, CONTENT_W - 72*mm])
    band_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  NAVY),
        ("BACKGROUND",    (0, 1), (-1, 1),  RED_LT),
        ("BACKGROUND",    (0, 2), (-1, 2),  AMBER_LT),
        ("BACKGROUND",    (0, 3), (-1, 3),  GREEN_LT),
        ("LINEBEFORE",    (0, 1), (0, 1),   4, RED_C),
        ("LINEBEFORE",    (0, 2), (0, 2),   4, AMBER_C),
        ("LINEBEFORE",    (0, 3), (0, 3),   4, GREEN_C),
        ("GRID",          (0, 0), (-1, -1), 0.5, RULE_C),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(band_tbl)
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────
    # PAGE 2: POLICY BRIEF
    # ─────────────────────────────────────────────────────────
    _section(story, "Policy Brief", "Risk  |  Implication  |  Action Now",
             "Structured decision summary for program directors and policy teams.", S)

    cw3 = CONTENT_W / 3
    brief_tbl = Table([[
        [Paragraph("RISK", ParagraphStyle("rl", fontName="Helvetica-Bold",
                    fontSize=8, textColor=RED_C, leading=11)),
         Spacer(1, 2*mm),
         Paragraph(
             f"<b>{n_high} regions</b> ({pct_high:.0f}% of the panel) are in the highest "
             f"vulnerability band. Combined, they represent an estimated "
             f"<b>~{pop_high/1e6:.0f}M people</b> facing elevated food price pressure, "
             "low employment, and limited income capacity -- the conditions that most "
             "strongly predict SNAP enrollment gaps.",
             S["body"])],
        [Paragraph("IMPLICATION", ParagraphStyle("im", fontName="Helvetica-Bold",
                    fontSize=8, textColor=NAVY, leading=11)),
         Spacer(1, 2*mm),
         Paragraph(
             f"<b>{pct_med:.0f}% of regions</b> require active attention -- either immediate "
             f"SNAP outreach or structured monitoring. Top-3 regions average a food price "
             f"index of <b>{top3food:.1f}</b>, above the panel baseline, compounding cost-of-"
             "living pressure on households already at or near eligibility thresholds.",
             S["body"])],
        [Paragraph("ACTION NOW", ParagraphStyle("an", fontName="Helvetica-Bold",
                    fontSize=8, textColor=GREEN_C, leading=11)),
         Spacer(1, 2*mm),
         Paragraph(
             "(1) Deploy targeted SNAP outreach in all High-band regions within 30 days. "
             "(2) Schedule food and labour program confirmations for high-stress areas. "
             "(3) Set monthly review triggers for Medium-band regions. "
             "(4) Link disbursements to food-price and employment monitoring data.",
             S["body"])],
    ]], colWidths=[cw3, cw3, cw3])
    brief_tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("BACKGROUND",    (0, 0), (-1, -1), WHITE_C),
        ("BOX",           (0, 0), (-1, -1), 0.5, RULE_C),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, RULE_C),
        ("LINEABOVE",     (0, 0), (0, 0),   3.5, RED_C),
        ("LINEABOVE",     (1, 0), (1, 0),   3.5, NAVY),
        ("LINEABOVE",     (2, 0), (2, 0),   3.5, GREEN_C),
    ]))
    story.append(brief_tbl)

    story.append(Spacer(1, 4*mm))
    _kpi_row(story, [
        ("Priority Action (Now)", top_action,
         f"For top focus region: {top_r['region']}"),
        ("Expected Impact (Indicative)", "Lower food-cost pressure ~2%",
         "Indicative scenario, not causal guarantee"),
        ("Regions Needing Attention", str(n_high + n_medium),
         "High or medium vulnerability -- action or monitoring needed"),
    ], S, accents=[RED_C, AMBER_C, NAVY])
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────
    # PAGE 3: CHARTS
    # ─────────────────────────────────────────────────────────
    _section(story, "Charts", "Vulnerability Score by Region",
             "All regions ranked by composite score, color-coded by priority band.", S)
    story.append(_vuln_chart(df))

    story.append(Spacer(1, 5*mm))
    _section(story, "", "Indicator Weights and Methodology",
             "How the composite vulnerability score is constructed.", S)

    weight_row = Table([[
        _weight_chart(),
        [Paragraph("HOW THE SCORE IS BUILT", S["label"]),
         Spacer(1, 2*mm),
         Paragraph(
             "Four indicators, each normalised 0-100 and weighted by policy relevance. "
             "Higher scores indicate greater vulnerability to food insecurity.",
             S["body"]),
         Spacer(1, 2*mm),
         Paragraph("<b>Food price index (35%)</b> -- cost-of-food pressure vs. panel median", S["body"]),
         Paragraph("<b>Employment rate (30%)</b> -- labour market capacity (inverted)", S["body"]),
         Paragraph("<b>Income index (25%)</b> -- household income capacity (inverted)", S["body"]),
         Paragraph("<b>Housing cost index (10%)</b> -- cost-of-shelter burden", S["body"]),
         Spacer(1, 3*mm),
         Paragraph(
             "Score thresholds:  High >= 65  |  Medium >= 40  |  Low < 40",
             S["body"]),
         Spacer(1, 3*mm),
         Paragraph(
             f"Model match rate: <b>{model_match}%</b> on held-out validation regions.",
             S["body"]),
         ],
    ]], colWidths=[CONTENT_W * 0.60, CONTENT_W * 0.40])
    weight_row.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(weight_row)
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────
    # PAGE 4+: REGIONAL INSIGHTS
    # ─────────────────────────────────────────────────────────
    _section(story, "Regional Insights", "Plain-Language Read Per Region",
             "Score, reasoning, and recommended action for every region in the panel.", S)

    for _, row in df.iterrows():
        band = row["risk_band"]
        acc  = BAND_RLCOLOR[band]
        bg   = BAND_RLBG[band]
        pill_ps = ParagraphStyle("pill", fontName="Helvetica-Bold",
                                 fontSize=7, textColor=acc, leading=9,
                                 alignment=TA_RIGHT)
        meta_str = (
            f"Score: <b>{row['vulnerability_score']}</b>   "
            f"Food index: <b>{row['avg_food_price_index']:.1f}</b>   "
            f"Employment: <b>{row['avg_employment_rate']:.1f}%</b>   "
            f"Population: <b>{row['population']/1e6:.1f}M</b>"
        )
        row_tbl = Table([[
            [Paragraph(row["region"], S["insight_r"]),
             Paragraph(meta_str, S["body_sm"]),
             Spacer(1, 1.5*mm),
             Paragraph(row["why_this_outlook"], S["insight_w"]),
             Spacer(1, 1*mm),
             Paragraph(f"Recommended: {row['recommended_action']}", S["action"])],
            [Paragraph(band.upper(), pill_ps)],
        ]], colWidths=[CONTENT_W - 18*mm, 18*mm])
        row_tbl.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (0, -1),  9),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("BACKGROUND",    (0, 0), (-1, -1), bg),
            ("BOX",           (0, 0), (-1, -1), 0.5, RULE_C),
            ("LINEBEFORE",    (0, 0), (0, -1),  4, acc),
        ]))
        story.append(KeepTogether([row_tbl, Spacer(1, 2*mm)]))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────
    # FULL REGIONAL TABLE
    # ─────────────────────────────────────────────────────────
    _section(story, "Full Regional Panel",
             "All Regions Ranked by Vulnerability Score",
             "Complete dataset with scores, indicators, and recommended actions.", S)

    tbl_header = [
        Paragraph("RANK",       S["tbl_head"]),
        Paragraph("REGION",     S["tbl_head"]),
        Paragraph("BAND",       S["tbl_head"]),
        Paragraph("SCORE",      S["tbl_head"]),
        Paragraph("FOOD IDX",   S["tbl_head"]),
        Paragraph("EMPLOYMENT", S["tbl_head"]),
        Paragraph("POPULATION", S["tbl_head"]),
    ]
    tbl_rows = [tbl_header]
    for _, row in df.iterrows():
        band   = row["risk_band"]
        acc    = BAND_RLCOLOR[band]
        band_p = ParagraphStyle("bps", fontName="Helvetica-Bold",
                                fontSize=7, textColor=acc, leading=9)
        tbl_rows.append([
            Paragraph(str(int(row["rank"])),             S["tbl_cell"]),
            Paragraph(row["region"],                     S["tbl_bold"]),
            Paragraph(band,                              band_p),
            Paragraph(str(row["vulnerability_score"]),   S["tbl_bold"]),
            Paragraph(f"{row['avg_food_price_index']:.1f}", S["tbl_cell"]),
            Paragraph(f"{row['avg_employment_rate']:.1f}%", S["tbl_cell"]),
            Paragraph(f"{row['population']/1e6:.1f}M",   S["tbl_cell"]),
        ])

    col_w = [12*mm, 44*mm, 18*mm, 18*mm, 20*mm, 24*mm, CONTENT_W - 136*mm]
    full_tbl = Table(tbl_rows, colWidths=col_w, repeatRows=1)
    row_styles = [
        ("BACKGROUND",    (0, 0), (-1, 0),  NAVY),
        ("GRID",          (0, 0), (-1, -1), 0.4, RULE_C),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE_C, LIGHT_BG]),
    ]
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        clr = BAND_RLCOLOR[row["risk_band"]]
        row_styles.append(("LINEBEFORE", (0, i), (0, i), 3.5, clr))
    full_tbl.setStyle(TableStyle(row_styles))
    story.append(full_tbl)
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────
    # SCOPE NOTE & BYLINE
    # ─────────────────────────────────────────────────────────
    _section(story, "Methodology and Scope",
             "Scope Note, Limitations and Data Sources",
             "Caveats for programme directors and government partners.", S)

    scope_items = [
        ("Illustrative data",
         "Built-in figures are composite illustrations for product demonstration. "
         "For live SNAP targeting, replace with CSV data from state administrative records "
         "or connect to USDA Food and Nutrition Service administrative data sources."),
        ("Composite scoring",
         "The vulnerability score combines four indicators using a weighted linear model. "
         "Weights (35/30/25/10) reflect policy relevance, not causal impact estimates. "
         "Results should inform, not replace, professional judgement."),
        ("Impact caveats",
         "Expected impact figures are indicative scenarios based on prior programme "
         "evaluations. They are not causal guarantees and should be treated as "
         "directional guidance only."),
        ("Model match rate",
         f"The {model_match}% model match rate reflects performance on a held-out "
         "validation set of historical regions. Future performance may vary as economic "
         "conditions and programme contexts evolve."),
    ]
    for i, (title, text) in enumerate(scope_items):
        num_ps = ParagraphStyle("num", fontName="Times-Bold",
                                fontSize=16, textColor=GOLD, leading=18)
        sc = Table([[
            Paragraph(f"{i+1}", num_ps),
            [Paragraph(title, S["h3"]),
             Paragraph(text, S["body"])],
        ]], colWidths=[14*mm, CONTENT_W - 14*mm])
        sc.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_BG),
            ("BOX",           (0, 0), (-1, -1), 0.5, RULE_C),
            ("LINEBEFORE",    (0, 0), (0, -1),  3.5, GOLD),
        ]))
        story.append(sc)
        story.append(Spacer(1, 2*mm))

    story.append(Spacer(1, 6*mm))
    _rule(story)

    byline = Table([[
        [Paragraph("Built by Sherriff Abdul-Hamid",
                   ParagraphStyle("bln", fontName="Helvetica-Bold",
                                  fontSize=9, textColor=INK, leading=12)),
         Spacer(1, 1*mm),
         Paragraph(
             "Product leader specialising in government digital services, SNAP and "
             "safety net benefits delivery, and proactive targeting tools for "
             "underserved communities. Former Founder and CEO, Poverty 360 "
             "(25,000+ beneficiaries served).",
             S["body"]),
         Spacer(1, 2*mm),
         Paragraph(
             "Obama Foundation Leaders Award (Top 1.3%)  |  Mandela Washington Fellow  "
             "|  Harvard Business School  |  USAID  UNDP  UKAID",
             S["italic_sm"]),
         ],
        [Paragraph(
             f"Report generated: {report_date}<br/>"
             f"Regions analysed: {n_regions}<br/>"
             f"Model match rate: {model_match}%<br/>"
             "Data: Illustrative",
             ParagraphStyle("mr", fontName="Helvetica", fontSize=8,
                            textColor=MUTED, leading=12, alignment=TA_RIGHT)),
         ],
    ]], colWidths=[CONTENT_W * 0.68, CONTENT_W * 0.32])
    byline.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_BG),
        ("BOX",           (0, 0), (-1, -1), 0.5, RULE_C),
        ("LINEBEFORE",    (0, 0), (0, -1),  4, GOLD),
    ]))
    story.append(byline)

    doc.build(story)
    buf.seek(0)
    return buf.read()
