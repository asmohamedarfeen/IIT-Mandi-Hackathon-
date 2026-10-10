"""Aggregate-only quality exports from the validated offline snapshot."""
import csv
import json
from io import BytesIO, StringIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.graphics.shapes import Drawing, Line, PolyLine, String
from pypdf import PdfReader, PdfWriter

SECTIONS = {'results', 'metrics', 'confusion-matrices', 'calibration', 'roc', 'pr', 'shap', 'feature-stability', 'thresholds', 'histogram', 'class-distribution', 'reproducibility'}


def selection(summary, section, target=None, model=None, confusion=None, models=None):
    selected = set(models) if models is not None else None
    result = {'schema_version': 1, 'run_id': summary['run_id'], 'generated_at': summary['generated_at'], 'status': summary['status'], 'stale': summary['stale'], 'section': section, 'selection': {'target': target, 'model': model, 'models': sorted(selected) if selected is not None else None}, 'provenance': summary['provenance'], 'limitations': summary['limitations']}
    result['data_quality'] = summary['data_quality']
    result['models'] = [entry for entry in summary['models'] if (model is None or entry['id'] == model) and (selected is None or entry['id'] in selected)]
    result['supplied_benchmarks'] = summary['supplied_benchmarks']
    if section == 'reproducibility':
        return result
    if section == 'results' and target is None and model is None:
        return {**summary, **result}
    result['targets'] = {}
    for name, value in summary['targets'].items():
        if target and name != target:
            continue
        item = {'class_distribution': value['class_distribution']}
        if section in ('results', 'class-distribution'):
            item['folds'] = value['folds']
        if section in ('results', 'shap', 'feature-stability'):
            for key in ('shap_stability', 'feature_stability'):
                if section == 'results' or key == {'shap': 'shap_stability', 'feature-stability': 'feature_stability'}.get(section):
                    item[key] = value[key]
        if section not in ('shap', 'feature-stability', 'class-distribution'):
            item['models'] = {}
            for identifier, evidence in value['models'].items():
                if model and identifier != model or selected is not None and identifier not in selected:
                    continue
                if section == 'results':
                    item['models'][identifier] = evidence
                elif section == 'metrics':
                    item['models'][identifier] = {key: evidence[key] for key in ('metrics', 'undefined_metrics', 'fold_metrics', 'fold_summary', 'fold_model_hashes', 'fold_fit_seconds') if key in evidence}
                else:
                    key = {'confusion-matrices': 'confusion_matrix', 'histogram': 'probability_histogram'}.get(section, section)
                    item['models'][identifier] = {key: confusion if confusion is not None else evidence['diagnostics'][key]}
        result['targets'][name] = item
    return result


def csv_export(payload):
    output = StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['run_id', 'section', 'path', 'value'])
    def walk(value, path):
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, f'{path}.{key}' if path else key)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f'{path}[{index}]')
        else:
            text = '' if value is None else str(value)
            if isinstance(value, str) and text.startswith(('=', '+', '-', '@', '\t', '\r')):
                text = "'" + text
            writer.writerow([payload['run_id'], payload['section'], path, text])
    walk(payload, '')
    return output.getvalue().encode('utf-8')


def pdf_export(payload):
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    ink, pale, line = (colors.HexColor(c) for c in ('#25332c', '#eef1e8', '#d6ddcf'))
    for style in styles.byName.values():
        style.textColor = ink
    for name in ('Heading1', 'Heading2', 'Heading3', 'Heading4'):
        styles[name].keepWithNext = True
    styles['BodyText'].fontSize = 8
    styles['BodyText'].leading = 10
    def p(value, style='BodyText'):
        display = 'Undefined' if value is None else format(value, '.6g') if isinstance(value, float) else str(value)
        text = display.encode('ascii', 'backslashreplace').decode('ascii')
        return Paragraph(escape(text), styles[style])
    story = [p('CardioVision / Model Quality', 'Title'), p('Offline out-of-fold evaluation. Research evidence, not clinical validation.'), p(f"Run {payload['run_id']} | {payload['generated_at']} | {payload['status']}"), p(f"Section: {payload['section']} | Selection: {json.dumps(payload['selection'])}"), Spacer(1, 12)]
    full_report = payload['section'] == 'results'
    story.append(p('Complete evidence appendix: this PDF contains an attached aggregate-evidence.json file with the exact exported selection, including all available fold metrics, fold model hashes, fit durations, ROC/PR points, thresholds, stability fold values and configuration parameters. No private OOF rows are included.'))
    story.append(p('Readable tables display numbers to six significant digits. The attached appendix preserves full stored precision.'))
    if full_report:
        story.append(p('The readable report shows metrics for every selected model and detailed diagnostic charts for the deployed calibrated voting configuration. Complete comparator diagnostics are preserved in the attached JSON appendix.'))
    def table(rows):
        t = Table([[p(v) for v in row] for row in rows], colWidths=[160, 345], repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), pale), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LINEBELOW', (0, 0), (-1, -1), .3, line), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
        story.append(t)
    def describe(value, label):
        if isinstance(value, dict):
            scalar = [[k, 'Undefined' if v is None else v] for k, v in value.items() if not isinstance(v, (dict, list))]
            if scalar:
                table([['Measure', 'Value'], *scalar])
            for key, child in value.items():
                if isinstance(child, (dict, list)):
                    story.extend([Spacer(1, 8), p(f'{label} / {key}', 'Heading3')])
                    describe(child, key)
        elif isinstance(value, list):
            if value and all(not isinstance(v, (dict, list)) for v in value):
                # Curves are printed completely, preserving precise aggregate values.
                story.append(p(', '.join('Undefined' if v is None else str(v) for v in value)))
            else:
                for index, child in enumerate(value):
                    story.append(p(f'{label} {index + 1}', 'Heading4'))
                    describe(child, label)
    def grid(rows, widths):
        t = Table([[p(v) for v in row] for row in rows], colWidths=widths, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), pale), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LINEBELOW', (0, 0), (-1, -1), .3, line), ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
        story.append(t)

    def curve(data, xkey, ykey, title):
        story.append(p(title, 'Heading3'))
        if not data[xkey]:
            story.append(p('Undefined for the observed class distribution.'))
            return
        chart = Drawing(505, 155)
        chart.add(Line(35, 20, 485, 20, strokeColor=line))
        chart.add(Line(35, 20, 35, 140, strokeColor=line))
        chart.add(String(35, 5, '0', fontSize=8)); chart.add(String(478, 5, '1', fontSize=8))
        chart.add(String(20, 135, '1', fontSize=8))
        chart.add(String(245, 5, xkey, fontSize=8))
        coords = [coordinate for x, y in zip(data[xkey], data[ykey]) for coordinate in (35 + 450*x, 20 + 120*y)]
        chart.add(PolyLine(coords, strokeColor=ink, strokeWidth=1.2))
        story.append(chart)

    for target, evidence in payload.get('targets', {}).items():
        story.extend([Spacer(1, 14), p(target, 'Heading1')])
        describe(evidence['class_distribution'], 'Class distribution')
        if evidence.get('folds'):
            story.append(p('Outer fold cohort counts', 'Heading3'))
            grid([['Fold', 'Train +', 'Train -', 'Test +', 'Test -'], *[[f['fold'], f['train']['positive'], f['train']['negative'], f['test']['positive'], f['test']['negative']] for f in evidence['folds']]], [65, 110, 110, 110, 110])
        for identifier, model in evidence.get('models', {}).items():
            story.extend([Spacer(1, 10), p(identifier, 'Heading2')])
            if 'metrics' in model:
                entries = list(model['metrics'].items())
                rows = [['Metric', 'Value', 'Metric', 'Value']]
                for index in range(0, len(entries), 2):
                    pair = entries[index:index+2]
                    rows.append([pair[0][0], pair[0][1], pair[1][0] if len(pair)>1 else '', pair[1][1] if len(pair)>1 else ''])
                grid(rows, [125, 127, 125, 128])
                if model.get('undefined_metrics'):
                    story.append(p('Undefined measures: ' + json.dumps(model['undefined_metrics'])))
                if model.get('fold_summary') and (not full_report or identifier == payload.get('selected_model', 'CalibratedVoting')):
                    story.append(p('Descriptive fold dispersion (not a confidence interval)', 'Heading3'))
                    grid([['Metric', 'Fold mean', 'Fold standard deviation'], *[[name, values['mean'], values['std']] for name, values in model['fold_summary'].items()]], [165, 170, 170])
                if model.get('fold_model_hashes'):
                    story.append(p(f"{len(model['fold_model_hashes'])} fold model hashes and fit durations archived in the complete evidence appendix."))
            if full_report and identifier != payload.get('selected_model', 'CalibratedVoting'):
                continue
            diagnostics = model.get('diagnostics', model)
            if 'confusion_matrix' in diagnostics:
                cm = diagnostics['confusion_matrix']
                story.append(p(f"Confusion matrix at probability threshold {cm['threshold']}", 'Heading3'))
                grid([['TN', 'FP', 'FN', 'TP'], [cm[k] for k in ('tn', 'fp', 'fn', 'tp')]], [126, 126, 126, 127])
            if 'calibration' in diagnostics:
                story.append(p('Calibration: held-out probability bins', 'Heading3'))
                grid([['Bin', 'Count', 'Mean probability', 'Fraction positive'], *[[f"{b['lower']}-{b['upper']}", b['count'], b['mean_probability'], b['fraction_positive']] for b in diagnostics['calibration']]], [90, 65, 175, 175])
            if 'roc' in diagnostics:
                curve(diagnostics['roc'], 'fpr', 'tpr', 'ROC: false positive rate / true positive rate')
            if 'pr' in diagnostics:
                curve(diagnostics['pr'], 'recall', 'precision', 'Precision / recall')
            if 'thresholds' in diagnostics and not full_report:
                story.append(p('Threshold sweep', 'Heading3'))
                grid([['Threshold', 'TN', 'FP', 'FN', 'TP', 'Precision', 'Recall', 'Specificity', 'F1'], *[[row[key] for key in ('threshold', 'tn', 'fp', 'fn', 'tp', 'precision', 'recall', 'specificity', 'f1')] for row in diagnostics['thresholds']]], [55, 32, 32, 32, 32, 80, 80, 80, 82])
            if 'probability_histogram' in diagnostics and not full_report:
                story.append(p('Probability histogram', 'Heading3'))
                grid([['Lower', 'Upper', 'Count'], *[[row[key] for key in ('lower', 'upper', 'count')] for row in diagnostics['probability_histogram']]], [170, 170, 165])
        for key in ('feature_stability', 'shap_stability'):
            if key not in evidence:
                continue
            stability = evidence[key]
            story.extend([Spacer(1, 10), p(key.replace('_', ' ').title(), 'Heading2'), p(f"Model: {stability['model']} | Method: {stability['method']}"), p(f"Mean rank correlation: {stability.get('mean_rank_correlation')} | Mean top-k Jaccard: {stability.get('mean_top_k_jaccard')}")])
            if stability['features']:
                grid([['Feature', 'Mean', 'Std', 'Top-k frequency', 'Mean rank', 'Rank std'], *[[f[k] for k in ('feature', 'mean', 'std', 'top_k_frequency', 'rank_mean', 'rank_std')] for f in stability['features']]], [145, 72, 72, 72, 72, 72])
            else:
                story.append(p('No feature stability observations were supplied.'))
    story.extend([Spacer(1, 14), p('Data quality', 'Heading1')])
    quality = payload.get('data_quality', {})
    describe({key: value for key, value in quality.items() if key not in ('missing_values', 'leakage_checks')}, 'Data quality')
    nonzero_missing = {key: value for key, value in quality.get('missing_values', {}).items() if value}
    story.append(p(f"Missing observations: {sum(quality.get('missing_values', {}).values())}; {len(nonzero_missing)} fields with missing values."))
    if nonzero_missing:
        describe(nonzero_missing, 'Fields with missing observations')
    checks = quality.get('leakage_checks', [])
    if checks:
        grid([['Check', 'Passed', 'Detail'], *[[row['check'], row['passed'], row['detail']] for row in checks]], [155, 55, 295])
    story.extend([Spacer(1, 14), p('Model configurations', 'Heading1')])
    for model in payload.get('models', []):
        story.append(p(f"{model['id']} | {model['name']} | Production configuration: {model['production_configuration']} | {model['configuration_source']}"))
    story.append(p('Exact nested estimator parameters are preserved without truncation in the attached JSON appendix.'))
    story.extend([Spacer(1, 14), p('Reproducibility', 'Heading1')])
    provenance = {key: value for key, value in payload['provenance'].items() if key != 'model_parameters'}
    describe(provenance, 'Provenance')
    story.extend([Spacer(1, 14), p('Supplied benchmarks', 'Heading1')])
    story.append(p('Historical supplied results, separate from this out-of-fold evaluation. All supplied measures are retained in the attached evidence appendix.'))
    benchmark_rows = [['Target / Model', 'Accuracy', 'ROC AUC', 'Recall', 'Specificity']]
    for target, models in payload.get('supplied_benchmarks', {}).get('targets', {}).items():
        if payload['selection'].get('target') and target != payload['selection']['target']:
            continue
        for name, metrics in models.items():
            benchmark_rows.append([f'{target} / {name}', *[metrics.get(key) for key in ('accuracy', 'roc_auc', 'recall', 'specificity')]])
    if len(benchmark_rows) > 1:
        grid(benchmark_rows, [185, 80, 80, 80, 80])
    story.extend([Spacer(1, 14), p('Limitations', 'Heading1')])
    for limitation in payload['limitations']:
        story.append(p(limitation))
    def footer(canvas, doc):
        canvas.saveState(); canvas.setFont('Helvetica', 8); canvas.setFillColor(ink)
        canvas.drawString(45, 25, f"Model Quality / {payload['run_id']}")
        canvas.drawRightString(A4[0] - 45, 25, str(doc.page)); canvas.restoreState()
    SimpleDocTemplate(buffer, pagesize=A4, rightMargin=45, leftMargin=45, topMargin=42, bottomMargin=42).build(story, onFirstPage=footer, onLaterPages=footer)
    writer = PdfWriter()
    writer.clone_document_from_reader(PdfReader(BytesIO(buffer.getvalue())))
    writer.add_attachment('aggregate-evidence.json', json.dumps(payload, allow_nan=False, indent=2).encode())
    complete = BytesIO(); writer.write(complete)
    return complete.getvalue()
