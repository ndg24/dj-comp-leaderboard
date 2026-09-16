import Header from "@/components/Header";
import Podium from "@/components/Podium";
import LeaderboardList from "@/components/LeaderboardList";
import ProgressDonate from "@/components/ProgressDonate";
import { getRankedDJs, siteConfig } from "@/data/djs";

export default function Home() {
  const ranked = getRankedDJs();

  return (
    <div className="w-full flex-1 flex justify-center">
      <main className="w-full max-w-[430px] bg-lotl-yellow border-x-0 sm:border-x-2 border-lotl-black min-h-screen flex flex-col">
        <Header />
        <Podium topThree={ranked.slice(0, 3)} />
        <ProgressDonate
          total={siteConfig.totalRaised}
          goal={siteConfig.goalAmount}
          donateUrl={siteConfig.donateUrl}
        />
        <LeaderboardList ranked={ranked} />
      </main>
    </div>
  );
}
