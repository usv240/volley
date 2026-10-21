"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "./ThemeToggle";

/**
 * The navigation, on screen the whole way down.
 *
 * A first-time visitor should be able to jump to the check, the Fire TV
 * steps, or the evidence from anywhere on the page, so the bar sticks.
 * It is translucent over the page rather than a solid band, so it never
 * hides the line of text underneath it.
 *
 * Eight links, a theme toggle and a call to action do not fit on one
 * row below about 1280px, and letting them wrap puts a two-line header
 * on the bar that is in nearly every shot of the demo. So labels never
 * break, the full row appears only where it fits, and below that the
 * links live behind Menu.
 */

const LINKS = [
  { href: "/#how", label: "How it counts" },
  { href: "/#day", label: "Your day" },
  { href: "/#privacy", label: "Privacy" },
  { href: "/#alexa", label: "Alexa+" },
  // The measured results stay on the home page; the agents, the impact
  // case and the tests have their own page. "Your Bee" went to make room:
  // Count your own, beside the links on every width, goes to the same place.
  { href: "/#evidence", label: "Results" },
  { href: "/evidence/", label: "Evidence" },
  { href: "/mine/", label: "Mine" },
];

export function Nav() {
  const [open, setOpen] = useState(false);
  const path = usePathname();
  const current = (href: string) => (href.startsWith("/#") ? undefined : path?.startsWith(href.replace(/\/$/, "")) ? "page" : undefined);
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-[color-mix(in_srgb,var(--bg)_82%,transparent)] backdrop-blur">
      <div className="mx-auto flex h-16 max-w-[1120px] items-center justify-between px-5 sm:px-8">
        <Link prefetch={false} href="/#top" className="display-sm text-2xl text-ink">
          Volley
        </Link>
        <nav className="hidden items-center gap-5 xl:flex" aria-label="Main">
          {LINKS.map((l) => (
            <Link prefetch={false}
              key={l.href}
              href={l.href}
              aria-current={current(l.href)}
              className="inline-flex min-h-11 items-center whitespace-nowrap text-sm text-muted transition-colors hover:text-ink aria-[current=page]:font-semibold aria-[current=page]:text-ink"
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="hidden items-center gap-3 md:flex">
          <ThemeToggle />
          <Link prefetch={false}
            href="/#yours"
            className="inline-flex min-h-11 items-center whitespace-nowrap rounded-[0.85rem] bg-[var(--accent)] px-4 text-sm font-semibold text-[var(--accent-ink)] transition-transform hover:-translate-y-px"
          >
            Count your own
          </Link>
        </div>
        <button
          type="button"
          className="ghost xl:hidden"
          aria-expanded={open}
          aria-label="Toggle menu"
          onClick={() => setOpen((v) => !v)}
        >
          Menu
        </button>
      </div>
      {open && (
        <div className="border-t border-line bg-surface px-5 py-4 xl:hidden">
          <nav className="flex flex-col" aria-label="Mobile">
            {LINKS.map((l) => (
              <Link prefetch={false} key={l.href} href={l.href} aria-current={current(l.href)} onClick={() => setOpen(false)} className="flex min-h-11 items-center text-base text-muted aria-[current=page]:font-semibold aria-[current=page]:text-ink">
                {l.label}
              </Link>
            ))}
            <Link prefetch={false} href="/#yours" onClick={() => setOpen(false)} className="flex min-h-11 items-center text-base font-semibold text-[var(--accent)]">
              Count your own
            </Link>
            <div className="pt-2 md:hidden">
              <ThemeToggle />
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
