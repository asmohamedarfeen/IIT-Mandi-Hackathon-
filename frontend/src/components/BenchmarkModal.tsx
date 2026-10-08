import { useState } from "react";
import { BenchmarkData, ModelCVMetrics } from "../utils/types";
import { Modal } from "./Modal";
export function BenchmarkModal({
  isOpen,
  onClose,
  benchmarkData,
  onRetry,
  loading,
}: {
  isOpen: boolean;
  onClose: () => void;
  benchmarkData: BenchmarkData | null;
  onRetry: () => void;
  loading: boolean;
}) {
  const [target, setTarget] = useState("CAD");
  const metrics: [keyof ModelCVMetrics, string][] = [
    ["roc_auc", "ROC-AUC"],
    ["f1", "F1"],
    ["accuracy", "Accuracy"],
    ["precision", "Precision"],
    ["recall", "Recall"],
    ["specificity", "Specificity"],
    ["mcc", "MCC"],
  ];
  return (
    <Modal
      open={isOpen}
      onClose={onClose}
      title="The evidence behind the model"
    >
      <p className="modal-lead">
        Recorded stratified 10-fold cross-validation on 303 records.
      </p>
      <p className="evidence-note">
        These metrics evaluate uncalibrated candidate models. The deployed
        ensemble is calibrated afterward; these scores do not establish its
        clinical calibration or external performance.
      </p>
      <div className="segmented">
        {["CAD", "LAD", "LCX", "RCA"].map((t) => (
          <button
            key={t}
            aria-pressed={t === target}
            onClick={() => setTarget(t)}
          >
            {t}
          </button>
        ))}
      </div>
      {benchmarkData ? (
        <div
          className="table-scroll"
          tabIndex={0}
          aria-label="Model benchmark table"
        >
          <table>
            <caption>{target} · saved cross-validation metrics</caption>
            <thead>
              <tr>
                <th scope="col">Model</th>
                {metrics.map(([, name]) => (
                  <th scope="col" key={name}>
                    {name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.entries(benchmarkData.targets[target] || {}).map(
                ([model, scores]) => (
                  <tr key={model}>
                    <th scope="row">{model}</th>
                    {metrics.map(([key]) => (
                      <td key={key}>{scores[key].toFixed(3)}</td>
                    ))}
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-state">
          <p>
            {loading
              ? "Loading model evidence…"
              : "Model evidence could not be loaded."}
          </p>
          <button className="button" disabled={loading} onClick={onRetry}>
            Retry evidence
          </button>
        </div>
      )}
      <p className="small-note">
        Targets are excluded from model inputs. Explanations use separate
        XGBoost models and should be interpreted as surrogate attributions.
        Training examples are not validation cases.
      </p>
    </Modal>
  );
}
