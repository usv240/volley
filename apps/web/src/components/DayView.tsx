import { Info } from "./Info";

/**
 * A day, like steps.
 *
 * Hours across, turns per hour as bars in one hue, the best hour
 * labelled, hours with no child speech shown as "away" rather than as
 * zero. Under 640 px the row becomes a list, one hour per line, because
 * fourteen bars in 360 px are a texture, not a chart. A table sits
 * behind an i-button for anyone who wants the numbers as numbers.
 *
 * Colour never carries the meaning alone: the best hour has a label,
 * away hours have a word, and the bar length is printed beside it on
 * the phone layout.
 */

export interface Hour {
  hour: number;
  turns: number;
  utterances_child: number;
  questions_adult?: number;
}

export interface Day {
  date: string;
  turns: number;
  hours: Hour[];
  best_hour: number | null;
  quietest_hour_with_child: number | null;
  longest_volley: number;
  questions_adult: number;
  words_discarded: number;
}

export function clock(h: number): string {
  const x = h % 24;
  if (x === 0) return "12am";
  if (x === 12) return "12pm";
  return x < 12 ? `${x}am` : `${x - 12}pm`;
}

export function DayView({ day, child, simulated }: { day: Day; child: string | null; simulated: boolean }) {
  const width = Math.max(1, ...day.hours.map((h) => h.turns));
  const who = child ?? "your child";
  return (
    <div className="card p-6 sm:p-8">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <p className="eyebrow">{simulated ? "A simulated family, labelled as one" : "The operator's own day"}</p>
          <p className="mt-2 flex items-baseline gap-3">
            <span className="display text-5xl text-ink">{day.turns}</span>
            <span className="text-muted">
              turns with {who} on {day.date} <Info term="turn" />
            </span>
          </p>
        </div>
        <dl className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <dt className="text-faint">
              best hour <Info term="bestHour" />
            </dt>
            <dd className="font-semibold text-ink">{day.best_hour === null ? "none yet" : clock(day.best_hour)}</dd>
          </div>
          <div>
            <dt className="text-faint">longest exchange</dt>
            <dd className="font-semibold text-ink">{day.longest_volley} turns</dd>
          </div>
          <div>
            <dt className="text-faint">
              questions <Info term="question" />
            </dt>
            <dd className="font-semibold text-ink">{day.questions_adult}</dd>
          </div>
        </dl>
      </div>

      <ol className="mt-6 hidden items-end gap-1 sm:flex" aria-label="Turns by hour">
        {day.hours.map((h) => {
          const away = h.utterances_child === 0;
          const best = h.hour === day.best_hour;
          return (
            <li key={h.hour} className="flex min-w-0 flex-1 flex-col items-center gap-1">
              <span className="text-xs text-faint">{away ? "" : h.turns}</span>
              <div className="flex h-32 w-full items-end">
                <div
                  className="w-full rounded-t"
                  style={{
                    height: `${away ? 2 : Math.max(4, Math.round((100 * h.turns) / width))}%`,
                    background: away ? "var(--line)" : "var(--chart-mark)",
                  }}
                  aria-hidden
                />
              </div>
              <span className={`text-xs ${best ? "font-semibold text-ink" : "text-faint"}`}>{clock(h.hour)}</span>
              <span className="text-[10px] text-faint">{away ? "away" : best ? "best" : ""}</span>
            </li>
          );
        })}
      </ol>

      <ul className="mt-6 space-y-2 sm:hidden" aria-label="Turns by hour">
        {day.hours.map((h) => {
          const away = h.utterances_child === 0;
          return (
            <li key={h.hour} className="flex items-center gap-3 text-sm">
              <span className="w-10 text-faint">{clock(h.hour)}</span>
              <span className="ew-track flex-1">
                {!away && <span className="ew-bar" style={{ width: `${Math.max(2, Math.round((100 * h.turns) / width))}%` }} />}
              </span>
              <span className="w-14 text-right text-ink">{away ? "away" : h.turns}</span>
            </li>
          );
        })}
      </ul>

      <p className="mt-4 text-sm text-muted">
        Hours with no child speech are shown as away <Info term="away" />, not as zero. {day.words_discarded} words were read and
        thrown away to make this <Info term="whatLeaves" />.
      </p>
    </div>
  );
}
