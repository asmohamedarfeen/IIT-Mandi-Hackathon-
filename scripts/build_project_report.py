#!/usr/bin/env python3
"""Build Track A's six-page documentation from a verified model release."""
import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]


def build(release, output):
    report = json.loads((release / 'summary.json').read_text())
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('TitleCV', fontName='Helvetica-Bold', fontSize=27, leading=31, textColor=colors.HexColor('#173d35'), spaceAfter=17))
    styles.add(ParagraphStyle('SectionCV', fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=colors.HexColor('#173d35'), spaceBefore=13, spaceAfter=9))
    styles.add(ParagraphStyle('BodyCV', fontName='Helvetica', fontSize=10.5, leading=15, spaceAfter=10))
    styles.add(ParagraphStyle('SmallCV', fontName='Helvetica', fontSize=8.5, leading=12, spaceAfter=8))
    story = []

    def p(text, style='BodyCV'):
        return Paragraph(escape(str(text)), styles[style])

    def heading(n, title, subtitle):
        if n > 1:
            story.append(PageBreak())
        story.extend([p(f'TRACK A / {n:02d}', 'SmallCV'), p(title, 'TitleCV'), p(subtitle)])

    def section(title, text):
        story.extend([p(title, 'SectionCV'), p(text)])

    def table(rows, widths):
        grid = [[p(cell, 'SmallCV') for cell in row] for row in rows]
        result = Table(grid, colWidths=widths, repeatRows=1, hAlign='LEFT')
        result.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e7efeb')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, 0), .7, colors.HexColor('#77978c')),
            ('LINEBELOW', (0, 1), (-1, -1), .3, colors.HexColor('#d5dfda')),
            ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
            ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.extend([result, Spacer(1, 10)])

    heading(1, 'CardioVision AI', 'Cardiovascular prediction, clinical explanations and interactive 3D artery risk mapping.')
    section('Purpose and delivered behavior', 'The React application sends clinical measurements to FastAPI. Four predictors estimate CAD and LAD, LCX and RCA stenosis probabilities. The dashboard shows model classification, probabilities, source-linked explanations and the corresponding reference artery colors. Predictions support education and decision support; they do not substitute for formal diagnostic imaging.')
    tuned = ', '.join(report.get('tuned_targets', report['targets'].keys()))
    section('Model update', f'Tuned targets: {tuned}. RCA uses a small shortlist of the existing predictor and two calibrated LightGBM configurations. Inner folds select configuration and classification threshold; ten outer folds compare that strategy with the baseline. Other targets retain their current configuration. A release gate preserves weights when an improvement fails its accuracy, recall, ROC-AUC or calibration requirements.')
    table([['Component', 'Implementation'], ['Web application', 'React 18, TypeScript, Three.js and Vite'], ['Model/API service', 'FastAPI, scikit-learn, CatBoost, XGBoost and LightGBM'], ['Persistence', 'SQLAlchemy assessment snapshots and inference audit'], ['Artifacts', 'Versioned model bundle, paired OOF audit, source hashes and rollback copy']], [140, 359])
    section('Release identity', report['run_id'])
    story.append(p('Full technical data-transfer documentation: docs/DATA_PIPELINE.md. Machine-readable evaluation: the release summary.json. No patient measurements are included in this project report.', 'SmallCV'))

    heading(2, 'Dataset and preprocessing', 'The supplied workbook is the single source cohort. Training and serving share the ordered feature definition.')
    table([['Outcome', 'Positive', 'Negative'], ['CAD (Cath)', '216', '87'], ['LAD stenosis', '177', '126'], ['LCX stenosis', '119', '184'], ['RCA stenosis', '114', '189']], [269, 115, 115])
    section('Data quality', 'The populated first sheet contains 303 rows and 59 columns; the second sheet has no records. There are no missing values or duplicate complete rows. Unknown outcome labels are rejected. The improvement run rejects incomplete source records so its compatibility preprocessing cannot learn cohort-wide medians.')
    section('Leakage prevention', 'Cath, CAD, LAD, LCX and RCA are excluded from every predictor. Identifiers and constant Exertional CP are also excluded. Fixed row-local engineering precedes splitting; learned candidate imputation is inside the model pipeline and is refitted within calibration folds. Neither outer test labels nor outer test inputs enter model or threshold selection.')
    section('Feature compatibility and ablation', 'Inputs are aligned to the saved 84-column float32 feature order and checked against the original reference vectors. Candidate raw-feature ablations remove calculated proxies inside the estimator while preserving the API input contract. BMI can be supplied or calculated per row from weight in kg and height in cm.')
    section('Clinical proxy limits', 'Estimated blood-pressure indices, pretest scores and RWMA territory flags retain legacy definitions. These are model assumptions, not validated clinical scores or patient-specific lesion coordinates. Demonstration mode labels default assumptions. Reviewed-case mode requires supplied, confirmed modeled measurements; unknown values cannot silently become normal. Snapshots preserve source and confirmation metadata.')

    heading(3, 'Evaluation and model results', 'Paired internal evaluation on identical outer-held-out patients. Metrics describe the strategy, not independent validation of final fitted weights.')
    rows = [['Target', 'Before accuracy', 'Released strategy', 'Before recall', 'Released recall']]
    for target, data in report['targets'].items():
        before, after = data['baseline_metrics'], data['release_procedure_metrics']
        rows.append([target] + [f'{m[k] * 100:.2f}%' for m, k in [(before, 'accuracy'), (after, 'accuracy'), (before, 'recall'), (after, 'recall')]])
    table(rows, [55, 111, 111, 111, 111])
    rows = [['Target', 'ROC-AUC', 'F1', 'Brier', 'Release decision']]
    for target, data in report['targets'].items():
        m = data['release_procedure_metrics']
        rows.append([target, f'{m["roc_auc"]:.4f}', f'{m["f1"]:.4f}', f'{m["brier_score"]:.4f}', 'Promoted' if data['promoted'] else 'Original retained'])
    table(rows, [55, 90, 90, 90, 174])
    section('Selection and calibration', report['method'] + ' The baseline and established LightGBM candidate use five-fold sigmoid calibration; the regularized candidate uses three folds. Seven class thresholds from 0.35 to 0.65 are explored using inner predictions. Final configuration and threshold use full-cohort inner predictions before final fitting.')
    section('Release gate and interpretation', 'Accuracy must increase. Recall and ROC-AUC may decrease by at most 0.02; Brier score may increase by at most 0.01. These are engineering tolerances. Promotion after outer evaluation and the subsequent RCA trial following a failed broad search add selection optimism. Small gains are descriptive, not proof of statistical significance or external clinical performance.')

    heading(4, 'Data transfer pipeline', 'One response owns the current scores, explanations and reference artery colors.')
    table([['Stage', 'Data and action'], ['1. Patient form', 'Demographics, examination, symptoms, ECG, laboratory and echo measurements'], ['2. Browser -> API', 'JSON POST /api/v1/predict; units and original measurement aliases preserved'], ['3. Validation -> features', 'Pydantic range/category checks, row-local BMI and ordered 1 x 84 float32 vector'], ['4. Features -> predictors', 'Four calibrated probabilities; apply stored class thresholds before display rounding'], ['5. Explanations and colors', 'Deployed-probability domain explanations, source lineage and LAD/LCX/RCA colors'], ['6. API -> database', 'Validated inputs, predictions, explanations, UUID, model hash and immutable assessment snapshot'], ['7. API -> dashboard', 'JSON updates cards, selected-vessel evidence and Three.js mesh colors together']], [135, 364])
    section('Edits, errors and saved reports', 'After the first assessment, valid input edits trigger reassessment after 700 ms. Superseded requests are cancelled, late responses ignored and stale evidence hidden. Invalid input returns 422. Persistence errors roll back the database transaction. PDF assessment downloads read the saved snapshot and never rerun a model or use edited form values.')
    section('Training stays offline', 'The Excel cohort is consumed only by offline training/evaluation commands. Prediction requests never fit models. Final release weights are loaded at backend startup; restart the backend after replacement or rollback. Patient requests do not transfer the training workbook to the browser.')

    heading(5, '3D mapping and interpretability', 'Reference anatomy gives vessel context. It does not provide patient-specific diagnostic imaging.')
    table([['Prediction', 'Response key', 'Displayed structure'], ['LAD', 'vessel_colors_3d.lad', 'Left anterior descending'], ['LCX', 'vessel_colors_3d.lcx', 'Left circumflex'], ['RCA', 'vessel_colors_3d.rca', 'Right coronary artery']], [65, 210, 224])
    section('Geometry and interaction', 'The mesh-processing script normalizes the supplied anatomy resource. The browser loads the local static anatomy JSON, with the backend anatomy endpoint as fallback. Three.js provides rotation, zoom and linked artery selection. Myocardium remains neutral; whole-vessel probabilities color the three corresponding reference structures.')
    section('Probability versus classification', 'Green indicates probability below 35%; amber indicates 35% to below 65%; red indicates 65% or above. These bands do not change when a class threshold changes. Predicted status is CAD/Normal or Stenotic/Normal, determined from the original probability and the stored per-target threshold. A probability is not a measured percentage of blockage.')
    section('Explanation contract', 'Primary seven-domain Shapley allocations query the actual calibrated predictor for all domain coalitions. The synthetic default reference probability plus contributions reconstructs the assessed probability. Reference choice and domain grouping affect attribution; mixed profiles may be implausible. This is not a causal or individual-feature clinical effect. Separate historical XGBoost TreeSHAP remains explicitly labeled as independent log-odds evidence.')
    section('Safety and evaluation boundary', 'No score locates a lesion, and RWMA is not mapped to a 3D lesion coordinate. Sample cases come from the training cohort and demonstrate functionality only. Clinical operating points, external validation and confidence intervals have not been established.')

    heading(6, 'Reproduce, verify and operate', 'Run from the repository root using the pinned local Python runtime and the existing frontend dependencies.')
    table([['Task', 'Command'], ['Evaluate and stage', '.venv/bin/python scripts/improve_models.py --targets RCA'], ['Evaluate and release', '.venv/bin/python scripts/improve_models.py --targets RCA --deploy'], ['Audit saved release', '.venv/bin/python scripts/improve_models.py --verify artifacts/model_releases/<release-id>'], ['Backend regression', '.venv/bin/python -m pytest testing/backend -q'], ['Frontend regression', 'npm --prefix frontend test'], ['Production web build', 'npm --prefix frontend run build'], ['Start application', './deploy/scripts/start.sh']], [132, 367])
    section('Provenance and rollback', 'A release directory contains baseline weights and benchmarks, final weights, aggregate summary, owner-readable private OOF records and archived source. Audit recomputes metrics and verifies hashes, fold coverage and threshold decisions. Restore the two baseline artifacts into artifacts/ and restart the backend to roll back. Preserve release directories for historical assessment traceability.')
    section('Model Quality Lab', 'The current Lab evaluates fixed cloned target-specific deployed recipes at saved thresholds and matches the serving bundle hash. RCA uses LightGBM sigmoid CV3 and threshold 0.40; other targets use voting sigmoid CV5 and threshold 0.50. This fixed-configuration evaluation is separate from nested release-selection evidence. Older archives remain preserved and become stale when hashes differ.')
    story.append(p('References: supplied Track A.pdf; UCI dataset 411 (extension of Z-Alizadeh Sani); scikit-learn 1.7 nested cross-validation and probability-calibration documentation. See docs/DATA_PIPELINE.md for source links and detailed contracts.', 'SmallCV'))
    story.append(p('Demonstration video: the problem statement requests a 3-10 minute YouTube demonstration. Recording, publication and a checked URL remain open. Clinical review, external data, geometry licensing and clean Docker runtime verification remain independent deliverables.', 'SmallCV'))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#51665d'))
        canvas.setFont('Helvetica', 8)
        canvas.drawString(48, 27, 'CardioVision AI | Research and educational use')
        canvas.drawRightString(A4[0] - 48, 27, f'{doc.page} / 6')
        canvas.restoreState()

    output.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(output), pagesize=A4, leftMargin=48, rightMargin=48,
                      topMargin=45, bottomMargin=48, title='CardioVision Track A - Model Update and Data Pipeline').build(story, onFirstPage=footer, onLaterPages=footer)
    if len(PdfReader(output).pages) != 6:
        raise ValueError('Documentation exceeds Track A six-page limit; revise layout')
    print(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'output/pdf/cardiovision-track-a.pdf')
    args = parser.parse_args()
    build(args.release, args.output)
