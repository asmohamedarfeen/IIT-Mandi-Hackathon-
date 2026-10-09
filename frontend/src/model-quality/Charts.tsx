import { useId } from "react";
import { displayMetric } from "./hooks";
import type { PlotSeries } from "./types";

export function Charts({ kind, series, baseline }: { kind: "roc" | "pr" | "calibration" | "histogram" | "threshold"; series: PlotSeries[]; baseline?: number }) {
  const id = useId();
  const labels = {
    roc: ["ROC curve", "False positive rate", "Sensitivity"],
    pr: ["Precision–recall curve", "Recall", "Precision"],
    calibration: ["Calibration curve", "Mean predicted probability", "Observed positive fraction"],
    histogram: ["Probability distribution", "Predicted probability", "Held-out records"],
    threshold: ["Threshold trade-off", "Decision threshold", "Metric value"],
  }[kind];
  const valid = series.map(item => ({...item,points:item.points.filter(point=>Number.isFinite(point.x) && Number.isFinite(point.y))})).filter(item=>item.points.length);
  if (!valid.length) return <p className="mq-unavailable">Unavailable · no saved {labels[0].toLowerCase()} data for this selection.</p>;
  const maxY = kind === "histogram" ? Math.max(...valid.flatMap(item=>item.points.map(point=>point.y)),1) : 1;
  const x = (value:number) => 64 + value * 440;
  const y = (value:number) => 262 - value / maxY * 220;
  return <div className="mq-chart">
    <svg viewBox="0 0 560 320" role="img" aria-labelledby={`${id}-title ${id}-desc`}>
      <title id={`${id}-title`}>{labels[0]}</title>
      <desc id={`${id}-desc`}>{labels[1]} on the horizontal axis; {labels[2]} on the vertical axis. Saved out-of-fold evaluation data. Exact values are available in the table below.</desc>
      {[0,.25,.5,.75,1].map(tick=><g key={tick} className="mq-axis">
        <line x1="64" x2="504" y1={y(tick*maxY)} y2={y(tick*maxY)} />
        <text x="54" y={y(tick*maxY)+4} textAnchor="end">{displayMetric(tick*maxY,kind==="histogram"?0:2)}</text>
        <text x={x(tick)} y="281" textAnchor="middle">{tick.toFixed(2)}</text>
      </g>)}
      <line className="mq-axis-line" x1="64" y1="42" x2="64" y2="262" />
      <line className="mq-axis-line" x1="64" y1="262" x2="504" y2="262" />
      {(kind==="roc" || kind==="calibration") && <line className="mq-reference" x1={x(0)} y1={y(0)} x2={x(1)} y2={y(1)} />}
      {kind==="pr" && baseline!==undefined && <line className="mq-reference" x1={x(0)} y1={y(baseline)} x2={x(1)} y2={y(baseline)} />}
      {valid.map((item,index)=><g key={item.name} className={`mq-series mq-series-${index%10}`}>
        {kind==="histogram" ? item.points.map((point,i)=><rect key={i} x={x(point.x)-18} y={y(point.y)} width="36" height={262-y(point.y)} opacity=".75" />) : <>
          <polyline points={item.points.map(point=>`${x(point.x)},${y(point.y)}`).join(" ")} fill="none" strokeWidth="2.5" strokeDasharray={index>4?"7 3":undefined} />
          {kind==="calibration" && item.points.map((point,i)=><circle key={i} cx={x(point.x)} cy={y(point.y)} r="4" />)}
        </>}
      </g>)}
      <text className="mq-axis-label" x="284" y="308" textAnchor="middle">{labels[1]}</text>
      <text className="mq-axis-label" transform="translate(16 154) rotate(-90)" textAnchor="middle">{labels[2]}</text>
    </svg>
    <ul className="mq-legend" aria-label="Displayed series">{valid.map((item,index)=><li key={item.name}><span className={`mq-swatch mq-series-${index%10}`} aria-hidden="true" />{item.name}</li>)}</ul>
    <details className="mq-values"><summary>View exact plotted values</summary><div className="table-scroll" tabIndex={0} aria-label={`${labels[0]} values`}><table><caption>{labels[0]} · saved coordinates</caption><thead><tr><th scope="col">Series</th><th scope="col">{labels[1]}</th><th scope="col">{labels[2]}</th></tr></thead><tbody>{valid.flatMap(item=>item.points.map((point,index)=><tr key={`${item.name}-${index}`}><th scope="row">{item.name}</th><td>{point.x}</td><td>{point.y}</td></tr>))}</tbody></table></div></details>
  </div>;
}
