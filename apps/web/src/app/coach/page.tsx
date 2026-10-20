import type { Metadata } from "next";
import { Mine } from "../../components/Mine";
import { Nav } from "../../components/Nav";

export const metadata: Metadata = {
  title: "Volley: a family's days, shared with you",
  description: "A family's counts, read-only, from a link they made for the person coaching them.",
};

/**
 * What a home visitor or a coach opens: the link a parent made with
 * `volley share`. Read-only by the service's rules, not only by this page.
 */
export default function CoachPage() {
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-[1120px] px-5 pb-24 pt-10 sm:px-8">
        <Mine mode="coach" />
      </main>
    </>
  );
}
