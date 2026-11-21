/** Static content of the help page (E9). Only non-profit organizations and official sources. */

export type OfficialLink = { title: string; text: string; href: string };

export const OFFICIAL_LINKS: OfficialLink[] = [
  {
    title: "ZUS – zasiłki",
    text: "Opisy spraw, formularze i bieżące wyjaśnienia dotyczące zasiłku macierzyńskiego, chorobowego i opiekuńczego.",
    href: "https://www.zus.pl",
  },
  {
    title: "Ministerstwo Rodziny, Pracy i Polityki Społecznej – urlop rodzicielski",
    text: "Zasady urlopu rodzicielskiego, w tym podział między rodziców i urlop w częściach.",
    href: "https://www.gov.pl/web/rodzina/urlop-rodzicielski",
  },
  {
    title: "Państwowa Inspekcja Pracy – rodzicielstwo",
    text: "Porady prawne o uprawnieniach pracowników związanych z rodzicielstwem, ochronie przed zwolnieniem i wnioskach.",
    href: "https://www.pip.gov.pl/dla-pracodawcow/porady-prawne/rodzicielstwo",
  },
  {
    title: "Dodatkowy urlop macierzyński dla rodziców wcześniaków",
    text: "Pytania i odpowiedzi Ministerstwa o dodatkowym urlopie dla rodziców wcześniaków i dzieci hospitalizowanych.",
    href: "https://www.gov.pl/web/rodzina/rodzice-wczesniakow-z-dluzszym-urlopem-macierzynskim-jest-projekt-ustawy",
  },
  {
    title: "Ważne zmiany dla rodziców, którzy stracili dziecko",
    text: "Informacja Ministerstwa o urlopie i świadczeniach po stracie dziecka.",
    href: "https://www.gov.pl/web/rodzina/wazne-zmiany-dla-rodzicow-ktorzy-stracili-dziecko",
  },
  {
    title: "Odpis aktu stanu cywilnego (gov.pl)",
    text: "Oficjalny wniosek o odpis zupełny lub skrócony aktu urodzenia.",
    href: "https://www.gov.pl/web/cyfryzacja/rejestr-stanu-cywilnego",
  },
];

export type Organization = { name: string; text: string; krs?: string; href?: string };
export type SupportGroup = { id: string; title: string; intro: string; organizations: Organization[] };

export const SUPPORT_GROUPS: SupportGroup[] = [
  {
    id: "loss",
    title: "Strata dziecka lub ciąży",
    intro:
      "Po poronieniu, martwym urodzeniu lub śmierci dziecka rodzice mogą skorzystać z bezpłatnej pomocy psychologicznej i grup wsparcia w żałobie. Wiele hospicjów dziecięcych przyjmuje także rodziców spoza swojej opieki.",
    organizations: [
      {
        name: "Fundacja Pomorze Dzieciom",
        text: "Hospicjum perinatalne i centrum wsparcia po stracie na Pomorzu.",
      },
      {
        name: "Fundacja Gajusz (Łódź)",
        text: "Prowadzi między innymi hospicjum perinatalne dla rodzin, które dowiadują się o nieuleczalnej chorobie dziecka.",
      },
      {
        name: "Fundacja Krakowskie Hospicjum dla Dzieci im. ks. Józefa Tischnera",
        text: "Hospicjum perinatalne dla rodziców oczekujących narodzin nieuleczalnie chorego dziecka oraz hospicjum domowe.",
        href: "https://www.hospicjumtischnera.org",
      },
      {
        name: "Fundacja Hospicyjna (Gdańsk)",
        text: "Program wsparcia w żałobie „Tumbo Pomaga” dla dzieci, młodzieży i rodziców.",
        krs: "0000201002",
        href: "http://www.fundacjahospicyjna.pl",
      },
    ],
  },
  {
    id: "preterm",
    title: "Wcześniak lub dziecko w szpitalu",
    intro:
      "Rodzice wcześniaków mogą liczyć na poradniki, kontakt z innymi rodzicami i pomoc w zdobyciu sprzętu. Dodatkowe informacje o urlopie dla rodziców wcześniaków znajdziesz w kalkulatorze (uzupełniający urlop macierzyński).",
    organizations: [
      {
        name: "Fundacja Koalicja dla Wcześniaka",
        text: "Edukacja i wsparcie rodziców wcześniaków, poradnik „Bezpieczny wcześniak – w szpitalu i w domu”.",
      },
      {
        name: "Fundacja Wcześniak Rodzice-Rodzicom",
        text: "Bezpłatna wypożyczalnia sprzętu (m.in. monitory oddechu, laktatory), program Mentor i grupy wsparcia.",
        krs: "0000191989",
        href: "https://wczesniak.pl",
      },
    ],
  },
  {
    id: "illness",
    title: "Ciężko chore dziecko",
    intro:
      "Hospicja domowe dla dzieci opiekują się dzieckiem w domu i wspierają rodzinę: pomocą medyczną, psychologiczną, rehabilitacją i opieką wytchnieniową.",
    organizations: [
      {
        name: "Fundacja Wrocławskie Hospicjum dla Dzieci",
        text: "Hospicjum domowe, hospicjum perinatalne i opieka wytchnieniowa dla rodzin.",
      },
      {
        name: "Fundacja Podkarpackie Hospicjum dla Dzieci",
        text: "Hospicjum perinatalne i grupa wsparcia dla rodziców w żałobie.",
        krs: "0000265120",
      },
      {
        name: "Fundacja Domowe Hospicjum Dziecięce Promyczek",
        text: "Domowa opieka paliatywna oraz pomoc psychologiczna i duszpasterska dla rodzin i rodziców w żałobie (Mazowsze).",
        krs: "0000336442",
      },
      {
        name: "Fundacja Hospicjum Nadzieja (Toruń)",
        text: "Hospicjum domowe dla dzieci chorych onkologicznie, z chorobami genetycznymi i wielonarządowymi.",
        krs: "0000017073",
      },
    ],
  },
];

export const SUPPORT_DISCLAIMER =
  "Lista jest przykładowa i obejmuje wyłącznie organizacje niekomercyjne. Zasięg działania bywa regionalny, a dane kontaktowe się zmieniają – sprawdź aktualne informacje na stronie organizacji lub w rejestrze KRS.";
