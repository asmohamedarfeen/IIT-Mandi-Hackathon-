/** Fullscreen is optional and may be denied by the embedding browser. */
export async function toggleFullscreen(
  stage: { requestFullscreen?: () => Promise<void> } | null,
  page: { fullscreenElement: unknown; fullscreenEnabled?: boolean; exitFullscreen?: () => Promise<void> },
): Promise<string | null> {
  const exiting = Boolean(page.fullscreenElement);
  if (exiting ? !page.exitFullscreen : !stage?.requestFullscreen || page.fullscreenEnabled === false)
    return "Fullscreen is unavailable in this browser. You can still rotate and zoom the heart here.";
  try {
    if (exiting) await page.exitFullscreen!();
    else await stage!.requestFullscreen!();
    return null;
  } catch {
    return exiting
      ? "Fullscreen could not be closed. Try your browser’s Escape key."
      : "Fullscreen could not be opened. You can still rotate and zoom the heart here.";
  }
}
