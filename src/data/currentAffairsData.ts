export interface CurrentAffairsCategory {
  id: string;
  title: string;
  gsPaper: 'GS-1' | 'GS-2' | 'GS-3' | 'GS-4';
  description: string;
  keySources: {
    name: string;
    type: 'Official Portal' | 'Daily Newspaper' | 'Monthly Magazine' | 'Analysis Video';
    url: string;
    free: boolean;
    howToUse: string;
  }[];
  highYieldTopics: string[];
}

export const CURRENT_AFFAIRS_CATEGORIES: CurrentAffairsCategory[] = [
  {
    id: 'ca-economy',
    title: 'Economy & Agriculture (GS-3)',
    gsPaper: 'GS-3',
    description: 'Macro indicators, Union Budget, Economic Survey, RBI monetary stance, trade deficits, MSP & farm issues.',
    keySources: [
      {
        name: 'Ministry of Finance & RBI Notifications',
        type: 'Official Portal',
        url: 'https://rbi.org.in',
        free: true,
        howToUse: 'Check bi-monthly MPC statements for official inflation & GDP growth commentary.'
      },
      {
        name: 'The Hindu & Indian Express Explained (Economy)',
        type: 'Daily Newspaper',
        url: 'https://indianexpress.com/section/explained/',
        free: true,
        howToUse: 'Read 1 explanatory article daily on inflation, export numbers, or fiscal deficit.'
      },
      {
        name: 'PIB Economy Highlights',
        type: 'Official Portal',
        url: 'https://pib.gov.in',
        free: true,
        howToUse: 'Review monthly GST collection releases and core sector output data.'
      }
    ],
    highYieldTopics: [
      'RBI Monetary Policy transmission & liquidity',
      'Capital Expenditure (CapEx) vs Revenue Expenditure',
      'Agricultural supply chains, e-NAM, and MSP debates',
      'Free Trade Agreements (FTAs) and semiconductor manufacturing'
    ]
  },
  {
    id: 'ca-environment',
    title: 'Environment, Climate & Disaster Management (GS-3)',
    gsPaper: 'GS-3',
    description: 'UNFCCC COP resolutions, Ramsar sites additions, IUCN red list updates, species in news, and climate adaptation.',
    keySources: [
      {
        name: 'MoEFCC Official Portal & PIB Environment',
        type: 'Official Portal',
        url: 'https://moef.gov.in',
        free: true,
        howToUse: 'Track new Tiger Reserves, Biosphere Reserves, and Elephant corridors declared.'
      },
      {
        name: 'Down To Earth Magazine (Selected Articles)',
        type: 'Monthly Magazine',
        url: 'https://www.downtoearth.org.in',
        free: true,
        howToUse: 'Read case studies on grassroots conservation, groundwater depletion, and renewable energy.'
      }
    ],
    highYieldTopics: [
      'COP decisions on Loss & Damage Fund and Carbon Markets',
      'Renewable Energy targets (500 GW by 2030, Green Hydrogen Mission)',
      'New Ramsar wetland additions and endemic wildlife reserves',
      'Forest Rights Act and compensatory afforestation (CAMPA)'
    ]
  },
  {
    id: 'ca-polity-ir',
    title: 'Polity, Governance & International Relations (GS-2)',
    gsPaper: 'GS-2',
    description: 'Landmark Supreme Court rulings, Constitutional bills, Center-State issues, bilateral summits, and multilateral organizations.',
    keySources: [
      {
        name: 'PRS Legislative Research',
        type: 'Official Portal',
        url: 'https://prsindia.org',
        free: true,
        howToUse: 'Download 2-page Bill summaries whenever Parliament is in session.'
      },
      {
        name: 'Sansad TV Perspective',
        type: 'Analysis Video',
        url: 'https://www.youtube.com/@SansadTV',
        free: true,
        howToUse: 'Watch 25-minute expert panel discussions on foreign policy and international groupings.'
      },
      {
        name: 'Ministry of External Affairs (MEA) Briefings',
        type: 'Official Portal',
        url: 'https://mea.gov.in',
        free: true,
        howToUse: 'Refer for official joint statements during Prime Minister foreign visits.'
      }
    ],
    highYieldTopics: [
      'Governor powers and federal dispute cases in Supreme Court',
      'Electoral reforms, Simultaneous Elections (One Nation One Election)',
      'India-Middle East-Europe Economic Corridor (IMEC) & Quad / BRICS expansion',
      'Free Speech, Defamation, and Digital Personal Data Protection Act'
    ]
  },
  {
    id: 'ca-scitech',
    title: 'Science, Technology & Space (GS-3)',
    gsPaper: 'GS-3',
    description: 'ISRO space missions, Artificial Intelligence governance, biotechnology, quantum computing, and defense acquisitions.',
    keySources: [
      {
        name: 'ISRO Official Portal & Missions Track',
        type: 'Official Portal',
        url: 'https://www.isro.gov.in',
        free: true,
        howToUse: 'Note payload details, orbit type (LEO/GEO/SSO), and objectives of major missions (Gaganyaan, Aditya-L1).'
      },
      {
        name: 'The Hindu Science Column (Every Sunday)',
        type: 'Daily Newspaper',
        url: 'https://www.thehindu.com/sci-tech/science/',
        free: true,
        howToUse: 'Crisp 1-paragraph summaries on CRISPR, mRNA vaccines, CAR-T cell therapy, and quantum tech.'
      }
    ],
    highYieldTopics: [
      'Gaganyaan human spaceflight mission architecture',
      'Generative AI ethics, Deepfakes regulation, and National AI Mission',
      'National Quantum Mission and Supercomputing initiatives',
      'CAR-T cell therapy, Gene Editing, and Sickle Cell Anaemia eradication'
    ]
  }
];
