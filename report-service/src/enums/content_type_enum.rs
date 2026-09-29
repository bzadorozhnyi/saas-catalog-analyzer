#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ContentType {
    Pdf,
}

impl ContentType {
    #[must_use]
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Pdf => "application/pdf",
        }
    }
}
