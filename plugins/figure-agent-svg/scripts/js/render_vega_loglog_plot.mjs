import * as vega from "vega";
import { compile } from "vega-lite";

async function readJsonStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  const text = chunks.join("").trim();
  return text ? JSON.parse(text) : {};
}

function defaultData() {
  return [
    { series: "Power-law", x: 1, y: 120 },
    { series: "Power-law", x: 2, y: 75 },
    { series: "Power-law", x: 5, y: 35 },
    { series: "Power-law", x: 10, y: 19 },
    { series: "Power-law", x: 20, y: 11 },
    { series: "Power-law", x: 50, y: 5.2 },
    { series: "Power-law", x: 100, y: 3.1 },
    { series: "Debye reference", x: 1, y: 95 },
    { series: "Debye reference", x: 2, y: 86 },
    { series: "Debye reference", x: 5, y: 60 },
    { series: "Debye reference", x: 10, y: 32 },
    { series: "Debye reference", x: 20, y: 12 },
    { series: "Debye reference", x: 50, y: 3.8 },
    { series: "Debye reference", x: 100, y: 2.6 },
  ];
}

function lineDashExpr() {
  return "datum.series === 'Debye reference' ? [7, 6] : [1, 0]";
}

const payload = await readJsonStdin();
const width = Number(payload.width ?? 360);
const height = Number(payload.height ?? 220);
const colors = payload.colors ?? ["#2563EB", "#6B7280"];
const values = Array.isArray(payload.data) && payload.data.length > 0 ? payload.data : defaultData();

const spec = {
  $schema: "https://vega.github.io/schema/vega-lite/v6.json",
  width,
  height,
  autosize: { type: "fit", contains: "padding" },
  padding: 5,
  background: "#FFFFFF",
  data: { values },
  config: {
    font: "Arial",
    axis: {
      domainColor: "#111827",
      domainWidth: 1.2,
      grid: true,
      gridColor: "#E5E7EB",
      gridWidth: 0.8,
      labelColor: "#111827",
      labelFont: "Arial",
      labelFontSize: 11,
      tickColor: "#111827",
      tickSize: 4,
      titleColor: "#111827",
      titleFont: "Arial",
      titleFontSize: 12,
    },
    view: { stroke: "#111827", strokeWidth: 1.2 },
  },
  layer: [
    {
      mark: {
        type: "line",
        point: { filled: true, size: 50 },
        strokeWidth: 2.4,
        interpolate: "monotone",
      },
      encoding: {
        x: {
          field: "x",
          type: "quantitative",
          scale: { type: "log", domain: [1, 100] },
          axis: { title: payload.x_label ?? "log t", values: [1, 2, 5, 10, 20, 50, 100] },
        },
        y: {
          field: "y",
          type: "quantitative",
          scale: { type: "log", domain: [2, 140] },
          axis: { title: payload.y_label ?? "log I", values: [2, 5, 10, 20, 50, 100] },
        },
        color: {
          field: "series",
          type: "nominal",
          legend: null,
          scale: {
            domain: ["Power-law", "Debye reference"],
            range: colors,
          },
        },
        strokeDash: {
          condition: { test: lineDashExpr(), value: [7, 6] },
          value: [1, 0],
        },
      },
    },
  ],
};

const runtime = vega.parse(compile(spec).spec);
const view = new vega.View(runtime, { renderer: "none" });
const svg = await view.toSVG();
process.stdout.write(svg);
