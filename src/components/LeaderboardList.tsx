import { DJ } from "@/data/djs";
import { formatCurrency } from "@/lib/format";

type RankedDJ = DJ & { rank: number };

const AMOUNT_CHIP: Record<number, string> = {
  1: "bg-lotl-pink text-white",
  2: "bg-lotl-rose text-lotl-black",
  3: "bg-lotl-mint text-lotl-black",
};

export default function LeaderboardList({ ranked }: { ranked: RankedDJ[] }) {
  return (
    <section className="bg-lotl-yellow">
      {ranked.map((dj) => (
        <div
          key={dj.id}
          className="flex items-center justify-between gap-3 px-5 py-4 border-b border-lotl-black/40 transition-transform hover:translate-x-1"
        >
          <div className="flex items-center gap-3 min-w-0">
            <span className="font-display text-2xl text-lotl-black shrink-0 w-9">
              {String(dj.rank).padStart(2, "0")}
            </span>
            <div className="min-w-0">
              <p className="font-display text-base tracking-wide uppercase text-lotl-black truncate">
                {dj.djName}
              </p>
              <p className="text-[10px] uppercase font-bold text-lotl-black/60 truncate">
                {dj.fullName} &middot; {dj.school}
              </p>
            </div>
          </div>
          <span
            className={`shrink-0 px-2.5 py-1 border-2 border-lotl-black font-display text-sm ${
              AMOUNT_CHIP[dj.rank] ?? "bg-lotl-white text-lotl-black"
            }`}
          >
            {formatCurrency(dj.amountRaised)}
          </span>
        </div>
      ))}
    </section>
  );
}
