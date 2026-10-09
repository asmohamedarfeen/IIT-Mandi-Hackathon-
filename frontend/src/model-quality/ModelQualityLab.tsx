import { lazy, Suspense, useEffect, useState, type ReactNode } from "react";
import { Download, RefreshCw, Sun, Moon } from "lucide-react";
import { displayMetric, exactThreshold, useQualityDownload, useQualityOverview } from "./hooks";
import type { ModelQualityOverview, ModelResult, PlotSeries, QualityTarget, ReportFormat, ReportSection, Stability } from "./types";
import "./styles.css";

const LazyCharts = lazy(() => import("./Charts").then(module => ({default:module.Charts})));
const targets: QualityTarget[] = ["CAD","LAD","LCX","RCA"];
const metrics = [
  ["roc_auc","ROC AUC"], ["pr_auc","PR AUC"], ["average_precision","Average precision"], ["accuracy","Accuracy"], ["precision","Precision"], ["recall","Recall"], ["sensitivity","Sensitivity"], ["specificity","Specificity"], ["f1","F1"], ["mcc","MCC"], ["cohen_kappa","Cohen’s κ"], ["balanced_accuracy","Balanced accuracy"], ["log_loss","Log loss"], ["brier_score","Brier score"], ["ece","ECE"],
] as const;
const lowerIsBetter = new Set(["log_loss","brier_score","ece"]);
const sectionLinks = [["mq-overview","Overview"],["mq-comparison","Compare models"],["mq-confusion","Confusion"],["mq-thresholds","Thresholds"],["mq-calibration","Calibration"],["mq-histogram","Probabilities"],["mq-roc","ROC"],["mq-pr","Precision–recall"],["mq-class-balance","Class balance"],["mq-features","Feature stability"],["mq-shap","SHAP stability"],["mq-provenance","Provenance"]];
function Plot(props: Parameters<typeof LazyCharts>[0]) { return <Suspense fallback={<p role="status">Loading plot…</p>}><LazyCharts {...props} /></Suspense>; }
function Table({caption, headings, children}: {caption:string;headings:string[];children:ReactNode}) {
  return <div className="table-scroll mq-table-scroll" tabIndex={0} aria-label={caption}><table><caption>{caption}</caption><thead><tr>{headings.map(heading=><th scope="col" key={heading}>{heading}</th>)}</tr></thead><tbody>{children}</tbody></table></div>;
}
function Section({id,title,description,action,children}: {id:string;title:string;description?:string;action?:ReactNode;children:ReactNode}) {
  return <section id={id} className="mq-section" aria-labelledby={`${id}-title`}><div className="mq-section-heading"><div><h2 id={`${id}-title`}>{title}</h2>{description && <p>{description}</p>}</div>{action}</div>{children}</section>;
}
function DownloadArtifact({section,target,model,threshold,runId,disabled=false}: {section:ReportSection;target?:QualityTarget;model?:string;threshold?:number;runId:string;disabled?:boolean}) {
  const [format,setFormat] = useState<ReportFormat>("csv");
  const state = useQualityDownload(`${runId}:${section}:${target}:${model}:${threshold}`);
  return <div className="mq-export"><label><span className="mq-sr-only">{section} download format</span><select aria-label={`${section} download format`} value={format} onChange={event=>setFormat(event.target.value as ReportFormat)}><option value="csv">CSV</option><option value="json">JSON</option><option value="pdf">PDF</option></select></label><button type="button" disabled={disabled || state.busy} onClick={()=>void state.download({section,format,target,model,threshold,expected_run_id:runId})}><Download size={15}/>{state.busy?"Downloading…":"Download"}</button>{state.message && <p role={state.error?"alert":"status"}>{state.message}</p>}</div>;
}
function StabilityTable({data,kind}: {data:Stability|undefined;kind:"Feature"|"SHAP"}) {
  if (!data?.features?.length) return <p className="mq-unavailable">Unavailable · no saved {kind.toLowerCase()} stability data.</p>;
  return <><p>{data.model} · {data.method}</p><p className="mq-inline-metrics">Mean rank correlation <strong>{displayMetric(data.mean_rank_correlation)}</strong> · Mean top-k Jaccard <strong>{displayMetric(data.mean_top_k_jaccard)}</strong></p><Table caption={`${kind} variation across held-out folds`} headings={["Feature","Mean ± SD","Mean rank ± SD","Top-k frequency","Fold values"]}>{data.features.map(feature=><tr key={feature.feature}><th scope="row">{feature.feature}</th><td>{displayMetric(feature.mean)} ± {displayMetric(feature.std)}</td><td>{displayMetric(feature.rank_mean)} ± {displayMetric(feature.rank_std)}</td><td>{displayMetric(feature.top_k_frequency)}</td><td>{feature.fold_values.map(value=>displayMetric(value)).join(" · ")}</td></tr>)}</Table></>;
}
function curveSeries(models: Array<[string,ModelResult]>, kind:"roc"|"pr"):PlotSeries[] {
  return models.map(([name,model])=>({name,points:kind==="roc" ? (model.diagnostics?.roc?.fpr || []).map((x,i)=>({x,y:model.diagnostics.roc.tpr[i]})) : (model.diagnostics?.pr?.recall || []).map((x,i)=>({x,y:model.diagnostics.pr.precision[i]}))}));
}
export function ModelQualityLab({initialData,loadOverview}: {initialData?:ModelQualityOverview;loadOverview?:(signal?:AbortSignal)=>Promise<ModelQualityOverview>}) {
  const {data,loading,error,reload} = useQualityOverview(initialData,loadOverview);
  const [target,setTarget] = useState<QualityTarget>("CAD");
  const [model,setModel] = useState(initialData?.selected_model || "CalibratedVoting");
  const [threshold,setThreshold] = useState(.5);
  const [sort,setSort] = useState<{key:string;ascending:boolean}>({key:"roc_auc",ascending:false});
  const [overlays,setOverlays] = useState<string[]>([]);
  const [theme,setTheme] = useState<"system"|"light"|"dark">("system");
  const [systemDark,setSystemDark] = useState(()=>typeof matchMedia==="function" && matchMedia("(prefers-color-scheme: dark)").matches);
  useEffect(()=>{
    if (typeof matchMedia!=="function") return;
    const preference=matchMedia("(prefers-color-scheme: dark)");
    const update=()=>setSystemDark(preference.matches);
    update(); preference.addEventListener("change",update);
    return ()=>preference.removeEventListener("change",update);
  },[]);
  const darkAppearance=theme==="dark" || (theme==="system" && systemDark);
  const evaluation = data?.targets[target];
  const availableModels = Object.keys(evaluation?.models || {});
  const selected = evaluation?.models[model];
  useEffect(()=>{
    if (!data) return;
    if (!availableModels.includes(model)) setModel(availableModels.includes(data.selected_model)?data.selected_model:availableModels[0] || "");
    setOverlays(current=>current.length?current.filter(id=>availableModels.includes(id)):[data.selected_model,...availableModels.filter(id=>id!==data.selected_model).slice(0,2)].filter(id=>availableModels.includes(id)));
  },[data,target]);
  const rows = Object.entries(evaluation?.models || {}).sort(([nameA,a],[nameB,b])=>{
    const av=a.metrics[sort.key], bv=b.metrics[sort.key];
    if (av==null || !Number.isFinite(av)) return bv==null || !Number.isFinite(bv)?nameA.localeCompare(nameB):1;
    if (bv==null || !Number.isFinite(bv)) return -1;
    return (sort.ascending?av-bv:bv-av) || nameA.localeCompare(nameB);
  });
  const point = exactThreshold(selected?.diagnostics?.thresholds,threshold);
  const selectedOverlays = Object.entries(evaluation?.models || {}).filter(([id])=>overlays.includes(id));
  const exportFor = (section:ReportSection,forModel=model,forTarget:QualityTarget|null=target) => data ? <DownloadArtifact section={section} target={forTarget ?? undefined} model={forModel || undefined} threshold={threshold} runId={data.run_id} disabled={loading}/> : null;
  const modelName = (id:string) => data?.models.find(candidate=>candidate.id===id)?.name || id;
  return <div className="model-quality-lab" data-theme={theme} id="model-quality-lab">
    <div className="mq-page-heading"><div><h1>Model Quality Lab</h1><p>Inspect saved held-out evaluation, operating points and reproducibility.</p></div><div className="mq-heading-actions"><button type="button" aria-label={`Switch to ${darkAppearance?"light":"dark"} Lab theme`} onClick={()=>setTheme(darkAppearance?"light":"dark")}>{darkAppearance?<Sun size={18}/>:<Moon size={18}/>}<span>{darkAppearance?"Light":"Dark"}</span></button><button type="button" onClick={()=>void reload()} disabled={loading}><RefreshCw size={16}/>{loading?"Loading…":"Refresh"}</button></div></div>
    {loading && !data && <div className="mq-loading" role="status" aria-live="polite"><p>Loading saved evaluation…</p><div/><div/><div/></div>}
    {!data && !loading && <div className="mq-empty" role="alert"><h2>Unavailable · evaluation has not been loaded</h2><p>{error || "No saved evaluation artifact is available."}</p><p>Generate real held-out evaluation using <code>.venv/bin/python scripts/evaluate_model_quality.py</code>, then retry.</p><button type="button" onClick={()=>void reload()}>Retry evaluation</button></div>}
    {data && <>
      {(data.stale || data.status==="stale") && <p className="mq-warning" role="status">This saved evaluation is stale. Model, dataset or evaluation source fingerprints changed. Generate a new run before relying on it.</p>}
      {error && <p className="mq-warning" role="alert">Refresh unavailable: {error}. Showing saved run {data.run_id}.</p>}
      <div className="mq-toolbar"><label htmlFor="mq-target">Target<select id="mq-target" value={target} onChange={event=>{setTarget(event.target.value as QualityTarget);setThreshold(.5);}}>{targets.filter(id=>data.targets[id]).map(id=><option key={id}>{id}</option>)}</select></label><label htmlFor="mq-model">Diagnostic model<select id="mq-model" value={model} onChange={event=>{setModel(event.target.value);setThreshold(.5);}}>{availableModels.map(id=><option key={id} value={id}>{modelName(id)}{id===data.selected_model?" · production":""}</option>)}</select></label><div className="mq-run"><span>Saved run</span><strong>{data.run_id}</strong><span>{data.generated_at}</span></div></div>
      <nav className="mq-section-nav" aria-label="Model quality sections">{sectionLinks.map(([id,label])=><a key={id} href={`#${id}`}>{label}</a>)}</nav>
      <Section id="mq-overview" title="Evaluation & data quality" description="Internal cross-validation evidence. Production configuration identifies the deployed model recipe; fold estimators are refitted for evaluation." action={exportFor("results","",null)}>
        <dl className="mq-summary"><div><dt>Records</dt><dd>{data.data_quality.rows}</dd></div><div><dt>Duplicate records</dt><dd>{data.data_quality.duplicates}</dd></div><div><dt>Outer / inner folds</dt><dd>{data.provenance.outer_folds ?? "Unavailable"} / {data.provenance.inner_folds ?? "Unavailable"}</dd></div><div><dt>Production configuration</dt><dd>{modelName(data.selected_model)}</dd></div></dl>
        <div className="mq-columns"><div><h3>Leakage checks</h3><ul className="mq-checks">{data.data_quality.leakage_checks.map(check=><li key={check.check}><strong className={check.passed?"mq-pass":"mq-fail"}>{check.passed?"Passed":"Failed"}</strong><div>{check.check}<p>{check.detail}</p></div></li>)}</ul>{!data.data_quality.leakage_checks.length && <p className="mq-unavailable">Unavailable · no saved leakage checks.</p>}</div><div><h3>Missing values</h3><Table caption="Missing values before preprocessing" headings={["Input","Missing records"]}>{Object.entries(data.data_quality.missing_values).map(([feature,count])=><tr key={feature}><th scope="row">{feature}</th><td>{count}</td></tr>)}</Table></div></div>
        <details><summary>Evaluation limitations</summary><ul>{data.limitations.map(limit=><li key={limit}>{limit}</li>)}</ul></details>
      </Section>
      <Section id="mq-comparison" title="Model comparison" description={`${target} · pooled out-of-fold metrics. Select a metric heading to sort; lower log loss, Brier score and ECE are better.`} action={exportFor("metrics","")}>
        <div className="table-scroll mq-table-scroll" tabIndex={0} aria-label="Sortable model metrics"><table><caption>{target} · saved evaluation metrics</caption><thead><tr><th scope="col">Model</th>{metrics.map(([key,label])=><th scope="col" key={key} aria-sort={sort.key===key?(sort.ascending?"ascending":"descending"):"none"}><button type="button" onClick={()=>setSort(current=>({key,ascending:current.key===key?!current.ascending:lowerIsBetter.has(key)}))}>{label}{sort.key===key?(sort.ascending?" ↑":" ↓"):""}</button></th>)}</tr></thead><tbody>{rows.map(([id,result])=><tr key={id} data-selected={id===model}><th scope="row"><button type="button" onClick={()=>{setModel(id);setThreshold(.5);}}>{modelName(id)}</button>{id===data.selected_model && <span className="mq-production">Production recipe</span>}</th>{metrics.map(([key])=><td key={key} title={result.undefined_metrics?.[key]}>{displayMetric(result.metrics[key])}</td>)}</tr>)}</tbody></table></div>
        <p className="mq-note">PR AUC uses trapezoidal integration; average precision is reported separately. Undefined metrics display “Unavailable” and retain the reason in the artifact.</p>
        {selected && <details><summary>{modelName(model)} · fold metrics & undefined values</summary><Table caption="Individual outer-fold metrics" headings={["Fold",...metrics.map(([,label])=>label)]}>{selected.fold_metrics.map((fold,index)=><tr key={index}><th scope="row">{index+1}</th>{metrics.map(([key])=><td key={key}>{displayMetric(fold[key])}</td>)}</tr>)}</Table>{Object.entries(selected.undefined_metrics || {}).map(([key,reason])=><p key={key}>{key}: {reason}</p>)}</details>}
        <details><summary>Supplied benchmarks · separate historical evaluation</summary><p>These supplied scores evaluate uncalibrated candidate models under their original protocol; they do not validate the calibrated deployment or external performance.</p><Table caption="Supplied historical cross-validation metrics" headings={["Model",...metrics.slice(0,12).map(([,label])=>label)]}>{Object.entries(data.supplied_benchmarks?.targets[target] || {}).map(([id,result])=><tr key={id}><th scope="row">{id}</th>{metrics.slice(0,12).map(([key])=><td key={key}>{displayMetric(result[key])}</td>)}</tr>)}</Table></details>
      </Section>
      <Section id="mq-confusion" title="Confusion matrix" description={`${target} · ${modelName(model)} · positive when probability ≥ threshold. Changing this diagnostic threshold does not change patient assessments.`} action={exportFor("confusion-matrices")}>
        <div className="mq-threshold-control"><label htmlFor="mq-threshold">Decision threshold <strong>{Math.round(threshold*100)}%</strong></label><input id="mq-threshold" type="range" min="0" max="1" step="0.01" value={threshold} aria-valuetext={`${Math.round(threshold*100)} percent`} onChange={event=>setThreshold(Number(event.target.value))}/></div>
        {point ? <div className="mq-columns"><table className="mq-confusion-table" aria-label="Confusion counts"><caption>Actual rows · predicted columns</caption><thead><tr><th scope="col">Actual / predicted</th><th scope="col">Negative</th><th scope="col">Positive</th></tr></thead><tbody><tr><th scope="row">Negative</th><td><strong>{point.tn}</strong>True negative</td><td><strong>{point.fp}</strong>False positive</td></tr><tr><th scope="row">Positive</th><td><strong>{point.fn}</strong>False negative</td><td><strong>{point.tp}</strong>True positive</td></tr></tbody></table><dl className="mq-summary mq-threshold-metrics">{(["precision","sensitivity","specificity","f1"] as const).map(key=><div key={key}><dt>{key}</dt><dd>{displayMetric(point[key])}</dd></div>)}</dl></div> : <p className="mq-unavailable">Unavailable · no exact saved counts at this threshold. No counts are interpolated.</p>}
        <p className="mq-note" role="status">{point?`${Math.round(threshold*100)}% threshold: ${point.tp} true positives, ${point.fp} false positives, ${point.fn} false negatives and ${point.tn} true negatives.`:"Exact operating-point metrics unavailable."}</p>
      </Section>
      <Section id="mq-thresholds" title="Threshold trade-offs" description="Sensitivity and specificity at each saved operating point." action={exportFor("thresholds")}>
        <Plot kind="threshold" series={["sensitivity","specificity"].map(key=>({name:key,points:(selected?.diagnostics?.thresholds || []).flatMap(value=>typeof value[key as "sensitivity"]==="number"?[{x:value.threshold,y:value[key as "sensitivity"] as number}]:[])}))}/>
      </Section>
      <Section id="mq-calibration" title="Calibration" description="Uncalibrated Voting compared with CalibratedVoting on the same evaluation folds. The diagonal indicates agreement between predicted probability and observed frequency." action={exportFor("calibration","")}>
        <Plot kind="calibration" series={["Voting","CalibratedVoting"].map(id=>({name:modelName(id),points:(evaluation?.models[id]?.diagnostics?.calibration || []).flatMap(bin=>bin.count>0 && bin.mean_probability!==null && bin.fraction_positive!==null?[{x:bin.mean_probability,y:bin.fraction_positive}]:[])}))}/>
        <Table caption="Selected model calibration bins" headings={["Probability bin","Records","Mean probability","Observed positive fraction"]}>{(selected?.diagnostics?.calibration || []).map(bin=><tr key={bin.lower}><th scope="row">{displayMetric(bin.lower,2)}–{displayMetric(bin.upper,2)}</th><td>{bin.count}</td><td>{displayMetric(bin.mean_probability)}</td><td>{displayMetric(bin.fraction_positive)}</td></tr>)}</Table>
      </Section>
      <Section id="mq-histogram" title="Probability distribution" description={`${modelName(model)} · held-out predicted probabilities; bar height is record count.`} action={exportFor("histogram")}>
        <Plot kind="histogram" series={[{name:modelName(model),points:(selected?.diagnostics?.probability_histogram || selected?.diagnostics?.calibration || []).map(bin=>({x:(bin.lower+bin.upper)/2,y:bin.count}))}]}/>
      </Section>
      <div className="mq-overlays"><fieldset><legend>ROC & precision–recall overlays</legend>{availableModels.map(id=><label key={id}><input type="checkbox" checked={overlays.includes(id)} onChange={event=>setOverlays(current=>event.target.checked?[...current,id]:current.filter(value=>value!==id))}/>{modelName(id)}</label>)}</fieldset></div>
      <div className="mq-columns mq-curve-columns"><Section id="mq-roc" title="ROC curves" description="Sensitivity versus false positive rate. Dashed diagonal: chance discrimination." action={exportFor("roc","")}><Plot kind="roc" series={curveSeries(selectedOverlays,"roc")}/></Section><Section id="mq-pr" title="Precision–recall curves" description="Precision versus recall. Dashed line: target prevalence." action={exportFor("pr","")}><Plot kind="pr" series={curveSeries(selectedOverlays,"pr")} baseline={evaluation?.class_distribution.total ? evaluation.class_distribution.positive/evaluation.class_distribution.total:undefined}/></Section></div>
      <Section id="mq-class-balance" title="Class balance & folds" description={`${target} · binary labels and stratified outer-fold composition.`} action={exportFor("class-distribution","")}>
        {evaluation ? <><p className="mq-balance">{evaluation.class_distribution.positive} positive · {evaluation.class_distribution.negative} negative · {evaluation.class_distribution.total} total</p><div className="mq-balance-track" aria-hidden="true"><span style={{width:`${evaluation.class_distribution.total?100*evaluation.class_distribution.positive/evaluation.class_distribution.total:0}%`}}/></div><Table caption="Outer-fold class distribution" headings={["Fold","Train positive","Train negative","Train total","Test positive","Test negative","Test total"]}>{evaluation.folds.map(fold=><tr key={fold.fold}><th scope="row">{fold.fold}</th><td>{fold.train.positive}</td><td>{fold.train.negative}</td><td>{fold.train.total}</td><td>{fold.test.positive}</td><td>{fold.test.negative}</td><td>{fold.test.total}</td></tr>)}</Table></> : <p className="mq-unavailable">Unavailable · target class counts were not saved.</p>}
      </Section>
      <Section id="mq-features" title="Feature importance stability" description="Importance and rank variation across refitted evaluation folds; a stable ranking does not establish causality." action={exportFor("feature-stability","XGBoost")}><StabilityTable data={evaluation?.feature_stability} kind="Feature"/></Section>
      <Section id="mq-shap" title="SHAP stability" description="Global explanation-model attribution variation across held-out folds. XGBoost attributions explain the surrogate, not the voting ensemble." action={exportFor("shap","XGBoost")}><StabilityTable data={evaluation?.shap_stability} kind="SHAP"/></Section>
      <Section id="mq-provenance" title="Provenance & reproducibility" description="Fingerprints, environment, estimator parameters and evaluation procedure from this saved run." action={exportFor("reproducibility","",null)}>
        <dl className="mq-provenance">{Object.entries(data.provenance).map(([key,value])=><div key={key}><dt>{key.replace(/_/g," ")}</dt><dd>{value==null?"Unavailable":typeof value==="object"?<pre>{JSON.stringify(value,null,2)}</pre>:String(value)}</dd></div>)}</dl>
        <h3>Model configurations</h3>{data.models.map(candidate=><details key={candidate.id}><summary>{candidate.name}{candidate.production_configuration?" · production configuration":""}</summary><p>Source: {candidate.configuration_source}</p><pre>{JSON.stringify(candidate.parameters,null,2)}</pre></details>)}
        <p className="mq-note">Results JSON exports the complete aggregate evaluation, including provenance and configurations. CSV and PDF sections retain the selected target and model context. Private patient-level out-of-fold records are not included.</p>
      </Section>
    </>}
  </div>;
}
