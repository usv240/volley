import type { Metadata } from "next";
import { Coach } from "../../components/Coach";
import { Nav } from "../../components/Nav";

export const metadata: Metadata = {
  title: "Volley: the families you follow",
  description: "Every family that shared its counts with you, one row each, read-only, from the links the families made.",
};

/**
 * What a home visitor or a coach opens: the links parents made with
 * `volley share`, remembered in this browser as one list. Read-only by
 * the service's rules, not only by this page.
 */
export default function CoachPage() {
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-[1120px] px-4 pb-24 pt-8 sm:px-8 sm:pt-10">
        <Coach />
      </main>
    </>
  );
}
