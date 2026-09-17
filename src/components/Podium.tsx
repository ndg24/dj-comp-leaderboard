import { DJ } from "@/data/djs";
import { formatCurrency } from "@/lib/format";

type RankedDJ = DJ & { rank: number };

function PodiumColumn({
  dj,
  pedestalColor,
  pedestalHeight,
  rankTextSize,
}: {
  dj: RankedDJ;
  pedestalColor: string;
  pedestalHeight: string;
  rankTextSize: string;
}) {
  return (
    <div className="flex flex-col items-center w-[30%] max-w-[128px]">
      <div className="w-full bg-lotl-white border-2 border-lotl-black px-1.5 py-2 text-center">
        <p className="font-display text-[13px] sm:text-sm leading-tight uppercase truncate">
          {dj.djName}
        </p>
        <p className="text-[7px] sm:text-[8px] uppercase font-bold text-lotl-black/60 leading-tight truncate">
          {dj.fullName}
        </p>
        <p className="mt-1 font-display text-sm sm:text-base text-lotl-pink leading-none">
          {formatCurrency(dj.amountRaised)}
        </p>
      </div>
      <div
        className={`w-full border-2 border-t-0 border-lotl-black flex items-center justify-center font-display text-lotl-black ${pedestalColor} ${pedestalHeight} ${rankTextSize}`}
      >
        {String(dj.rank).padStart(2, "0")}
      </div>
    </div>
  );
}

export default function Podium({ topThree }: { topThree: RankedDJ[] }) {
  const [first, second, third] = topThree;

  return (
    <section className="bg-lotl-pink border-b-2 border-lotl-black px-4 pt-8 pb-0">
      <p className="text-center text-[10px] uppercase font-bold tracking-widest text-white/80 mb-4">
        Top Fundraisers
      </p>
      <div className="flex items-end justify-center gap-2 sm:gap-3">
        {second && (
          <PodiumColumn
            dj={second}
            pedestalColor="bg-lotl-rose"
            pedestalHeight="h-16"
            rankTextSize="text-2xl"
          />
        )}
        {first && (
          <PodiumColumn
            dj={first}
            pedestalColor="bg-lotl-yellow"
            pedestalHeight="h-24"
            rankTextSize="text-3xl"
          />
        )}
        {third && (
          <PodiumColumn
            dj={third}
            pedestalColor="bg-lotl-mint"
            pedestalHeight="h-12"
            rankTextSize="text-xl"
          />
        )}
      </div>
    </section>
  );
}
