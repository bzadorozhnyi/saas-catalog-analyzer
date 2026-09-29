#let data = json("data.json")

#let ink = rgb("#1b1f3b")
#let muted = rgb("#6c757d")
#let bg-soft = rgb("#f4f5f9")
#let border-color = rgb("#dde1ea")
#let low-color = rgb("#e5484d")
#let mid-color = rgb("#f0a202")
#let high-color = rgb("#2f9e6e")

#let mono(body) = text(font: "DejaVu Sans Mono", body)

// Formats the RFC 3339 timestamp Rust's chrono produces (e.g.
// "2026-09-29T14:23:50.610386Z") without a datetime-parsing library, since
// the exact shape is known ahead of time.
#let month-names = (
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
)
#let format-timestamp(iso) = {
  let year = int(iso.slice(0, 4))
  let month = int(iso.slice(5, 7))
  let day = int(iso.slice(8, 10))
  let time = iso.slice(11, 16)
  str(day) + " " + month-names.at(month - 1) + " " + str(year) + ", " + time + " UTC"
}

// Red -> amber -> green across the 0..1 range, used for both similarity
// and LLM confidence so the two numbers read on a shared scale.
#let confidence-color(value) = {
  if value < 0.5 {
    color.mix((low-color, (1 - value * 2) * 100%), (mid-color, value * 2 * 100%))
  } else {
    color.mix((mid-color, (1 - (value - 0.5) * 2) * 100%), (high-color, (value - 0.5) * 2 * 100%))
  }
}

#let scale-bar(value, width: 100%, height: 8pt) = box(
  width: width,
  height: height,
  radius: height / 2,
  fill: bg-soft,
  stroke: 0.5pt + border-color,
  box(width: value * width, height: height, radius: height / 2, fill: confidence-color(value)),
)

#let badge(label, fill-color, text-color: white) = box(
  fill: fill-color,
  radius: 3pt,
  inset: (x: 6pt, y: 3pt),
  mono(text(size: 8pt, weight: "bold", fill: text-color, upper(label))),
)

#let verdict-badge(verdict) = if verdict == "LIKELY_DUPLICATE" {
  badge("likely duplicate", low-color)
} else {
  badge("review manually", mid-color)
}

#let duplicate-badge(is-duplicate) = if is-duplicate {
  badge("duplicate", low-color)
} else {
  badge("not duplicate", high-color)
}

#let stat-card(label, value, accent-color) = block(
  fill: bg-soft,
  stroke: (left: 3pt + accent-color),
  inset: 10pt,
  radius: 3pt,
  width: 100%,
  [
    #text(size: 20pt, weight: "bold", fill: ink)[#value]
    #linebreak()
    #text(size: 8pt, fill: muted)[#upper(label)]
  ],
)

#let feature-chip(feature) = box(
  fill: bg-soft,
  radius: 2pt,
  inset: (x: 5pt, y: 2pt),
  mono(text(size: 8pt, feature)),
)

#let pair-card(pair) = {
  block(
    fill: white,
    stroke: 0.5pt + border-color,
    radius: 5pt,
    inset: 14pt,
    width: 100%,
    breakable: false,
    [
      #grid(
        columns: (1fr, auto),
        align: horizon,
        text(size: 13pt, weight: "bold")[#pair.name_a  vs.  #pair.name_b],
        verdict-badge(pair.verdict),
      )

      #v(10pt)

      #grid(
        columns: (auto, 1fr, auto),
        column-gutter: 8pt,
        align: horizon,
        text(size: 9pt, fill: muted)[Similarity],
        scale-bar(pair.similarity),
        mono(text(size: 9pt, weight: "bold")[#calc.round(pair.similarity * 100, digits: 1)%]),
      )

      #if pair.reasoning != none [
        #v(12pt)
        #line(length: 100%, stroke: 0.5pt + border-color)
        #v(10pt)

        #grid(
          columns: (auto, auto, 1fr, auto),
          column-gutter: 8pt,
          align: horizon,
          duplicate-badge(pair.is_duplicate),
          text(size: 9pt, fill: muted)[LLM confidence],
          scale-bar(pair.confidence),
          mono(text(size: 9pt, weight: "bold")[#calc.round(pair.confidence * 100, digits: 1)%]),
        )

        #v(8pt)
        #text(size: 10pt)[#pair.reasoning]

        #if pair.overlapping_features != none and pair.overlapping_features.len() > 0 [
          #v(8pt)
          #text(size: 9pt, fill: muted)[Overlapping features:]
          #h(4pt)
          #for feature in pair.overlapping_features [
            #feature-chip(feature)
            #h(4pt)
          ]
        ]
      ] else [
        #v(10pt)
        #text(size: 9pt, style: "italic", fill: muted)[No explanation requested for this pair.]
      ]
    ],
  )
  v(10pt)
}

#set page(
  margin: (top: 2.2cm, bottom: 2.2cm, x: 2cm),
  footer: context [
    #line(length: 100%, stroke: 0.5pt + border-color)
    #v(4pt)
    #align(center)[#mono(text(size: 8pt, fill: muted)[SaaS Duplicate Finder  ·  Page #counter(page).display() of #counter(page).final().first()])]
  ],
)
#set text(font: "Libertinus Serif", size: 11pt, fill: ink)
#set heading(numbering: none)

#block(
  fill: ink,
  inset: (x: 20pt, y: 16pt),
  radius: 4pt,
  width: 100%,
  [
    #text(size: 20pt, weight: "bold", fill: white)[Duplicate Detection Report]
    #v(4pt)
    #text(size: 9pt, fill: rgb("#c7cbe8"))[Generated #format-timestamp(data.created_at)]
  ],
)

#v(14pt)

#block(
  fill: bg-soft,
  stroke: 0.5pt + border-color,
  radius: 4pt,
  inset: 12pt,
  width: 100%,
  grid(
    columns: (auto, 1fr),
    row-gutter: 6pt,
    column-gutter: 10pt,
    text(weight: "bold")[Checked subscriptions], text(data.subscription_names.join(", ")),
    text(weight: "bold")[Duplicate threshold], [#mono[#calc.round(data.duplicate_threshold * 100, digits: 0)%] and above marks a pair as _likely duplicate_],
    text(weight: "bold")[Review threshold], [#mono[#calc.round(data.review_threshold * 100, digits: 0)%] and above marks a pair for _manual review_],
  ),
)

#v(10pt)

#block[
  #text(size: 9pt, fill: muted)[Color scale — similarity / confidence]
  #v(3pt)
  #grid(
    columns: (auto, 1fr, auto),
    column-gutter: 6pt,
    align: horizon,
    mono(text(size: 8pt, fill: muted)[0%]),
    rect(width: 100%, height: 8pt, radius: 4pt, fill: gradient.linear(low-color, mid-color, high-color)),
    mono(text(size: 8pt, fill: muted)[100%]),
  )
]

#v(16pt)

= Summary

#let likely-count = data.pairs.filter(p => p.verdict == "LIKELY_DUPLICATE").len()
#let review-count = data.pairs.filter(p => p.verdict == "REVIEW_MANUALLY").len()

#if data.pairs.len() == 0 [
  #block(
    fill: bg-soft,
    stroke: 0.5pt + border-color,
    radius: 4pt,
    inset: 14pt,
    width: 100%,
    text(fill: muted)[No potential duplicates found among the checked subscriptions.],
  )
] else [
  #grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 10pt,
    stat-card("Pairs found", str(data.pairs.len()), ink),
    stat-card("Likely duplicates", str(likely-count), low-color),
    stat-card("Review manually", str(review-count), mid-color),
  )

  #v(20pt)

  = Details

  #for pair in data.pairs [
    #pair-card(pair)
  ]
]
