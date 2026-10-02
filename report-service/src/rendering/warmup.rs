use std::collections::BTreeSet;
use std::fs;

use crate::rendering::typst_renderer::TypstRenderer;

/// Forces resolution (and, on a cold cache, download) of every `@preview`
/// package the templates import, once, before the consumer starts claiming
/// real SQS messages — so the first real report doesn't pay for a cold
/// `typst-kit` package fetch (the dominant cost on a fresh deploy; this is
/// what the `render` span in traces was showing). Derives the package list
/// straight from whatever `templates/*.typ` actually imports right now, so
/// there's nothing here to keep in sync by hand when a template's imports
/// change.
///
/// Best-effort: a failure here (e.g. the package registry is briefly
/// unreachable) is logged and otherwise ignored rather than stopping the
/// service from starting — worst case, the first real report pays the cold
/// cost instead, exactly like before this existed.
pub fn warm_up(renderer: &TypstRenderer, templates_dir: &str) {
    let source = match build_warmup_source(templates_dir) {
        Ok(Some(source)) => source,
        Ok(None) => {
            tracing::info!("no @preview imports found in templates, nothing to warm up");
            return;
        }
        Err(error) => {
            tracing::warn!(%error, "failed to scan templates for warm-up, continuing anyway");
            return;
        }
    };

    let started = std::time::Instant::now();
    match renderer.render(source, b"{}".to_vec()) {
        Ok(_) => {
            tracing::info!(elapsed = ?started.elapsed(), "warmed up Typst package cache");
        }
        Err(error) => {
            tracing::warn!(%error, "Typst package cache warm-up failed, continuing anyway");
        }
    }
}

/// Collects every distinct `@preview/<name>:<version>` spec referenced by
/// `templates/*.typ` into one tiny synthetic document — just the bare
/// imports, no symbols or body, enough to make Typst resolve each package
/// without needing any report data at all. Regex-based, not a full Typst
/// parser — fine since these are our own, fully-controlled template files,
/// not external input.
fn build_warmup_source(templates_dir: &str) -> anyhow::Result<Option<String>> {
    let pattern = regex::Regex::new(r"@preview/[A-Za-z0-9_-]+:[0-9]+\.[0-9]+\.[0-9]+")?;
    let mut specs = BTreeSet::new();

    for entry in fs::read_dir(templates_dir)? {
        let path = entry?.path();
        if path.extension().and_then(|ext| ext.to_str()) != Some("typ") {
            continue;
        }
        let text = fs::read_to_string(&path)?;
        specs.extend(pattern.find_iter(&text).map(|m| m.as_str().to_string()));
    }

    if specs.is_empty() {
        return Ok(None);
    }
    let source = specs.into_iter().fold(String::new(), |mut source, spec| {
        use std::fmt::Write;
        let _ = writeln!(source, "#import \"{spec}\"");
        source
    });
    Ok(Some(source))
}
