import { PYQItem } from '../lib/types';

export const PYQ_ITEMS: PYQItem[] = [
  // ================= POLITY PYQS =================
  {
    id: 'pyq-pol-2023-1',
    type: 'Prelims',
    year: 2023,
    paper: 'GS-1',
    subject: 'Indian Polity',
    topic: 'Due Process of Law & Article 21',
    question: 'In essence, what does "Due Process of Law" mean?',
    options: [
      'The principle of natural justice',
      'The procedure established by law',
      'Fair application of law',
      'Equality before law'
    ],
    correctAnswer: 'Fair application of law',
    explanation: '"Due process of law" examines not only whether a law was enacted under proper legislative procedure, but also whether the law itself is just, fair, and reasonable (substantive due process). Post-Maneka Gandhi (1978), the Supreme Court integrated Due Process into Article 21.',
    seniorApproachTip: 'Notice the difference between "Procedure Established by Law" (formal compliance) and "Due Process of Law" (fairness of both procedure and substantive content). Class 11 NCERT Chapter 2 touches on this exact philosophical distinction.',
    relatedSubjectPath: '/roadmaps/polity',
    relatedResourceId: 'res-ncert-polity-strategy'
  },
  {
    id: 'pyq-pol-2022-1',
    type: 'Prelims',
    year: 2022,
    paper: 'GS-1',
    subject: 'Indian Polity',
    topic: 'Anti-Defection Law (10th Schedule)',
    question: 'With reference to the anti-defection law in India, consider the following statements:\n1. The law specifies that a nominated legislator cannot join any political party within six months of being appointed to the House.\n2. The law does not provide any time-frame within which the presiding officer has to decide a defection case.\nWhich of the statements given above is/are correct?',
    options: [
      '1 only',
      '2 only',
      'Both 1 and 2',
      'Neither 1 nor 2'
    ],
    correctAnswer: '2 only',
    explanation: 'Statement 1 is incorrect because a nominated member can join a political party within 6 months, but is disqualified if they join AFTER 6 months. Statement 2 is correct because the 10th Schedule does not specify a mandatory timeline for the Speaker/Chairman to adjudicate defection petitions.',
    seniorApproachTip: 'Laxmikanth chapter on Anti-Defection has this exact rule about Nominated members vs Independent members. Independent members can NEVER join a party, while nominated members get a 6-month grace window.',
    relatedSubjectPath: '/roadmaps/polity',
    relatedResourceId: 'res-laxmikanth-master'
  },
  {
    id: 'pyq-pol-2021-1',
    type: 'Prelims',
    year: 2021,
    paper: 'GS-1',
    subject: 'Indian Polity',
    topic: 'Constitutional Government Definition',
    question: 'A constitutional government by definition is a:',
    options: [
      'Government by popular representative',
      'Multi-party government',
      'Limited government',
      'Government by the legislature'
    ],
    correctAnswer: 'Limited government',
    explanation: 'The core essence of Constitutionalism is "Limited Government"—imposing legal and constitutional restraints on the exercise of arbitrary state power to safeguard individual liberties.',
    seniorApproachTip: 'UPSC asked this exact conceptual question in 2014, 2020, and 2021! Constitutionalism = Checks & Balances + Fundamental Rights = Limited Government.',
    relatedSubjectPath: '/roadmaps/polity',
    relatedResourceId: 'res-ncert-polity-strategy'
  },

  // ================= HISTORY PYQS =================
  {
    id: 'pyq-hist-2022-1',
    type: 'Prelims',
    year: 2022,
    paper: 'GS-1',
    subject: 'History',
    topic: 'Ancient India - Terms',
    question: 'With reference to Indian history, consider the following pairs of historical terms and their meanings:\n1. Aryasatyas — 4 Noble Truths of Buddhism\n2. Sarthavaha — Leader of merchant caravan\n3. Ur — Village assembly in Chola empire\nHow many pairs given above are correctly matched?',
    options: [
      'Only one pair',
      'Only two pairs',
      'All three pairs',
      'None of the pairs'
    ],
    correctAnswer: 'All three pairs',
    explanation: 'Aryasatyas are the 4 Noble Truths taught by Buddha. Sarthavaha refers to the leader of traveling merchant caravans in ancient and Gupta trade networks. Ur was the general village assembly of non-Brahmadeya settlements in the Chola Kingdom (explained in Class 7 NCERT).',
    seniorApproachTip: 'Ancient administrative terms come directly from NCERT sideboxes. Class 6 Chapter 8 and Class 7 Chapter 2 explicitly cover Ur, Sabha, and Sarthavaha.',
    relatedSubjectPath: '/roadmaps/history',
    relatedResourceId: 'res-ncert-history-mega'
  },
  {
    id: 'pyq-hist-2021-1',
    type: 'Prelims',
    year: 2021,
    paper: 'GS-1',
    subject: 'History',
    topic: 'Modern History - 1919 Montford Reforms',
    question: 'In the Government of India Act 1919, the functions of Provincial Government were divided into "Reserved" and "Transferred" subjects. Which of the following were treated as Reserved subjects?\n1. Administration of Justice\n2. Local Self-Government\n3. Land Revenue\n4. Police\nSelect the correct answer using the code given below:',
    options: [
      '1, 2 and 3',
      '2, 3 and 4',
      '1, 3 and 4',
      '1, 2 and 4'
    ],
    correctAnswer: '1, 3 and 4',
    explanation: 'Under Dyarchy (GoI Act 1919), vital control departments like Police, Land Revenue, and Administration of Justice were kept as "Reserved" with the British Governor and his Executive Council. Transferred subjects given to Indian Ministers included Local Self-Government, Health, and Education.',
    seniorApproachTip: 'Remember the British logic: Any department involving coercion or money (Police, Justice, Revenue, Finance) was Reserved; service departments with low budgets (Education, Local self govt) were Transferred.',
    relatedSubjectPath: '/roadmaps/history',
    relatedResourceId: 'res-spectrum-modern'
  },

  // ================= GEOGRAPHY PYQS =================
  {
    id: 'pyq-geo-2023-1',
    type: 'Prelims',
    year: 2023,
    paper: 'GS-1',
    subject: 'Geography',
    topic: 'Seismology & Earth Interior',
    question: 'Consider the following statements regarding Earthquake waves:\n1. P-waves are longitudinal waves that can travel through solids, liquids, and gases.\n2. S-waves are transverse waves that can only travel through solid materials.\n3. The shadow zone of P-waves is larger than that of S-waves.\nHow many of the statements given above are correct?',
    options: [
      'Only one',
      'Only two',
      'All three',
      'None'
    ],
    correctAnswer: 'Only two',
    explanation: 'Statements 1 and 2 are correct. Statement 3 is incorrect because the shadow zone of S-waves (beyond 105° all the way to 105° on the other side, covering over 40% of earth surface) is significantly LARGER than the P-wave shadow zone (105° to 145° ring).',
    seniorApproachTip: 'Class 11 Physical Geography Chapter 3 has a full-page diagram of P-wave vs S-wave shadow zones. S-wave shadow zone is massive because S-waves cannot pass through the liquid outer core.',
    relatedSubjectPath: '/roadmaps/geography',
    relatedResourceId: 'res-ncert-geo-mega'
  },

  // ================= ECONOMY PYQS =================
  {
    id: 'pyq-eco-2022-1',
    type: 'Prelims',
    year: 2022,
    paper: 'GS-1',
    subject: 'Economy',
    topic: 'Monetary Policy & Inflation',
    question: 'In India, which one of the following is responsible for maintaining price stability by controlling inflation?',
    options: [
      'Department of Consumer Affairs',
      'Cabinet Committee on Economic Affairs',
      'Financial Stability and Development Council',
      'Reserve Bank of India'
    ],
    correctAnswer: 'Reserve Bank of India',
    explanation: 'Under the amended RBI Act 1934 (in 2016), the Reserve Bank of India (via the Monetary Policy Committee) has the statutory mandate to maintain price stability while keeping in mind the objective of growth (target: 4% CPI +/- 2%).',
    seniorApproachTip: 'This is a straight-forward question testing basic institutional knowledge. Don’t overthink and guess complex committees when the central bank is explicitly tasked with inflation targeting.',
    relatedSubjectPath: '/roadmaps/economy',
    relatedResourceId: 'res-ncert-economy-ied'
  },

  // ================= MAINS GS QUESTIONS =================
  {
    id: 'pyq-mains-gs2-2023',
    type: 'Mains',
    year: 2023,
    paper: 'GS-2',
    subject: 'Indian Polity',
    topic: 'Constitutional Morality & Basic Structure',
    question: '“The Constitution of India is a living instrument with capabilities of enormous dynamism. It is a mechanism that provides powers of growth and expansion.” Explain in the light of landmark judicial pronouncements.',
    explanation: 'Answer Framework:\n- Introduction: Define Constitution as an organic document that evolves with society without losing foundational ethos.\n- Body 1: Expansive interpretation of Fundamental Rights (Art 21 - Maneka Gandhi, Puttaswamy privacy, Navtej Johar).\n- Body 2: Basic Structure Doctrine (Kesavananda Bharati) as a protective yet flexible evolutionary framework.\n- Body 3: Socio-economic welfare & affirmative action adjustments (EWS 103rd Amendment, Gender rights in Sabarimala).\n- Conclusion: Quote Dr. Ambedkar on the adaptability of the Constitution.',
    seniorApproachTip: 'Always structure Mains GS2 answers with 3-4 landmark Supreme Court cases and relevant constitutional article numbers.',
    relatedSubjectPath: '/roadmaps/polity',
    relatedResourceId: 'res-ncert-polity-strategy'
  }
];
