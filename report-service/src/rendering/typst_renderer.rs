use typst::foundations::Bytes;
use typst::syntax::{FileId, RootedPath, VirtualPath, VirtualRoot};
use typst::text::{Font, FontBook};
use typst::utils::LazyHash;
use typst::{Library, LibraryExt};
use typst_layout::PagedDocument;
use typst_pdf::PdfOptions;

use crate::rendering::report_world::ReportWorld;

/// Holds everything expensive-to-build and shared across every render call
/// (fonts, standard library) — built once at service startup and reused for
/// every report, regardless of which template is being compiled.
pub struct TypstRenderer {
    library: LazyHash<Library>,
    book: LazyHash<FontBook>,
    fonts: Vec<Font>,
}

impl Default for TypstRenderer {
    fn default() -> Self {
        Self::new()
    }
}

impl TypstRenderer {
    #[must_use]
    pub fn new() -> Self {
        let library = LazyHash::new(Library::default());
        let fonts: Vec<Font> = typst_assets::fonts()
            .filter_map(|data| Font::new(Bytes::new(data), 0))
            .collect();
        let book = LazyHash::new(FontBook::from_fonts(&fonts));
        Self {
            library,
            book,
            fonts,
        }
    }

    /// Compiles a `.typ` source string against injected JSON data (readable
    /// from the template via `json("data.json")`) into PDF bytes.
    /// Template-agnostic — the caller decides what `source_text` and
    /// `data_json` contain; this function has no idea what a "report" is.
    pub fn render(&self, source_text: String, data_json: Vec<u8>) -> anyhow::Result<Vec<u8>> {
        let main_id = Self::file_id("/main.typ");
        let data_id = Self::file_id("/data.json");

        let world = ReportWorld::new(
            self.library.clone(),
            self.book.clone(),
            self.fonts.clone(),
            main_id,
            source_text,
            data_id,
            Bytes::new(data_json),
        );

        let warned = typst::compile::<PagedDocument>(&world);
        let document = warned
            .output
            .map_err(|diags| anyhow::anyhow!("typst compile failed: {diags:?}"))?;
        let pdf_bytes = typst_pdf::pdf(&document, &PdfOptions::default())
            .map_err(|diags| anyhow::anyhow!("typst pdf export failed: {diags:?}"))?;
        Ok(pdf_bytes)
    }

    fn file_id(path: &str) -> FileId {
        let vpath = VirtualPath::new(path).expect("literal path is always valid");
        FileId::new(RootedPath::new(VirtualRoot::Project, vpath))
    }
}
