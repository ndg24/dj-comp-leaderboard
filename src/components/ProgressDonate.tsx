import { formatCurrency } from "@/lib/format";

export default function ProgressDonate({
  total,
  goal,
  donateUrl,
}: {
  total: number;
  goal: number;
  donateUrl: string;
}) {
  const pct = Math.min(100, Math.round((total / goal) * 100));

  return (
    <section className="bg-lotl-cyan border-b-2 border-lotl-black px-5 py-4">
      <div className="w-full h-4 border-2 border-lotl-black bg-lotl-white overflow-hidden">
        <div
          className="h-full bg-lotl-pink"
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="mt-2.5 flex items-end justify-between gap-3">
        <div className="min-w-0">
          <p className="font-display text-2xl leading-none text-lotl-black">
            {formatCurrency(total)}
          </p>
          <p className="text-[9px] uppercase font-bold text-lotl-black/60 mt-0.5">
            of {formatCurrency(goal)} goal &middot; {pct}%
          </p>
        </div>
        <a
          href={donateUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 bg-lotl-pink text-white font-display text-xs tracking-wide px-4 py-2.5 border-2 border-lotl-black hover:bg-lotl-black transition-colors"
        >
          DONATE &rarr;
        </a>
      </div>
    </section>
  );
}
