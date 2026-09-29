use std::path::PathBuf;

use typst::Library;
use typst::World;
use typst::diag::{FileError, FileResult};
use typst::foundations::{Bytes, Datetime, Duration};
use typst::syntax::{FileId, Source};
use typst::text::{Font, FontBook};
use typst::utils::LazyHash;

/// A [`World`] that serves a single, already-resolved template `Source` plus
/// one injected data file. Deliberately template-agnostic: it knows nothing
/// about "report" documents specifically — `TypstRenderer` decides which
/// template and data to plug in per call, so adding a new report template
/// later never requires touching this file.
pub struct ReportWorld {
    library: LazyHash<Library>,
    book: LazyHash<FontBook>,
    fonts: Vec<Font>,
    main_id: FileId,
    source: Source,
    data_id: FileId,
    data_bytes: Bytes,
}

impl ReportWorld {
    #[must_use]
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        library: LazyHash<Library>,
        book: LazyHash<FontBook>,
        fonts: Vec<Font>,
        main_id: FileId,
        source_text: String,
        data_id: FileId,
        data_bytes: Bytes,
    ) -> Self {
        let source = Source::new(main_id, source_text);
        Self {
            library,
            book,
            fonts,
            main_id,
            source,
            data_id,
            data_bytes,
        }
    }
}

impl World for ReportWorld {
    fn library(&self) -> &LazyHash<Library> {
        &self.library
    }

    fn book(&self) -> &LazyHash<FontBook> {
        &self.book
    }

    fn main(&self) -> FileId {
        self.main_id
    }

    fn source(&self, id: FileId) -> FileResult<Source> {
        if id == self.main_id {
            Ok(self.source.clone())
        } else {
            Err(FileError::NotFound(PathBuf::from(
                id.vpath().get_with_slash(),
            )))
        }
    }

    fn file(&self, id: FileId) -> FileResult<Bytes> {
        if id == self.data_id {
            Ok(self.data_bytes.clone())
        } else {
            Err(FileError::NotFound(PathBuf::from(
                id.vpath().get_with_slash(),
            )))
        }
    }

    fn font(&self, index: usize) -> Option<Font> {
        self.fonts.get(index).cloned()
    }

    fn today(&self, _offset: Option<Duration>) -> Option<Datetime> {
        None
    }
}
