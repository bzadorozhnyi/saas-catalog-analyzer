#let data = json("data.json")

#set page(margin: 2cm)
#set text(font: "Libertinus Serif", size: 11pt)

= Duplicate Detection Report

*Checked subscriptions:* #data.subscription_names.join(", ") \
*Thresholds:* likely duplicate ≥ #data.duplicate_threshold, review ≥ #data.review_threshold \
*Generated:* #data.created_at

== Summary

#data.pairs.len() pair(s) found.

#if data.pairs.len() == 0 [
  No potential duplicates found among the checked subscriptions.
] else [
  #for pair in data.pairs [
    === #pair.name_a vs. #pair.name_b
    *Similarity:* #calc.round(pair.similarity * 100, digits: 1)% \
    *Verdict:* #pair.verdict

    #if pair.reasoning != none [
      *LLM assessment:* #if pair.is_duplicate [Likely duplicate] else [Not a duplicate] (confidence: #calc.round(pair.confidence * 100, digits: 1)%)

      #pair.reasoning

      #if pair.overlapping_features.len() > 0 [
        *Overlapping features:* #pair.overlapping_features.join(", ")
      ]
    ] else [
      _No explanation requested for this pair._
    ]
  ]
]
