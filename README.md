# অতঃকিম (Otohkim) companion website

Live at **https://otohkim.github.io**. One short page per question that viewers ask on the
YouTube channel [অতঃকিম](https://www.youtube.com/@otohkim), in Bengali, with official sources and the date
the facts were checked.

## How it works

- `content/topics/*.md`: one file per topic (YAML front matter + Markdown).
- `content/tags.yml`: the tag list (Bengali name, English web slug, one-line description).
- `content/graphics/*.svg`: hand-made diagrams used by topics.
- `tools/build.py`: turns the content into the site in `_site/` (pages, tag pages, search index, sitemap).
  It also refuses to build if an em dash slips into the text.
- `.github/workflows/pages.yml`: on every push to `main`, GitHub builds and publishes the site.
- Git history keeps every old version: each topic page links to its own history, so you can see what a rule
  was on any date.

## Adding a topic

Tell Claude the topic. Claude researches it on official sites, writes `content/topics/<slug>.md`,
sets `checked:` to today, previews it, and pushes. The page appears at `https://otohkim.github.io/<slug>/`
about a minute later.

Front matter fields:

| Field | Meaning |
|---|---|
| `title` | Page heading (Bengali) |
| `short_title` | Optional shorter name for the breadcrumb |
| `slug` | Web address, short English words with hyphens |
| `summary` | One or two lines, shown in cards and search |
| `checked` | Date the facts were checked (YYYY-MM-DD); shown as "তথ্য যাচাই" |
| `tags` | From `content/tags.yml` |
| `keywords` | Hidden search words in Bengali, English and Banglish |
| `video` | Optional `url` and `title` of the related video or Short |
| `sources` | Official sources: `title`, `url`, optional `note` |
| `image` | Optional share image for WhatsApp/Facebook previews |

Graphic blocks in the body start with `@@<kind>` and end with `@@`:

- `@@img`: an image from `assets/img/` (`src`, `alt`, `caption`, `full`)
- `@@svg`: a diagram from `content/graphics/` (`file`, `caption`)
- `@@compare`: two side-by-side cards (`left`/`right` with `title`, `sub`, `color`, `items`)
- `@@bars`: a sketchy bar chart (`items` with `label`, `value`, optional `extra`)
- `@@pie`: a pie chart (`items` with `label`, `value`)
- `@@map`: India map on the official Survey of India boundary (`fills`, `points`, `legend`, `caption`)
- `@@note`: a highlighted tip or warning (`kind`: tip, warn or info; `label`; `text`)

See `content/topics/english-teacher-routes.md` for a full example.

## Style rules

- Bengali digits ০-৯ are always drawn with Noto Sans Bengali (`assets/fonts/noto-bengali-digits.woff2`,
  `unicode-range: U+09E6-09EF`, first in every font stack). Hind Siliguri and Atma draw ১ badly.
- Colours: teal #2FB3A3, coral #E8705F, yellow #F4B740, ink #22303A on warm paper.
- Fonts: Hind Siliguri (body), Galada and Atma (headings), all self-hosted (SIL Open Font License).
- Maps use only the Survey of India boundary from Datameet (`tools/make_india_paths.py`).
- Images: our own graphics or royalty-free images with credits. No em dashes.

## Build locally

```
pip install markdown pyyaml
python3 tools/build.py            # or --preview for links that work from plain files
```

Credits: sketch style by [rough.js](https://roughjs.com) (MIT). Fonts from Google Fonts via Fontsource (OFL).
