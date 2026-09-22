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
  { id: "oliver-broek", djName: "So Broek", fullName: "Oliver Broek", school: "Vanderbilt", amountRaised: 8172 },
  { id: "tom-saul", djName: "Tom Saul", fullName: "Tom Saul", school: "Vanderbilt", amountRaised: 2762 },
  { id: "daria-mehrnia", djName: "65th Vision", fullName: "Daria Mehrnia", school: "Vanderbilt", amountRaised: 115 },
  // Hunter has a standing +$355 from a donation through his personal account that doesn't show up in the tracked numbers.
  { id: "hunter-truitt", djName: "DJ HUNT", fullName: "Hunter Truitt", school: "Belmont", amountRaised: 485 },
  { id: "andrew-brodie", djName: "Andrew Brodie", fullName: "Andrew Brodie", school: "Tulane", amountRaised: 200 },
  { id: "yarden-sam", djName: "SOMA", fullName: "Yarden Sharon & Sam Veiner", school: "Vanderbilt", amountRaised: 598 },
  { id: "joshua-levy", djName: "Dj Astro", fullName: "Joshua Levy", school: "Vanderbilt", amountRaised: 5 },
  { id: "eli-gordon", djName: "EA", fullName: "Eli Gordon", school: "Vanderbilt", amountRaised: 58 },
  { id: "henry-wood", djName: "Nockon", fullName: "Henry Wood", school: "Vanderbilt", amountRaised: 350 },
  { id: "jasper-chazen", djName: "Sper", fullName: "Jasper Chazen", school: "Vanderbilt", amountRaised: 8402 },
  { id: "holden-hanenberger", djName: "Berger", fullName: "Holden Hanenberger", school: "Vanderbilt", amountRaised: 2735 },
  { id: "dylan-steele", djName: "DJ Amplitude", fullName: "Dylan Steele", school: "Syracuse", amountRaised: 9964 },
  { id: "mick-hooley", djName: "HOOLZ", fullName: "Mick Hooley", school: "Vanderbilt", amountRaised: 0 },
  { id: "noah-wenner", djName: "Nyehilism", fullName: "Noah Nye Wenner", school: "Vanderbilt", amountRaised: 100 },
];

export const siteConfig = {
  goalAmount: 40000,
  // Real overall campaign total — updated nightly alongside the DJ amounts.
  // Includes donations not tied to any DJ's own link, so it may run ahead of
  // the sum of amountRaised across djs[].
  totalRaised: 37231,
  // Updated automatically every time sync.py writes this file.
  lastUpdated: "2026-09-22T13:51:14-05:00",
  donateUrl: "https://www.lightsonthelawn.org/dj-competition",
};

export function getRankedDJs(): (DJ & { rank: number })[] {
  return [...djs]
    .sort((a, b) => b.amountRaised - a.amountRaised)
    .map((dj, i) => ({ ...dj, rank: i + 1 }));
}
