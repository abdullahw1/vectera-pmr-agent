"""Portable vector exhibits, with the prior PMR's compact chart typography."""

import io
import math

import fitz
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, String, Rect
from reportlab.graphics.charts.barcharts import VerticalBarChart, HorizontalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib import colors

NAVY, GOLD = colors.HexColor("#1b2a4a"), colors.HexColor("#c7a14a")
PALETTE = [NAVY, GOLD, colors.HexColor("#587fa4"), colors.HexColor("#9caed1"), colors.HexColor("#b79250"), colors.HexColor("#8c96a8")]


def label(drawing, x, y, text, size=7, bold=False, color=NAVY):
    drawing.add(String(x, y, str(text), fontName="Helvetica-Bold" if bold else "Helvetica", fontSize=size, fillColor=color))


def legend(drawing, x, y, text, color):
    drawing.add(Rect(x, y, 5, 5, fillColor=color, strokeColor=None))
    label(drawing, x + 8, y, text, 7, color=color)


def chart_drawing(kind, data):
    drawing = Drawing(495, 180 if kind != "geography" else 200)
    drawing.hAlign = "LEFT"
    if kind == "property":
        label(drawing, 24, 167, "Property Type Diversification", 10, True)
        rows = data["diversification"][kind]
        chart = Pie()
        chart.x, chart.y, chart.width, chart.height = 24, 14, 140, 140
        chart.data = [r["value"] for r in rows]
        chart.labels = []
        chart.slices.strokeWidth = 0.4
        chart.slices.strokeColor = colors.white
        for index, row in enumerate(rows):
            color = PALETTE[index % len(PALETTE)]
            chart.slices[index].fillColor = color
            legend(drawing, 196, 139 - 15 * index, f"{row['label']} - {row['value']:.1f}%", color)
        drawing.add(chart)
        return drawing
    if kind == "annual":
        label(drawing, 44, 166, "Annualized Time-Weighted Return (net, %)", 10, True)
        legend(drawing, 292, 167, "Portfolio", NAVY)
        legend(drawing, 352, 167, data["portfolio"]["benchmark"], GOLD)
        rows = data["portfolio"]["annual"]
        chart = VerticalBarChart()
        chart.x, chart.y, chart.width, chart.height = 44, 40, 350, 110
        chart.data = [[r["value"] for r in rows], [r["benchmark"] for r in rows]]
        chart.categoryAxis.categoryNames = [f"{r['horizon']}-Yr" for r in rows]
        chart.bars[0].fillColor, chart.bars[1].fillColor = NAVY, GOLD
        values = [v for series in chart.data for v in series]
        chart.valueAxis.valueMin = min(0, math.floor(min(values) / 2) * 2)
        chart.valueAxis.valueMax = max(2, math.ceil(max(values) / 2) * 2)
        chart.valueAxis.valueStep = 2
        chart.barLabels.fontName, chart.barLabels.fontSize = "Helvetica", 7
        chart.barLabelFormat = "%.1f"
        chart.barLabels.nudge = 4
        chart.categoryAxis.labelAxisMode = "low"
        for series_index, values in enumerate(chart.data):
            for index, value in enumerate(values):
                chart.barLabels[series_index, index].boxAnchor = "s" if value >= 0 else "n"
                chart.barLabels[series_index, index].nudge = 4 if value >= 0 else 10
        chart.groupSpacing, chart.barSpacing = 24, 6
    elif kind == "allocation":
        label(drawing, 44, 166, "Target Allocation vs Net Asset Value ($MM)", 10, True)
        legend(drawing, 292, 167, "Target allocation", NAVY)
        legend(drawing, 402, 167, "NAV", GOLD)
        rows = data["history"]
        chart = HorizontalLineChart()
        chart.x, chart.y, chart.width, chart.height = 44, 40, 350, 110
        chart.data = [[r["target"] for r in rows], [r["nav"] for r in rows]]
        chart.categoryAxis.categoryNames = [r["quarter"] for r in rows]
        chart.lines[0].strokeColor, chart.lines[1].strokeColor = NAVY, GOLD
        chart.lines.strokeWidth = 1.3
        values = [v for series in chart.data for v in series]
        step = max(10, math.ceil((max(values) - min(values)) / 50) * 10)
        chart.valueAxis.valueMin = math.floor(min(values) / step) * step - step
        chart.valueAxis.valueMax = math.ceil(max(values) / step) * step + step
        chart.valueAxis.valueStep = step
    else:
        label(drawing, 24, 187, "Geographic Diversification (% of market value)", 10, True)
        rows = sorted(data["diversification"][kind], key=lambda r: (r["value"], r["label"]))
        chart = HorizontalBarChart()
        chart.x, chart.y, chart.width, chart.height = 98, 20, 298, 155
        chart.data = [[r["value"] for r in rows]]
        chart.categoryAxis.categoryNames = [r["label"] for r in rows]
        chart.bars[0].fillColor = NAVY
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = math.ceil(max(r["value"] for r in rows) / 5) * 5
        chart.valueAxis.valueStep = 5
        chart.barLabelFormat = "%.1f%%"
        chart.barLabels.fontName, chart.barLabels.fontSize = "Helvetica", 7
        chart.barLabels.nudge = 4
        chart.barLabels.boxAnchor = "w"
        chart.barLabels.textAnchor = "start"
    chart.categoryAxis.labels.fontName = chart.valueAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = chart.valueAxis.labels.fontSize = 7
    chart.categoryAxis.strokeWidth = chart.valueAxis.strokeWidth = 0.6
    chart.valueAxis.visibleGrid = False
    drawing.add(chart)
    return drawing


def chart_preview(kind, data):
    drawing = chart_drawing(kind, data)
    with fitz.open(stream=renderPDF.drawToString(drawing), filetype="pdf") as document:
        return io.BytesIO(document[0].get_pixmap(matrix=fitz.Matrix(160 / 72, 160 / 72)).tobytes("png"))
