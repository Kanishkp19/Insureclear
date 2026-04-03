// === POLICY TREE DATA ===
export const TREE_DATA = [
  {
    id: 'root',
    label: 'Standard Commercial Liability',
    type: 'folder',
    defaultExpanded: true,
    children: [
      {
        id: 'section1',
        label: 'Section I - Coverages',
        type: 'folder',
        defaultExpanded: true,
        children: [
          {
            id: 'covA',
            label: 'Coverage A - Bodily Injury',
            type: 'folder',
            defaultExpanded: true,
            children: [
              {
                id: 'excl1',
                label: '2. Exclusions: Expected or Intended Injury',
                type: 'file',
                defaultExpanded: false,
              },
              {
                id: 'excl2',
                label: '3. Exclusions: Contractual Liability',
                type: 'file',
                defaultExpanded: false,
              },
            ],
          },
          {
            id: 'covB',
            label: 'Coverage B - Personal Injury',
            type: 'folder',
            defaultExpanded: false,
            children: [],
          },
        ],
      },
      {
        id: 'section2',
        label: 'Section II - Who Is An Insured',
        type: 'folder',
        defaultExpanded: false,
        children: [],
      },
      {
        id: 'section3',
        label: 'Section III - Limits of Insurance',
        type: 'folder',
        defaultExpanded: false,
        children: [],
      },
    ],
  },
]
