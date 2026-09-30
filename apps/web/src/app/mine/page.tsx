import type { Metadata } from "next";
import { Mine } from "../../components/Mine";
import { Nav } from "../../components/Nav";

export const metadata: Metadata = {
  title: "Volley: your days",
  description: "Your own household's counts, read from the service with your key, in your browser.",
};

/**
 * The parent's own page. Everything on it is fetched from the browser
 * with the key `volley connect` handed over, so the static site never
 * holds a household; see the Mine component for how the key arrives.
 */
export default function MinePage() {
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-[1120px] px-5 pb-24 pt-10 sm:px-8">
        <Mine />
      </main>
    </>
  );
}
