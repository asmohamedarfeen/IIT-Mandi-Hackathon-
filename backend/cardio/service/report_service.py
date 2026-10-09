"""PDF generation from an immutable, persisted inference snapshot."""
from io import BytesIO
from itertools import zip_longest
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak, KeepTogether

from backend.cardio.constants import CATEGORY_CODES
from backend.cardio.schemas.prediction_schema import PredictionResponse
from backend.cardio.service.prediction_service import FEATURE_DISPLAY_NAMES

INK = colors.HexColor("#25332c")
MUTED = colors.HexColor("#59665d")
PALE = colors.HexColor("#eef1e8")
LINE = colors.HexColor("#d6ddcf")
MEASUREMENT_LABELS = {**FEATURE_DISPLAY_NAMES, "ESR": "Erythrocyte Sedimentation Rate (mm/h)", "WBC": "White Blood Cell Count (/uL)", "PLT": "Platelet Count (1000/uL)"}


def _text(value):
    # Standard PDF fonts cover these clinical labels; escape other characters
    # explicitly rather than silently rendering unsupported glyphs as squares.
    text = str(value)
    for source, replacement in {"≥": ">=", "≤": "<=", "×": "x", "→": "->", "–": "-", "—": "-", "’": "'", "µ": "u", "²": "2"}.items():
        text = text.replace(source, replacement)
    return escape(text.encode("ascii", "backslashreplace").decode("ascii"))


def _value(key, value):
    if key in CATEGORY_CODES:
        labels = {"Sex": ["Female", "Male"], "BBB": ["None", "LBBB", "RBBB"], "VHD": ["None", "Mild", "Moderate", "Severe"], "Function Class": ["0", "I", "II", "III", "IV"], "Region RWMA": ["0", "1", "2", "3", "4"]}
        options = labels.get(key, ["No", "Yes"])
        try:
            return f"{options[int(value)]} (code {value})"
        except (ValueError, TypeError, IndexError):
            return str(value)
    return f"{value:.6g}" if isinstance(value, float) else str(value)


def generate_evidence_report(prediction: PredictionResponse) -> bytes:
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("ReportTitle", fontName="Helvetica-Bold", fontSize=26, leading=30, textColor=INK, spaceAfter=12))
    styles.add(ParagraphStyle("Section", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=INK, spaceAfter=12))
    styles.add(ParagraphStyle("Copy", fontSize=9, leading=13, textColor=INK, spaceAfter=7))
    styles.add(ParagraphStyle("SmallCopy", fontSize=8, leading=11, textColor=MUTED, spaceAfter=3))
    styles.add(ParagraphStyle("Cell", fontSize=8, leading=11, textColor=INK))
    styles.add(ParagraphStyle("RightCell", parent=styles["Cell"], alignment=TA_RIGHT))
    story = []
    evidence = prediction.evidence
    p = lambda value, style="Copy": Paragraph(_text(value), styles[style])

    def table(rows, widths, header=True, padding=7):
        result = Table([[p(cell, "Cell") for cell in row] for row in rows], colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
        commands = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), padding), ("BOTTOMPADDING", (0, 0), (-1, -1), padding), ("LINEBELOW", (0, 0), (-1, -1), .35, LINE)]
        if header:
            commands += [("BACKGROUND", (0, 0), (-1, 0), PALE)]
        result.setStyle(TableStyle(commands))
        return result

    story += [p("CARDIOVISION AI / EVIDENCE REPORT", "SmallCopy"), p("One assessment.\nComplete evidence.", "ReportTitle"), p("Research prototype - not a diagnosis", "Copy"), Spacer(1, 14)]
    story += [p(f"Case reference: {prediction.patient_id}"), p(f"Assessment ID: {evidence.assessment_id}"), p(f"Inference completed (UTC): {evidence.generated_at}"), Spacer(1, 16), p("Four model predictions", "Section")]
    risks = {"CAD": prediction.overall_cad, **prediction.vessels}
    story.append(table([["Target", "Model probability", "Display category"], *[[target, f"{risks[target].probability_percent:.1f}%", risks[target].risk_level] for target in ("CAD", "LAD", "LCX", "RCA")]], [65, 130, 316]))
    story += [Spacer(1, 14), p("Whole-vessel probabilities do not measure percentage blockage or locate a lesion. CAD is the overall coronary disease target; LAD, LCX and RCA are artery targets."), p("Display bands: green <35%; amber 35% to <65%; red >=65%. These are application display thresholds, not validated clinical decision boundaries."), Spacer(1, 14), p("Model provenance", "Section"), p(f"Application version: {evidence.application_version}"), p(f"Prediction: {evidence.prediction_model}"), p(f"Explanation: {evidence.explanation_model}"), p("Model artifact version (SHA-256):", "SmallCopy"), p(evidence.model_artifact_sha256 or "Unavailable", "SmallCopy"), p("A semantic training/model release version was not supplied. The artifact hash identifies the exact saved weights.", "SmallCopy"), p("This report reproduces the stored assessment snapshot. Downloading it does not rerun inference or use subsequently edited form values.")]

    story += [PageBreak(), p("Assessed input measurements", "Section"), p("Validated values used for this inference. Categories include their model code. Measurement units appear in the labels; numerical display is rounded to six significant digits.")]
    entries = list(evidence.clinical_inputs.items())
    half = (len(entries) + 1) // 2
    rows = [["Measurement", "Assessed value", "Measurement", "Assessed value"]]
    for left, right in zip_longest(entries[:half], entries[half:]):
        row = []
        for entry in (left, right):
            row.extend([MEASUREMENT_LABELS.get(entry[0], entry[0]), _value(*entry)] if entry else ["", ""])
        rows.append(row)
    story.append(table(rows, [170, 85, 171, 85], padding=4))
    story += [Spacer(1, 10), p("BMI can be supplied or calculated from height and weight. These are recorded clinical inputs, not direct measurements of artery blockage.", "SmallCopy")]

    for target in ("CAD", "LAD", "LCX", "RCA"):
        risk = risks[target]
        story += [PageBreak(), p(f"{target} / prediction and explanation", "Section"), p(f"Model probability: {risk.probability_percent:.1f}% | {risk.risk_level}"), p(risk.anatomical_description)]
        if target != "CAD":
            story.append(p(f"Risk-map source: vessel_colors_3d.{target.lower()} = {prediction.vessel_colors_3d[target.lower()]} | model probability = {risk.probability}"))
        story += [p("Patient-specific factors ranked by absolute contribution. Positive values increase the independent XGBoost output; negative values decrease it. Units are log-odds relative to that model's baseline, not changes in ensemble probability."), Spacer(1, 8)]
        factors = sorted(prediction.shap_explanations.get(target, []), key=lambda item: abs(item.contribution), reverse=True)
        if not factors:
            story.append(p("No contributing factors were supplied for this target."))
        for rank, factor in enumerate(factors, 1):
            block = [table([[f"{rank}. {factor.display_name}", f"{factor.contribution:+.4f} log-odds"]], [386, 125], padding=4), p(f"{'Calculated' if factor.feature_kind == 'derived' else 'Model'} feature value: {factor.model_input_value:.6g}", "SmallCopy")]
            sources = []
            for source in factor.source_measurements:
                if source.input_key in evidence.clinical_inputs:
                    sources.append(f"{MEASUREMENT_LABELS.get(source.input_key, source.input_key)}: {_value(source.input_key, evidence.clinical_inputs[source.input_key])}")
            block.append(p("Assessed sources: " + ("; ".join(sources) or "Unavailable"), "SmallCopy"))
            if factor.derivation:
                block.append(p(factor.derivation, "SmallCopy"))
            block.append(Spacer(1, 5))
            story.append(KeepTogether(block))

    validation = evidence.validation_summary
    story += [PageBreak(), p("Validation summary and limitations", "Section"), p(f"Dataset: {validation.get('record_count', 'Unavailable')} records. {validation.get('method', 'Validation metadata unavailable.')}"), p(validation.get("source", "Validation source unavailable."), "SmallCopy")]
    metrics = validation.get("ensemble_metrics", {})
    if metrics:
        columns = ["roc_auc", "accuracy", "precision", "recall", "f1", "specificity", "mcc"]
        rows = [["Target", "ROC-AUC", "Accuracy", "Precision", "Recall", "F1", "Specificity", "MCC"]]
        for target in ("CAD", "LAD", "LCX", "RCA"):
            values = metrics.get(target, {})
            rows.append([target] + [f"{values[key]:.4f}" if key in values else "N/A" for key in columns])
        story.append(table(rows, [45, 66, 66, 66, 60, 48, 100, 60]))
    story += [Spacer(1, 14), p(validation.get("limitations", "Validation of deployed calibrated models has not been established.")), p("Confidence interval: unavailable. Model probability is not a measure of model certainty."), Spacer(1, 8)]
    for index, limitation in enumerate(evidence.limitations, 1):
        story.append(p(f"{index}. {limitation}"))
    story += [Spacer(1, 12), p("Clinical safety", "Section"), p(prediction.disclaimer), p("The supplied sample cases belong to the training dataset; demonstrations are not held-out clinical validation. Reference anatomy is not patient-specific imaging."), p("This download contains the assessed input measurements and results. Handle it as confidential clinical research data. Non-ASCII characters outside the supported clinical labels are represented with explicit character escapes.", "SmallCopy")]

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(LINE)
        canvas.line(42, 37, A4[0] - 42, 37)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(42, 25, f"Assessment {evidence.assessment_id}")
        canvas.drawRightString(A4[0] - 42, 25, f"Research only | Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=50, title="CardioVision assessment evidence", author="CardioVision AI")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
