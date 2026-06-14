export interface NoteMock {
  id: string;
  tags: string[];
  createdAt: number;
  updatedAt: number;
  content: string;
}

const day = 86_400_000;
const now = Date.now();
const ago = (ms: number) => now - ms;

export const mockNotes: NoteMock[] = [
  {
    id: "n1",
    tags: ["draft", "journal"],
    createdAt: ago(2 * 60 * 60 * 1000),
    updatedAt: ago(2 * 60 * 60 * 1000),
    content: `# Morning Pages

Three pages, longhand, first thing - before the inbox, before the news, before the day has an opinion about who I should be.

## What it's for

It isn't writing, exactly. It's **clearing the channel**. Whatever is loud gets put on the page so the quieter things can be heard.

> The page asks for nothing back. That's the whole trick.

A few rules I keep:

- Don't stop moving the pen
- Boring is allowed, even encouraged
- Nobody reads this, especially not me

## Today

Slept badly, woke up with a knot about the Q3 review. Wrote it out and it shrank to a single sentence: I'm afraid the work won't speak for itself. It will. It usually does.`,
  },
  {
    id: "n2",
    tags: ["log", "work"],
    createdAt: ago(5 * 60 * 60 * 1000),
    updatedAt: ago(5 * 60 * 60 * 1000),
    content: `# Standup notes

Quick log so I stop holding it all in my head.

### Yesterday

- Shipped the tag filter behind a flag
- Paired with Ana on the export bug

### Today

- [x] Write up the rollout plan
- [ ] Review Sam's PR
- [ ] Draft the changelog entry`,
  },
  {
    id: "n3",
    tags: ["research"],
    createdAt: ago(day - 3 * 60 * 60 * 1000),
    updatedAt: ago(day - 3 * 60 * 60 * 1000),
    content: `# Reading list

Things to get through this quarter. Pasted straight from my notes app - markdown just works.

| Title | Author | Why |
| --- | --- | --- |
| The Craftsman | Sennett | Making as thinking |
| Several Short Sentences | Klinkenborg | Prose at the sentence level |
| A Pattern Language | Alexander | Structure that feels alive |

## Notes so far

Klinkenborg keeps insisting that the sentence is the unit of composition, not the paragraph. Slows me down in a good way.`,
  },
  {
    id: "n4",
    tags: ["draft", "ideas"],
    createdAt: ago(day - 60 * 60 * 1000),
    updatedAt: ago(day - 60 * 60 * 1000),
    content: `# Trip planning - coast, late September

Rough shape of the week. Nothing booked yet.

1. Fly in Friday night, stay near the harbor
2. Two slow days walking the cliffs
3. Drive north for the last three

## Packing, the short version

- Rain shell
- The good notebook
- Fewer books than I think I need`,
  },
  {
    id: "n5",
    tags: ["ideas"],
    createdAt: ago(6 * day),
    updatedAt: ago(6 * day),
    content: `# Book ideas

A place to park the ones that keep coming back.

- A quiet novel where nothing happens twice
- Field guide to ordinary weather
- Essays on tools that disappear when they work`,
  },
  {
    id: "n6",
    tags: ["log"],
    createdAt: ago(9 * day),
    updatedAt: ago(9 * day),
    content: `# Recipes - weeknight rotation

The five that never fail.

### Lemon orzo

Toast the orzo first. Don't skip it. Finish with far more lemon than feels reasonable.

### Sheet-pan everything

1. Heat the oven hot
2. One protein, two vegetables, one fat
3. Don't crowd the pan`,
  },
];
