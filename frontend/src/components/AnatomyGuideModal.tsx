import { Modal } from "./Modal";
import { VESSELS } from "../utils/vessels";
export function AnatomyGuideModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  return (
    <Modal open={isOpen} onClose={onClose} title="A map for understanding">
      <p className="modal-lead">
        Explore the coronary tree in its anatomical context.
      </p>
      {VESSELS.map((v) => (
        <details className="vessel-detail" key={v.key}>
          <summary>
            <i style={{ background: v.color }} />
            {v.key.toUpperCase()}
            <span>{v.name}</span>
            <b aria-hidden="true">+</b>
          </summary>
          <p>{v.description}</p>
        </details>
      ))}
      <h3>Reading the model</h3>
      <p>
        The heart is a shared BodyParts3D reference anatomy, not a scan of the
        assessed patient. Surface geometry remains registered across the
        myocardium and coronary trees. The left coronary stem is shown neutrally
        because it has no separate prediction target.
      </p>
      <p>
        Risk mode colors whole vessel trees by model output; it does not locate
        a narrowing or show blood flow. The pulse is an illustrative uniform
        motion, not a physiological simulation.
      </p>
      <div className="risk-key">
        <span>
          <i style={{ background: "#10B981" }} />
          Low &lt;35%
        </span>
        <span>
          <i style={{ background: "#F59E0B" }} />
          Intermediate 35–&lt;65%
        </span>
        <span>
          <i style={{ background: "#EF4444" }} />
          High ≥65%
        </span>
      </div>
      <p className="small-note">
        These are display thresholds, not diagnostic cutoffs. Drag to rotate,
        pinch or scroll to zoom. Use vessel focus or Reset view to navigate with
        a keyboard.
      </p>
    </Modal>
  );
}
