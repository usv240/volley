export const REPO = "https://github.com/usv240/volley";

/** The footer every long page ends on: the licence, the mark, and what this is not. */
export function Footer() {
  return (
    <footer className="mt-24 border-t border-line pt-8 text-sm text-muted">
      <p>
        Open source, MIT.{" "}
        <a className="text-[var(--accent)] underline underline-offset-4" href={REPO}>
          The repository
        </a>{" "}
        carries the evidence, the prior art, and every number on this page as a test. LENA is a registered mark of the LENA
        Foundation; Volley implements the published definition and is not affiliated.
      </p>
      <p className="mt-3">Not a diagnosis, not a test, a count. Built for the Build, Ship, Shape: Amazon Developer Hackathon.</p>
    </footer>
  );
}
