import { siteConfig } from "@/data/djs";

function formatUpdated(iso: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(new Date(iso));
}

export default function Header() {
  return (
    <header className="bg-lotl-yellow border-b-2 border-lotl-black px-5 pt-4 pb-6">
      <div className="flex items-center justify-end gap-1.5 mb-3">
        <span className="w-2 h-2 rounded-full bg-lotl-pink shrink-0" />
        <span className="text-[10px] tracking-widest uppercase font-bold text-lotl-black">
          Updated {formatUpdated(siteConfig.lastUpdated)}
        </span>
      </div>
      <h1 className="font-display text-[19vw] leading-[0.85] tracking-tight text-lotl-black sm:text-[80px]">
        LOTL
      </h1>
      <p className="mt-2 text-sm sm:text-base font-bold uppercase tracking-wide text-lotl-black">
        Student DJ Competition Leaderboard
      </p>
    </header>
  );
}
