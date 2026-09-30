#import "@preview/cetz:0.4.0": canvas
#import "@preview/cetz-plot:0.1.2": chart

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

// `index` matches this pair's position in `data.pairs`, shared with the
// ranked chart above — that's what `link(label("pair-" + str(index)))`
// in `bar-row` jumps to.
#let pair-card(pair, index) = [
  #metadata(none)
  #label("pair-" + str(index))
  #block(
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
  #v(10pt)
]

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

  = Subscription Involvement

  // Per-subscription rollup, computed from `data.pairs` — how many pairs
  // each subscription shows up in, its average similarity across those,
  // and how many of them are flagged likely duplicates. Sorted so the
  // subscriptions most worth a second look surface first.
  #let subscription-stats = data.subscription_names.map(name => {
    let involved = data.pairs.filter(p => p.name_a == name or p.name_b == name)
    let count = involved.len()
    let avg-similarity = if count > 0 {
      involved.map(p => p.similarity).sum() / count
    } else {
      0
    }
    let likely = involved.filter(p => p.verdict == "LIKELY_DUPLICATE").len()
    (name: name, count: count, avg-similarity: avg-similarity, likely: likely)
  })
  #let sorted-stats = subscription-stats.sorted(key: s => -s.avg-similarity)

  #table(
    columns: (1fr, auto, auto, auto),
    stroke: 0.5pt + border-color,
    inset: 8pt,
    align: (left, center, center, center),
    fill: (x, y) => if y == 0 { bg-soft } else { white },
    table.header(
      text(size: 9pt, weight: "bold", fill: muted)[SUBSCRIPTION],
      text(size: 9pt, weight: "bold", fill: muted)[PAIRS],
      text(size: 9pt, weight: "bold", fill: muted)[AVG SIMILARITY],
      text(size: 9pt, weight: "bold", fill: muted)[LIKELY DUPLICATES],
    ),
    ..sorted-stats
      .map(s => (
        text(size: 10pt)[#s.name],
        mono(text(size: 9pt)[#s.count]),
        mono(text(size: 9pt)[#calc.round(s.avg-similarity * 100, digits: 1)%]),
        if s.likely > 0 {
          badge(str(s.likely), low-color)
        } else {
          text(size: 9pt, fill: muted)[--]
        },
      ))
      .flatten(),
  )

  = Similarity Landscape

  // `data.pairs` already arrives sorted by similarity DESC (the SQL query
  // orders it), so slicing the first N gives the top N directly, and the
  // index into this array is stable — it's exactly what `pair-card` labels
  // its card with, so each bar's name links straight to its detail card.
  #let top-n = 30
  #let shown-count = calc.min(top-n, data.pairs.len())
  #let shown = data.pairs.slice(0, shown-count)
  #let chart-data = shown.enumerate().map(entry => {
    let (i, p) = entry
    (
      link(label("pair-" + str(i)))[#text(size: 8pt)[#p.name_a vs. #p.name_b]],
      p.similarity,
    )
  })

  // `canvas()` is one opaque vector block Typst can't paginate mid-way —
  // wrapping it `breakable: false` tells Typst to push the whole thing to
  // the next page if it doesn't fit in what's left of the current one,
  // instead of letting it overflow past the margin/footer.
  #block(
    breakable: false,
    canvas({
      chart.barchart(
        mode: "basic",
        size: (11, shown-count * 0.5),
        label-key: 0,
        value-key: 1,
        x-label: [Similarity],
        bar-style: i => (
          fill: if shown.at(i).verdict == "LIKELY_DUPLICATE" { low-color } else { mid-color },
        ),
        chart-data,
      )
    }),
  )

  #if data.pairs.len() > shown-count [
    #v(6pt)
    #text(size: 9pt, fill: muted)[+#(data.pairs.len() - shown-count) more pair(s) not shown above — see Details.]
  ]

  #v(20pt)

  = Details

  #for (i, pair) in data.pairs.enumerate() [
    #pair-card(pair, i)
  ]
]
