use std::path::PathBuf;

use typst::Library;
use typst::World;
use typst::diag::{FileError, FileResult};
use typst::foundations::{Bytes, Datetime, Duration};
use typst::syntax::{FileId, Source, VirtualRoot};
use typst::text::{Font, FontBook};
use typst::utils::LazyHash;
use typst_kit::downloader::SystemDownloader;
use typst_kit::packages::SystemPackages;

/// Resolves `@preview` package files (e.g. `cetz`) on demand, downloading
/// and caching them the same way `typst-cli` does (via `typst-kit`, the
/// official helper crate for exactly this). Kept separate from the
/// in-memory template/data serving below since it's the one part of
/// `ReportWorld` that touches the network/filesystem.
struct PackageLoader {
    packages: SystemPackages,
}

impl PackageLoader {
    fn new() -> Self {
        Self {
            packages: SystemPackages::new(SystemDownloader::new("report-service")),
        }
    }

    fn load(&self, id: FileId) -> FileResult<Bytes> {
        let VirtualRoot::Package(spec) = id.root() else {
            return Err(FileError::NotFound(PathBuf::from(
                id.vpath().get_with_slash(),
            )));
        };
        let root = self.packages.obtain(spec).map_err(FileError::Package)?;
        root.load(id.vpath())
    }
}

/// A [`World`] that serves a single, already-resolved template `Source` plus
/// one injected data file, and resolves `@preview` packages on demand.
/// Deliberately template-agnostic: it knows nothing about "report" documents
/// specifically — `TypstRenderer` decides which template and data to plug in
/// per call, so adding a new report template later never requires touching
/// this file.
pub struct ReportWorld {
    library: LazyHash<Library>,
    book: LazyHash<FontBook>,
    fonts: Vec<Font>,
    main_id: FileId,
    source: Source,
    data_id: FileId,
    data_bytes: Bytes,
    packages: PackageLoader,
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
            packages: PackageLoader::new(),
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
            return Ok(self.source.clone());
        }
        if matches!(id.root(), VirtualRoot::Package(_)) {
            let bytes = self.packages.load(id)?;
            let text = std::str::from_utf8(&bytes)
                .map_err(|_| FileError::InvalidUtf8)?
                .to_string();
            return Ok(Source::new(id, text));
        }
        Err(FileError::NotFound(PathBuf::from(
            id.vpath().get_with_slash(),
        )))
    }

    fn file(&self, id: FileId) -> FileResult<Bytes> {
        if id == self.data_id {
            return Ok(self.data_bytes.clone());
        }
        if matches!(id.root(), VirtualRoot::Package(_)) {
            return self.packages.load(id);
        }
        Err(FileError::NotFound(PathBuf::from(
            id.vpath().get_with_slash(),
        )))
    }

    fn font(&self, index: usize) -> Option<Font> {
        self.fonts.get(index).cloned()
    }

    fn today(&self, _offset: Option<Duration>) -> Option<Datetime> {
        None
    }
}
