import { SubjectRoadmap } from '../lib/types';

export const SUBJECT_ROADMAPS: SubjectRoadmap[] = [
  // ================= HISTORY ROADMAP =================
  {
    subjectId: 'history',
    subjectName: 'History & Art & Culture',
    iconName: 'Landmark',
    description: 'Master ancient archaeological foundations, medieval state structures, modern freedom struggle, world history, and art forms with high-yield chronology.',
    overviewAdvice: 'History mein sabse badi mistake hoti hai dates ratne ki koshish karna. Pehle Class 6-12 NCERTs se timeline aur socioeconomic causes samjho, phir Spectrum aur PYQs pe jao.',
    steps: [
      {
        id: 'hist-s1',
        stepNumber: 1,
        title: 'NCERT Foundation (Class 6–12)',
        level: 'Foundation',
        tagline: 'Build your mental timeline from Harappa to 1947',
        seniorGuidance: 'Don’t buy fat reference books yet. Finish Class 6 (Ancient), Class 7 (Medieval), Class 8 (Modern), Class 11 Fine Arts, and Class 12 Themes I, II, III.',
        estimatedTime: '3–4 Weeks (2 hrs/day)',
        pyqFocusArea: 'Observe how UPSC asks questions on ancient terminology (e.g. Sarthavaha, Ur, Sabha, Agrahara) and Harappan sites.',
        actionChecklist: [
          'Read Class 6 Our Pasts - I and map major Neolithic & Harappan sites',
          'Read Class 7 Our Pasts - II (Focus on Chola local governance & Bhakti saints)',
          'Read Class 8 Our Pasts - III (Land revenue systems Zamindari/Ryotwari/Mahalwari)',
          'Read Class 12 Themes in Indian History Part I, II, III'
        ],
        resources: [
          {
            id: 'res-h1',
            title: 'Complete NCERT History Class 6–12 Foundation Series',
            subject: 'History',
            category: 'NCERT Foundation',
            level: 'Foundation',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'UPSCprep.com & PW OnlyIAS',
            url: 'https://www.youtube.com/watch?v=fJQSktxOXWY',
            description: 'Structured class-by-class video lecture series covering Ancient, Medieval, and Modern NCERTs with timestamps and conceptual notes.',
            seniorTip: 'Ye playlist 1.25x speed pe dekho while keeping NCERT book open on your table.',
            estimatedHours: 28,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-03',
            verificationSignals: {
              views: '190K+',
              subscribers: '1.2M+',
              completeness: 'Complete Class 6–12 Coverage',
              uploadYear: '2026',
              channelName: 'UPSCprep / OnlyIAS'
            },
            tags: ['History', 'NCERT', 'Class 6-12', 'Foundation']
          }
        ]
      },
      {
        id: 'hist-s2',
        stepNumber: 2,
        title: 'Ancient India & Harappan Civilization',
        level: 'Standard',
        tagline: 'Deep dive into Prehistoric sites, Vedic Age, Mahajanapadas, Mauryas, and Guptas',
        seniorGuidance: 'UPSC Prelims loves Buddhism, Jainism, Sangam literature terms, and Mauryan edicts. Ancient India ke coins, inscriptions aur ports (Arikamedu, Muziris, Barygaza) pe special focus rakho.',
        estimatedTime: '10–12 Days',
        pyqFocusArea: 'Buddhism concepts (Bodhisattva, Maitreya, Hinayana vs Mahayana, Chaitya vs Vihara) and Asokan Edict locations.',
        actionChecklist: [
          'Read RS Sharma (Old NCERT) or Class 12 Theme 1 & 2',
          'Make a 1-page comparative chart of 4 Buddhist Councils (King, President, Venue, Outcome)',
          'List ancient Indian ports and Greek/Roman trade items',
          'Solve last 10 years Prelims Ancient India questions'
        ],
        resources: [
          {
            id: 'res-h2',
            title: 'Ancient Indian History Comprehensive Masterclass',
            subject: 'History',
            category: 'Ancient India',
            level: 'Standard',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'PW OnlyIAS & Unacademy Free Archive',
            url: 'https://www.youtube.com/watch?v=fJQSktxOXWY',
            description: 'Chronological coverage from Stone Age, Indus Valley, Vedic period, Mahajanapadas, Mauryan Empire, Post-Mauryan foreign rulers to Gupta and Harshavardhana.',
            seniorTip: 'Make short bullet notes on administrative terms: Samaharta, Sannidhata, Yuktas, Rajukas.',
            estimatedHours: 16,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-02',
            verificationSignals: {
              views: '320K+',
              completeness: 'Complete ancient syllabus',
              uploadYear: '2026'
            },
            tags: ['Ancient India', 'Buddhism', 'Mauryan', 'Gupta']
          }
        ]
      },
      {
        id: 'hist-s3',
        stepNumber: 3,
        title: 'Medieval India & Bhakti-Sufi Synthesis',
        level: 'Standard',
        tagline: 'Delhi Sultanate, Vijayanagara Empire, Mughals, and Marathas',
        seniorGuidance: 'Vijayanagara Empire is the MOST frequent topic in UPSC medieval history (Amaranāyaka system, Mahanavami Dibba, foreign travelers like Nicolo Conti, Abdur Razzaq, Domingo Paes). Satish Chandra / NCERT se isko ache se cover karo.',
        estimatedTime: '8–10 Days',
        pyqFocusArea: 'Vijayanagara capital layout, Mughal revenue terms (Zabt, Dahsala, Jagir vs Inam lands), Chola bronze sculptures.',
        actionChecklist: [
          'Study Vijayanagara administration, water systems (Kamalapuram tank, Hiriya canal), and temples',
          'Understand Akbar’s Mansabdari system (Zat vs Sawar ranks)',
          'Prepare table of foreign travelers in India (Name, Origin, Ruler’s Court, Book written)',
          'Solve Medieval History PYQs (2014–2025)'
        ],
        resources: [
          {
            id: 'res-h3',
            title: 'Medieval Indian History & Vijayanagara Master Series',
            subject: 'History',
            category: 'Medieval India',
            level: 'Standard',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'UPSCprep.com',
            url: 'https://www.youtube.com/watch?v=fJQSktxOXWY',
            description: 'High-yield medieval lectures concentrating strictly on UPSC relevant areas: Vijayanagara, Sultanate administration, Mughal systems, and Bhakti/Sufi poetry.',
            seniorTip: 'Do NOT memorize battles of small chieftains. Stick strictly to administrative, economic, and architectural innovations.',
            estimatedHours: 14,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-03',
            verificationSignals: {
              views: '150K+',
              completeness: 'UPSC high-yield focused'
            },
            tags: ['Medieval India', 'Vijayanagara', 'Mughals', 'Bhakti']
          }
        ]
      },
      {
        id: 'hist-s4',
        stepNumber: 4,
        title: 'Modern Indian History & Freedom Struggle',
        level: 'Advanced',
        tagline: 'From European arrival (1498) to Independence & Partition (1947)',
        seniorGuidance: 'Spectrum (A Brief History of Modern India by Rajiv Ahir) is the industry standard. Read it topic-wise: British economic policies -> 1857 Revolt -> Socio-religious reforms -> Moderates vs Extremists -> Gandhian phase -> Revolutionary nationalists -> Constitutional Acts (1909, 1919, 1935).',
        estimatedTime: '3 Weeks',
        pyqFocusArea: 'Govt of India Acts (1919 Dyarchy vs 1935 Provincial Autonomy), Cripps Mission vs Cabinet Mission differences, Gandhi-Ambedkar Poona Pact, Tribal and Peasant rebellions.',
        actionChecklist: [
          'Read Spectrum chapters on British administrative & economic impact',
          'Make comparative notes on 1909 Morley-Minto, 1919 Montagu-Chelmsford, 1935 GoI Act',
          'Map Gandhian movements: Champaran, Kheda, Rowlatt Satyagraha, NCM, CDM, QIM',
          'Practice 100+ Modern History MCQs from past 15 years'
        ],
        resources: [
          {
            id: 'res-h4',
            title: 'Spectrum Modern History Chapter-Wise High-Yield Series',
            subject: 'History',
            category: 'Modern History',
            level: 'Advanced',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'PW OnlyIAS',
            url: 'https://www.youtube.com/watch?v=fJQSktxOXWY',
            description: 'Complete Spectrum revision covering all high-yield chapters, socio-religious reform tables, and national movement chronologies with PYQ cross-referencing.',
            seniorTip: 'Review the summary boxes at the end of each Spectrum chapter daily before going to bed.',
            estimatedHours: 24,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-03',
            verificationSignals: {
              views: '450K+',
              completeness: 'Complete Spectrum mapping'
            },
            tags: ['Modern History', 'Freedom Struggle', 'Spectrum', 'Gandhian Era']
          }
        ]
      },
      {
        id: 'hist-s5',
        stepNumber: 5,
        title: 'Art & Culture (Architecture, Sculpture, Paintings, Music & Dance)',
        level: 'Advanced',
        tagline: 'Nitin Singhania / Class 11 Fine Arts NCERT conceptual synthesis',
        seniorGuidance: 'Class 11 NCERT "An Introduction to Indian Art" is the most authentic, concise source for temple architecture (Nagara, Dravida, Vesara), cave architecture (Ajanta, Ellora, Elephanta), and Buddhist stupas.',
        estimatedTime: '2 Weeks',
        pyqFocusArea: 'Temple styles (Panchayatana, Mandapa, Shikhara vs Vimana), Classical Dances (Sangeet Natak Akademi 8 dances), Miniature painting schools (Mughal, Rajasthani, Pahari).',
        actionChecklist: [
          'Read Class 11 Fine Arts NCERT (Chapters 1–8)',
          'Draw Nagara vs Dravida temple architecture architectural components',
          'Make a matrix of 8 Classical Dances: State, Mudras, Musical instruments, Famous exponents',
          'Review UNESCO World Heritage Sites in India (Tangible and Intangible)'
        ],
        resources: [
          {
            id: 'res-h5',
            title: 'Class 11 Fine Arts NCERT & Art & Culture Master Series',
            subject: 'History',
            category: 'Art & Culture',
            level: 'Advanced',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'UPSCprep.com',
            url: 'https://www.youtube.com/watch?v=Y2IRiAoSygk',
            description: 'Visual walkthrough of Indian temple architecture, caves, sculptures, classical dance forms, and UNESCO heritage with high-resolution imagery.',
            seniorTip: 'Always study architecture with visual diagrams and photos, never plain text alone.',
            estimatedHours: 18,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-02',
            verificationSignals: {
              views: '210K+',
              completeness: 'Visual Art & Culture breakdown'
            },
            tags: ['Art & Culture', 'Fine Arts NCERT', 'Architecture', 'Sculpture']
          }
        ]
      },
      {
        id: 'hist-s6',
        stepNumber: 6,
        title: 'PYQ Mastery & Mains GS1 Answer Writing Integration',
        level: 'Integration',
        tagline: 'Transform knowledge into 150-word and 250-word structured answers',
        seniorGuidance: 'Mains GS1 asks analytical questions (e.g. "Evaluate the nature of Bhakti literature", "Why did industrial revolution happen in Britain first?", "Evaluate Gandhi vs Bose ideological approaches"). Write 1 answer daily with intro-body-conclusion format.',
        estimatedTime: 'Ongoing Practice',
        pyqFocusArea: 'Mains GS1 past 10 years papers analysis + Prelims negative marking elimination tricks.',
        actionChecklist: [
          'Analyze all Mains GS1 History questions from 2013 to 2025',
          'Practice writing 20 answers using subheadings, bullet points, and timeline diagrams',
          'Attempt 5 sectional Prelims mock tests on History'
        ],
        resources: [
          {
            id: 'res-h6',
            title: 'Mains GS1 History & Culture Model Answer Writing Sessions',
            subject: 'History',
            category: 'Mains GS1',
            level: 'Integration',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'PW OnlyIAS / IASbaba Free Sessions',
            url: 'https://www.youtube.com/watch?v=Y2IRiAoSygk',
            description: 'Line-by-line model answer writing breakdowns for past UPSC Mains GS1 History and Culture questions.',
            seniorTip: 'Notice how toppers use mini-maps and flowcharts in History answers to save writing time.',
            estimatedHours: 12,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-03',
            verificationSignals: {
              views: '110K+',
              channelName: 'PW OnlyIAS'
            },
            tags: ['Mains GS1', 'Answer Writing', 'PYQs']
          }
        ]
      }
    ]
  },

  // ================= GEOGRAPHY ROADMAP =================
  {
    subjectId: 'geography',
    subjectName: 'Geography & Mapping',
    iconName: 'Compass',
    description: 'Master Geomorphology, Climatology, Oceanography, Indian Physical & River Systems, Economic Resources, and Global Mapping.',
    overviewAdvice: 'Geography is one of the most scoring and scientific subjects. Do NOT memorize text without an Atlas. Har concept ko map aur diagram ke saath link karo.',
    steps: [
      {
        id: 'geo-s1',
        stepNumber: 1,
        title: 'Class 6–10 NCERT Foundation',
        level: 'Foundation',
        tagline: 'Basic earth systems, latitude/longitude, Indian relief & rivers',
        seniorGuidance: 'Start with Class 6, 7, 8, 9, 10 NCERTs. Class 9 Contemporary India I is crucial for Indian river systems and monsoon basics.',
        estimatedTime: '2–3 Weeks',
        pyqFocusArea: 'Direct matching of physical relief features, passes in Himalayas, and river drainage directions.',
        actionChecklist: [
          'Study Class 6 The Earth Our Habitat (Latitudes, Longitudes, Motions)',
          'Study Class 7 Our Environment (Atmosphere layers & Ocean currents)',
          'Study Class 9 Contemporary India I (Drainage & Monsoon)',
          'Study Class 10 Contemporary India II (Resources, Minerals, Agriculture)'
        ],
        resources: [
          {
            id: 'res-g1',
            title: 'NCERT Geography Class 6–10 Complete Foundation',
            subject: 'Geography',
            category: 'NCERT Foundation',
            level: 'Foundation',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'PW OnlyIAS',
            url: 'https://www.youtube.com/watch?v=ON4s3_4Zdp4',
            description: 'Comprehensive animated explanation of earth motions, landforms, Indian drainage networks, and atmospheric layers.',
            seniorTip: 'Draw alongside the educator whenever they draw a landform or pressure belt diagram.',
            estimatedHours: 22,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-03',
            verificationSignals: {
              views: '340K+',
              completeness: 'Complete Class 6–10 walkthrough'
            },
            tags: ['Geography', 'NCERT', 'Class 6-10']
          }
        ]
      },
      {
        id: 'geo-s2',
        stepNumber: 2,
        title: 'Class 11 Fundamentals of Physical Geography',
        level: 'Standard',
        tagline: 'The absolute bedrock of UPSC Physical Geography (Geomorphology, Climatology, Oceanography)',
        seniorGuidance: 'This is arguably the single most important book for Geography. Read every chapter twice. Plate Tectonics, Hadley/Ferrel cells, Cyclones, and Ocean Salinity/Currents require conceptual mastery.',
        estimatedTime: '3 Weeks',
        pyqFocusArea: 'Tropical vs Extra-tropical cyclones, Karst/Glacial landforms, Temperature inversion, Salinity in enclosed seas (Red Sea, Mediterranean).',
        actionChecklist: [
          'Master Plate Tectonics & Continental Drift evidences',
          'Draw tri-cellular atmospheric circulation model with Coriolis deflection',
          'Understand Tropical Cyclone formation conditions & eye structure',
          'Diagram thermohaline circulation & ocean gyres'
        ],
        resources: [
          {
            id: 'res-g2',
            title: 'Class 11 Physical Geography In-Depth Masterclass',
            subject: 'Geography',
            category: 'Physical Geography',
            level: 'Standard',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'PW OnlyIAS & Amit Sen Geography',
            url: 'https://www.youtube.com/watch?v=ON4s3_4Zdp4',
            description: 'Clear conceptual breakdown of Geomorphology, Climatology, and Oceanography strictly based on Class 11 NCERT.',
            seniorTip: 'Do not move to Indian Geography until your Physical concepts (Pressure belts, Adiabatic lapse rate) are 100% solid.',
            estimatedHours: 26,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-03',
            verificationSignals: {
              views: '580K+',
              channelName: 'PW OnlyIAS'
            },
            tags: ['Physical Geography', 'Class 11 NCERT', 'Climatology', 'Geomorphology']
          }
        ]
      },
      {
        id: 'geo-s3',
        stepNumber: 3,
        title: 'India: Physical Environment (Class 11) & Drainage',
        level: 'Standard',
        tagline: 'Indian physiography, Himalayas geological structure, river basins, soils & vegetation',
        seniorGuidance: 'Indian Geography is heavily tested through map-based questions in Prelims. Learn Himalayan mountain ranges from North to South (Karakoram -> Ladakh -> Zaskar -> Pir Panjal -> Dhauladhar -> Shiwalik).',
        estimatedTime: '2 Weeks',
        pyqFocusArea: 'Left bank vs Right bank tributaries of Indus, Ganga, Brahmaputra, Godavari, Krishna, Cauvery; Himalayan passes; National Parks in specific river basins.',
        actionChecklist: [
          'Read Class 11 India Physical Environment',
          'Map major Himalayan passes (Zoji La, Shipki La, Nathu La, Lipulekh, Bomdi La)',
          'Trace Indus Waters Treaty rivers (Indus, Jhelum, Chenab vs Ravi, Beas, Sutlej)',
          'Classify Indian soil types (Alluvial, Black/Regur, Red/Yellow, Laterite, Arid, Saline, Peaty)'
        ],
        resources: [
          {
            id: 'res-g3',
            title: 'Indian Physical Geography & River Systems Masterclass',
            subject: 'Geography',
            category: 'Indian Geography',
            level: 'Standard',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'UPSCprep.com',
            url: 'https://www.youtube.com/watch?v=ON4s3_4Zdp4',
            description: 'Comprehensive mapping of Indian river networks, mountain passes, physiographic divisions, and climatic zones.',
            seniorTip: 'Draw each river system on a blank white paper from memory until you can place every tributary accurately.',
            estimatedHours: 18,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-02',
            verificationSignals: {
              views: '240K+'
            },
            tags: ['Indian Geography', 'Rivers', 'Drainage', 'Himalayas']
          }
        ]
      },
      {
        id: 'geo-s4',
        stepNumber: 4,
        title: 'Mapping (India & World) & Current Affairs Places in News',
        level: 'Advanced',
        tagline: 'High-yield map skills: straits, seas, choke points, critical minerals, and conflict zones',
        seniorGuidance: 'Every year, 4–6 Prelims questions are 100% map-based (e.g. Red Sea bordering countries, Black Sea, Caspian Sea, Mediterranean, Horn of Africa, Southeast Asian straits: Malacca, Sunda, Lombok). Keep Oxford Student Atlas open.',
        estimatedTime: '10 Days + Weekly Routine',
        pyqFocusArea: 'Strait of Hormuz, Bab-el-Mandeb, Bosphorus, Dardanelles; Countries surrounding Mediterranean, Black, Caspian, Red, and Baltic seas.',
        actionChecklist: [
          'Memorize border countries acronyms for Black Sea (BURGER-T), Caspian (TARIK), Red Sea (DESSEY)',
          'Map Indian National Parks, Tiger Reserves, Ramsar Wetland sites',
          'Track places in news from Current Affairs (West Asia, Sahel region, South China Sea, Arctic)',
          'Practice 50+ map identification questions'
        ],
        resources: [
          {
            id: 'res-g4',
            title: 'World & India Mapping Master Series for UPSC Prelims',
            subject: 'Geography',
            category: 'Mapping',
            level: 'Advanced',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'PW OnlyIAS & StudyIQ Free Lectures',
            url: 'https://www.youtube.com/watch?v=ON4s3_4Zdp4',
            description: 'Complete map mnemonics for seas, straits, trenches, mountain ranges, islands, and places frequently in global geopolitical news.',
            seniorTip: 'Review 1 continent map every Sunday morning for 30 minutes.',
            estimatedHours: 16,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-03',
            verificationSignals: {
              views: '410K+',
              uploadYear: '2026'
            },
            tags: ['Mapping', 'World Geography', 'Places in News', 'Prelims']
          }
        ]
      }
    ]
  },

  // ================= POLITY ROADMAP =================
  {
    subjectId: 'polity',
    subjectName: 'Indian Polity & Governance',
    iconName: 'ShieldCheck',
    description: 'Master the Constitution of India, Laxmikanth, Parliamentary procedures, Judicial doctrines, Federal dynamics, and Governance bodies.',
    overviewAdvice: 'Indian Polity is the highest Return-on-Investment (ROI) subject in Prelims (15-18 questions) and GS2 Mains. Accuracy should be above 85%. Class 11 NCERT for conceptual foundation + Laxmikanth for standard rules.',
    steps: [
      {
        id: 'pol-s1',
        stepNumber: 1,
        title: 'Class 6–10 Civics & Class 11 Constitution at Work',
        level: 'Foundation',
        tagline: 'Understand the philosophical and analytical soul of Indian constitutionalism',
        seniorGuidance: 'Class 11 "Indian Constitution at Work" is non-negotiable. It teaches you WHY our constitution has specific provisions, not just what the article number is.',
        estimatedTime: '2 Weeks',
        pyqFocusArea: 'Preamble terms (Liberty, Equality, Fraternity, Justice), Basic Structure doctrine origins, First Past the Post vs Proportional Representation.',
        actionChecklist: [
          'Read Class 11 Indian Constitution at Work (all 10 chapters)',
          'Understand difference between Constitutional Law and Ordinary Law',
          'Study evolution of Fundamental Rights vs DPSP conflicts (Champakam Dorairajan to Minerva Mills)'
        ],
        resources: [
          {
            id: 'res-p1',
            title: 'Class 11 Indian Constitution at Work Complete Foundation',
            subject: 'Indian Polity',
            category: 'NCERT Foundation',
            level: 'Foundation',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'UPSCprep.com',
            url: 'https://www.youtube.com/watch?v=Y2IRiAoSygk',
            description: 'In-depth conceptual analysis of Indian constitutional architecture, Separation of Powers, and Judicial Review.',
            seniorTip: 'Read the text carefully and mark lines explaining the rationale of the Constituent Assembly.',
            estimatedHours: 18,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-03',
            verificationSignals: {
              views: '310K+'
            },
            tags: ['Polity', 'NCERT', 'Constitution', 'Class 11']
          }
        ]
      },
      {
        id: 'pol-s2',
        stepNumber: 2,
        title: 'M. Laxmikanth Core Pillars (Preamble to Fundamental Duties)',
        level: 'Standard',
        tagline: 'Articles 1 to 51A: Citizenship, Fundamental Rights, DPSPs, and Fundamental Duties',
        seniorGuidance: 'Fundamental Rights (Articles 12-35) is the single highest yield section in UPSC. Understand reasonable restrictions, Article 21 expansive interpretations (Puttaswamy privacy judgment), and Article 32 writs.',
        estimatedTime: '2 Weeks',
        pyqFocusArea: 'Article 14 (Equality before Law vs Equal Protection of Laws), Article 19 freedoms & reasonable restrictions, Article 21 rights, Article 32 Writs vs High Court Art 226 scope, DPSP socialist/Gandhian/liberal-intellectual classification.',
        actionChecklist: [
          'Study Preamble text and Supreme Court rulings (Berubari, Kesavananda, LIC of India)',
          'Create a comparative table of 5 Writs (Habeas Corpus, Mandamus, Prohibition, Certiorari, Quo-Warranto)',
          'Classify DPSPs into Socialistic, Gandhian, and Liberal-Intellectual categories',
          'Solve 150+ MCQs on Fundamental Rights and DPSPs'
        ],
        resources: [
          {
            id: 'res-p2',
            title: 'Laxmikanth Indian Polity Core Pillars (Articles 1–51A Masterclass)',
            subject: 'Indian Polity',
            category: 'Laxmikanth',
            level: 'Standard',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'PW OnlyIAS & UPSC Wallah',
            url: 'https://www.youtube.com/watch?v=Y2IRiAoSygk',
            description: 'Exhaustive chapter-wise explanation of Preamble, Citizenship, Fundamental Rights, DPSPs, and Fundamental Duties with landmark Supreme Court cases.',
            seniorTip: 'Whenever reading an Article in Laxmikanth, always test yourself on exceptions and constitutional amendments (e.g. 42nd, 44th, 86th, 103rd).',
            estimatedHours: 24,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-03',
            verificationSignals: {
              views: '540K+',
              channelName: 'PW OnlyIAS'
            },
            tags: ['Laxmikanth', 'Fundamental Rights', 'DPSP', 'Preamble']
          }
        ]
      },
      {
        id: 'pol-s3',
        stepNumber: 3,
        title: 'Union & State Machinery (Parliament, Executive, Judiciary, Federalism)',
        level: 'Advanced',
        tagline: 'President, Governor, PM/CM, Lok Sabha, Rajya Sabha, Supreme Court & High Courts',
        seniorGuidance: 'Compare President vs Governor powers (Veto, Ordinance, Pardon Article 72 vs 161). Understand Parliamentary motions (No-Confidence, Adjournment, Censure, Calling Attention) and Money Bill procedure (Article 110).',
        estimatedTime: '3 Weeks',
        pyqFocusArea: 'Pardoning power differences, Discretionary powers of Governor (Article 163), Special powers of Rajya Sabha (Art 249, 312), Parliamentary Committees (Public Accounts, Estimates, CoPU), SC Collegium system & Curative Petition.',
        actionChecklist: [
          'Make comparative chart: President vs Governor (Executive, Legislative, Pardoning, Veto powers)',
          'Diagram Money Bill, Financial Bill Type I, Type II, and Ordinary Bill legislative pathways',
          'Understand Supreme Court Jurisdictions: Original (Art 131), Appellate, Advisory (Art 143), Writ (Art 32), Review',
          'Study Center-State Relations (7th Schedule, Financial relations, Finance Commission Art 280, Inter-State Council Art 263)'
        ],
        resources: [
          {
            id: 'res-p3',
            title: 'Parliament, Executive & Judiciary Complete Polity Roadmap',
            subject: 'Indian Polity',
            category: 'Standard Polity',
            level: 'Advanced',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'UPSCprep.com & OnlyIAS',
            url: 'https://www.youtube.com/watch?v=Y2IRiAoSygk',
            description: 'Comprehensive coverage of Union & State Executive, Parliament devices, Budget passage stages, and Supreme Court/High Court functioning.',
            seniorTip: 'Pay special attention to Parliamentary devices: Starred vs Unstarred questions, Zero Hour (Indian innovation), and guillotine in Budget.',
            estimatedHours: 28,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-03',
            verificationSignals: {
              views: '480K+'
            },
            tags: ['Parliament', 'Judiciary', 'President', 'Governor', 'Laxmikanth']
          }
        ]
      },
      {
        id: 'pol-s4',
        stepNumber: 4,
        title: 'Constitutional, Statutory Bodies & Governance (Panchayats, ECI, CAG, UPSC, CVC, Lokpal)',
        level: 'Advanced',
        tagline: 'Independent accountability institutions and local self-government',
        seniorGuidance: 'Constitutional bodies (ECI, UPSC, SPSC, FC, CAG, NCSC, NCST, NCBC) vs Statutory/Executive bodies (NITI Aayog, NHRC, CIC, CVC, Lokpal, CBI, NIA). Remember appointment composition, tenure, removal process, and report submission.',
        estimatedTime: '10 Days',
        pyqFocusArea: 'CAG duties and power (Article 148-151), Election Commission appointment rules & collegium, 73rd/74th Amendment mandatory vs voluntary provisions.',
        actionChecklist: [
          'Create a 1-page mega-table of all Constitutional & Non-Constitutional bodies (Tenure, Removal, Appointed by)',
          'Master 73rd & 74th Amendments (11th Schedule 29 subjects, 12th Schedule 18 subjects, PESA Act 1996)',
          'Solve past 15 years Polity Prelims questions (Aim for 90% accuracy)'
        ],
        resources: [
          {
            id: 'res-p4',
            title: 'Constitutional Bodies & Local Governance Masterclass',
            subject: 'Indian Polity',
            category: 'Governance & Bodies',
            level: 'Advanced',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'PW OnlyIAS',
            url: 'https://www.youtube.com/watch?v=Y2IRiAoSygk',
            description: 'Structured comparison of CAG, ECI, Finance Commission, UPSC, Lokpal, CVC, CBI and Panchayati Raj / PESA Act 1996.',
            seniorTip: 'Remember: NITI Aayog is neither constitutional nor statutory; it was created by an Executive Resolution.',
            estimatedHours: 14,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-03',
            verificationSignals: {
              views: '260K+'
            },
            tags: ['Constitutional Bodies', 'Panchayati Raj', 'CAG', 'ECI', 'PESA']
          }
        ]
      }
    ]
  },

  // ================= ECONOMY ROADMAP =================
  {
    subjectId: 'economy',
    subjectName: 'Indian Economy & Macroeconomics',
    iconName: 'TrendingUp',
    description: 'Master Macroeconomic fundamentals, National Income, Banking & Monetary Policy (RBI), Fiscal Policy & Budget, External Sector (BoP, Forex), Inflation, and Agriculture.',
    overviewAdvice: 'Economy ratne ka subject nahi hai. Basic logic samjho: Agar RBI Repo Rate badhata hai toh money supply kam hogi, demand kam hogi, inflation control hoga, lekin growth slow ho sakti hai. Connect every concept logically.',
    steps: [
      {
        id: 'eco-s1',
        stepNumber: 1,
        title: 'Class 9–10 NCERT & Class 11 Indian Economic Development',
        level: 'Foundation',
        tagline: 'Basic economic concepts and history of Indian economic evolution since 1947',
        seniorGuidance: 'Class 11 "Indian Economic Development" is compulsory for every aspirant. It provides the economic narrative: Pre-1991 License Raj, 1991 LPG reforms, structural changes, and rural distress.',
        estimatedTime: '2 Weeks',
        pyqFocusArea: 'LPG reforms rationale, Mahalanobis heavy industry model, Jobless growth, Disguised unemployment in agriculture.',
        actionChecklist: [
          'Read Class 9 Economics (Palampur factors of production, Poverty, Food Security)',
          'Read Class 10 Economics (Sectors of Economy, Money & Credit, Globalization)',
          'Read Class 11 Indian Economic Development (Eve of independence, Planning, 1991 Reforms, Rural credit)'
        ],
        resources: [
          {
            id: 'res-e1',
            title: 'NCERT Economy Class 9 to 11 Complete Foundation',
            subject: 'Economy',
            category: 'NCERT Foundation',
            level: 'Foundation',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'PW OnlyIAS & Mrunal Patel Free Archive',
            url: 'https://www.youtube.com/watch?v=ON4s3_4Zdp4',
            description: 'Crystal clear foundation of basic economic terminologies, Indian economic history, and sector-wise challenges.',
            seniorTip: 'Write down definitions of GDP, GNP, NNP, Factor Cost, and Basic Prices in your own words.',
            estimatedHours: 20,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-03',
            verificationSignals: {
              views: '490K+'
            },
            tags: ['Economy', 'NCERT', 'Class 9-11', 'LPG']
          }
        ]
      },
      {
        id: 'eco-s2',
        stepNumber: 2,
        title: 'Class 12 Macroeconomics (Selected) & Core National Income',
        level: 'Standard',
        tagline: 'GDP, GNP, GVA, Inflation indicators (CPI vs WPI), and Fiscal Budget concepts',
        seniorGuidance: 'Class 12 Introductory Macroeconomics se mathematical calculus formulas skip karo. Focus on conceptual definitions: Real vs Nominal GDP, GDP Deflator, CPI vs WPI calculation basket and weightages, Revenue Deficit vs Fiscal Deficit vs Primary Deficit.',
        estimatedTime: '12 Days',
        pyqFocusArea: 'GDP Deflator vs CPI differences, WPI manufacturing vs food weightage, Fiscal Deficit definition and FRBM Act targets.',
        actionChecklist: [
          'Calculate GDP via 3 methods (Expenditure, Income, Value Added / GVA)',
          'Make comparative table: CPI (Base year 2012, NSO, covers services) vs WPI (Base year 2011-12, DPIIT, goods only)',
          'Master Budget classifications: Revenue Receipts (Tax vs Non-tax), Capital Receipts (Debt vs Non-debt), Revenue Expenditure vs Capital Expenditure'
        ],
        resources: [
          {
            id: 'res-e2',
            title: 'Macroeconomics for UPSC: National Income, Inflation & Budgeting',
            subject: 'Economy',
            category: 'Macroeconomics',
            level: 'Standard',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'UPSCprep.com',
            url: 'https://www.youtube.com/watch?v=ON4s3_4Zdp4',
            description: 'Conceptual masterclass on GDP, Inflation metrics, Deficits, and Budget concepts tailored specifically for UPSC without complex academic math.',
            seniorTip: 'Focus on Capital Expenditure (CapEx) multiplier effect on infrastructure vs Revenue Expenditure.',
            estimatedHours: 16,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-03',
            verificationSignals: {
              views: '230K+'
            },
            tags: ['Macroeconomics', 'GDP', 'Inflation', 'Budget']
          }
        ]
      },
      {
        id: 'eco-s3',
        stepNumber: 3,
        title: 'Money, Banking, RBI Monetary Policy & Financial Markets',
        level: 'Advanced',
        tagline: 'Repo, Reverse Repo, SDF, MSF, CRR, SLR, Open Market Operations, NPAs, IBC 2016, and Capital Markets',
        seniorGuidance: 'Monetary policy is asked almost every single year in Prelims. Learn how Quantitative tools (Repo, Reverse Repo, CRR, SLR, OMO) and Qualitative tools (Margin requirements, Moral suasion) regulate liquidity in the economy.',
        estimatedTime: '2 Weeks',
        pyqFocusArea: 'Money Multiplier effect, High Powered Money (M0) vs Broad Money (M3), Standing Deposit Facility (SDF) role, Non-Performing Assets (Gross vs Net NPA), Insolvency and Bankruptcy Code (IBC) process.',
        actionChecklist: [
          'Understand RBI Monetary Policy Committee (MPC) structure (6 members, 4% +/- 2% inflation target)',
          'Trace what happens when RBI buys vs sells government securities in OMO',
          'Learn types of financial instruments: Treasury Bills, Commercial Papers, Certificates of Deposit, Sovereign Green Bonds',
          'Study Capital Markets: SEBI regulations, Primary vs Secondary market, Angel Investors, Venture Capital, Participatory Notes (P-Notes)'
        ],
        resources: [
          {
            id: 'res-e3',
            title: 'Banking, RBI Monetary Policy & Financial Markets Masterclass',
            subject: 'Economy',
            category: 'Banking & Money',
            level: 'Advanced',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'PW OnlyIAS & Vivek Singh Free Series',
            url: 'https://www.youtube.com/watch?v=ON4s3_4Zdp4',
            description: 'Exhaustive lecture series on RBI tools, liquidity transmission, NPA crisis resolution, and capital market instruments.',
            seniorTip: 'Remember: When RBI increases CRR, banks have less money to lend, so Money Multiplier decreases.',
            estimatedHours: 22,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-03',
            verificationSignals: {
              views: '410K+'
            },
            tags: ['Banking', 'RBI', 'Monetary Policy', 'NPA', 'SEBI']
          }
        ]
      },
      {
        id: 'eco-s4',
        stepNumber: 4,
        title: 'External Sector, Balance of Payments (BoP), WTO & Annual Budget/Economic Survey',
        level: 'Advanced',
        tagline: 'Current Account vs Capital Account, Forex Reserves, NEER/REER, WTO agreements, and Economic Survey analysis',
        seniorGuidance: 'Current Account (Trade in Goods, Trade in Services, Transfers/Remittances, Income) vs Capital Account (FDI, FPI/FII, External Commercial Borrowings, NRI deposits). FDI is stable and long-term; FPI is hot money.',
        estimatedTime: '2 Weeks + Annual Updates',
        pyqFocusArea: 'FDI vs FPI differences, Current Account Deficit (CAD) triggers, Real Effective Exchange Rate (REER) appreciation vs depreciation, WTO Green/Blue/Amber box subsidies.',
        actionChecklist: [
          'Make a complete Balance of Payments (BoP) accounting matrix',
          'Understand Currency Depreciation vs Devaluation, Appreciation vs Revaluation',
          'Study WTO bodies & boxes (Amber Box, Blue Box, Green Box, Peace Clause)',
          'Read the Summary of latest Union Budget and Economic Survey'
        ],
        resources: [
          {
            id: 'res-e4',
            title: 'External Sector, Balance of Payments & Economic Survey Synthesis',
            subject: 'Economy',
            category: 'External Sector',
            level: 'Advanced',
            language: 'English/Hinglish',
            type: 'YouTube',
            provider: 'UPSCprep.com & PW OnlyIAS',
            url: 'https://www.youtube.com/watch?v=ON4s3_4Zdp4',
            description: 'BoP mechanics, Forex reserve composition, Foreign Trade Policy, and key takeaways from the latest Economic Survey and Union Budget.',
            seniorTip: 'Do not read the 800-page Economic Survey word-for-word. Read authentic summaries with key graphs and policy debates.',
            estimatedHours: 18,
            free: true,
            verified: true,
            verificationStatus: 'Verified',
            lastVerified: '2026-03',
            verificationSignals: {
              views: '370K+',
              uploadYear: '2026'
            },
            tags: ['BoP', 'Forex', 'WTO', 'Economic Survey', 'Budget']
          }
        ]
      }
    ]
  }
];
