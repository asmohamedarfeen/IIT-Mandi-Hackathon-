# CardioVision professional anatomy and assessment redesign

## Intent
Deliver an end-to-end professional cardiovascular research demo with a redesigned entire interface, faithful supplied anatomical heart geometry in Three.js, polished motion, and verified model inference. User expressly requested planning and immediate execution with minimal questions and Subagent-Driven Development.

## Design
An editorial clinical workspace: warm ivory, charcoal typography, restrained coral/red accent, and a dark cinematic anatomical stage. Geist typography, artistic asymmetry hero with wide heading and actual live heart. Navigation links to assessment and evidence, benchmark and anatomy dialogs. Four equal risk summaries, organized clinical form, real sample case carousel, vessel accordion, clear explanation panel. Use spacious chapters without obstructing clinical workflow. GSAP card stacking and desktop scroll pinning enhance the anatomy/evidence story; reduce motion on request and disable pinning on narrow displays. No fabricated testimonials, random stock images, decorative fake metrics, emojis, or technical error dumps.

## Anatomy and model truth
Use the repository's BodyParts3D OBJ archive. Preserve coordinates and include complete supplied chamber walls and coronary surfaces without arbitrary subsampling. Document structure sources and omissions; exact means faithful to supplied mesh, not a patient-specific scan or simulated physiology. Render realistic warm tissue with shaded surfaces; distinguish coronary arteries in anatomy mode and color by prediction in risk mode. Orbit/zoom, view reset, chamber transparency, territory focus and illustrative heartbeat must work repeatedly without scene recreation bugs.
Check existing joblib model bundle in a Python 3.11 environment. Fix category encoding and BMI consistency, sample round trips and misleading explanation/evaluation descriptions. Existing weights need not be retrained to alter appearance. Retain API shape and trained artifacts, and state measured limitations honestly.

## Acceptance
Frontend production build and backend tests pass in reproducible local environments. Browser smoke checks exercise actual 3D render, model prediction, sample selection, all viewer controls, dialogs, mobile layout and reduced motion. No stale prediction presented as current input, no blank heart after controls, no fabricated readiness or performance. Local runnable preview and reviewable committed branch. Do not publish or push.
