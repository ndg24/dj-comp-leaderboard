// Real roster + real amounts as of the last nightly update.
// Mick Hooley and Noah Nye Wenner are confirmed at $0 — some donations come
// in through the general campaign rather than a DJ's own link, so the sum
// of amountRaised below will legitimately run behind siteConfig.totalRaised.
//
// Auto-updated nightly by scripts/gofundme-sync/sync.py. Manual adjustments
// (a DJ's own account giving, or general-campaign gifts a scrape can't see)
// live in scripts/gofundme-sync/accounts.json, not here.

export interface DJ {
  id: string;
  djName: string;
  fullName: string;
  school: string;
  amountRaised: number;
}

export const djs: DJ[] = [
  { id: "tabor-defore", djName: "DJ D4", fullName: "Tabor DeFore", school: "Vanderbilt", amountRaised: 60 },
  { id: "oliver-broek", djName: "So Broek", fullName: "Oliver Broek", school: "Vanderbilt", amountRaised: 10422 },
  // Tom has a standing +$5,000 from a verified check donation that doesn't show up in the tracked GoFundMe numbers.
  { id: "tom-saul", djName: "Tom Saul", fullName: "Tom Saul", school: "Vanderbilt", amountRaised: 7762 },
  { id: "daria-mehrnia", djName: "65th Vision", fullName: "Daria Mehrnia", school: "Vanderbilt", amountRaised: 115 },
  // Hunter has a standing +$355 from a donation made before this tracked account's history that doesn't show up in GoFundMe's own numbers.
  { id: "hunter-truitt", djName: "DJ HUNT", fullName: "Hunter Truitt", school: "Belmont", amountRaised: 485 },
  { id: "andrew-brodie", djName: "Andrew Brodie", fullName: "Andrew Brodie", school: "Tulane", amountRaised: 200 },
  { id: "yarden-sam", djName: "SOMA", fullName: "Yarden Sharon & Sam Veiner", school: "Vanderbilt", amountRaised: 598 },
  { id: "joshua-levy", djName: "Dj Astro", fullName: "Joshua Levy", school: "Vanderbilt", amountRaised: 5 },
  { id: "eli-gordon", djName: "EA", fullName: "Eli Gordon", school: "Vanderbilt", amountRaised: 58 },
  { id: "henry-wood", djName: "Nockon", fullName: "Henry Wood", school: "Vanderbilt", amountRaised: 850 },
  { id: "jasper-chazen", djName: "Sper", fullName: "Jasper Chazen", school: "Vanderbilt", amountRaised: 8737 },
  { id: "holden-hanenberger", djName: "Berger", fullName: "Holden Hanenberger", school: "Vanderbilt", amountRaised: 2735 },
  // Dylan has a standing +$1,000 from a donation linked to him that GoFundMe doesn't track, plus a temporary +$1,510 because GoFundMe's API ($11,725) lags his GoFundMe page ($13,235) as of 2026-09-22 - drop back to 1000 once the scrape catches up.
  { id: "dylan-steele", djName: "DJ Amplitude", fullName: "Dylan Steele", school: "Syracuse", amountRaised: 14235 },
  { id: "mick-hooley", djName: "HOOLZ", fullName: "Mick Hooley", school: "Vanderbilt", amountRaised: 0 },
  { id: "noah-wenner", djName: "Nyehilism", fullName: "Noah Nye Wenner", school: "Vanderbilt", amountRaised: 100 },
];

export const siteConfig = {
  goalAmount: 45000,
  // Real overall campaign total — updated nightly alongside the DJ amounts.
  // Includes donations not tied to any DJ's own link, so it may run ahead of
  // the sum of amountRaised across djs[].
  totalRaised: 44537,
  // Updated automatically every time sync.py writes this file.
  lastUpdated: "2026-09-22T22:50:41-05:00",
  donateUrl: "https://www.lightsonthelawn.org/dj-competition",
};

export function getRankedDJs(): (DJ & { rank: number })[] {
  return [...djs]
    .sort((a, b) => b.amountRaised - a.amountRaised)
    .map((dj, i) => ({ ...dj, rank: i + 1 }));
}
