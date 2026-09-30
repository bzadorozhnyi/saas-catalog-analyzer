use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct DbSettings {
    pub host: String,
    pub port: u16,
    pub user: String,
    pub password: String,
    pub name: String,
    pub ssl_mode: String,
}

impl DbSettings {
    #[must_use]
    pub fn url(&self) -> String {
        format!(
            "postgres://{}:{}@{}:{}/{}?sslmode={}",
            self.user, self.password, self.host, self.port, self.name, self.ssl_mode
        )
    }
}

fn default_queue_name() -> String {
    "report-generation-queue".to_string()
}

fn default_dlq_name() -> String {
    "report-generation-dlq".to_string()
}

fn default_account_id() -> String {
    "000000000000".to_string()
}

fn default_region() -> String {
    "us-east-1".to_string()
}

#[derive(Debug, Deserialize)]
pub struct SqsSettings {
    #[serde(default = "default_queue_name")]
    pub queue_name: String,
    #[serde(default = "default_dlq_name")]
    pub dlq_name: String,
    #[serde(default = "default_account_id")]
    pub account_id: String,
    #[serde(default = "default_region")]
    pub region: String,
    pub endpoint_url: Option<String>,
    pub access_key_id: Option<String>,
    pub secret_access_key: Option<String>,
}

impl SqsSettings {
    #[must_use]
    pub fn queue_url(&self) -> String {
        Self::build_url(
            &self.queue_name,
            &self.account_id,
            &self.region,
            self.endpoint_url.as_deref(),
        )
    }

    #[must_use]
    pub fn dlq_url(&self) -> String {
        Self::build_url(
            &self.dlq_name,
            &self.account_id,
            &self.region,
            self.endpoint_url.as_deref(),
        )
    }

    fn build_url(
        queue_name: &str,
        account_id: &str,
        region: &str,
        endpoint_url: Option<&str>,
    ) -> String {
        let host = endpoint_url.map_or_else(
            || format!("https://sqs.{region}.amazonaws.com"),
            str::to_string,
        );
        format!("{host}/{account_id}/{queue_name}")
    }
}

fn default_bucket_name() -> String {
    "report-documents".to_string()
}

#[derive(Debug, Deserialize)]
pub struct S3Settings {
    #[serde(default = "default_bucket_name")]
    pub bucket_name: String,
    #[serde(default = "default_region")]
    pub region: String,
    pub endpoint_url: Option<String>,
    pub access_key_id: Option<String>,
    pub secret_access_key: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct Settings {
    pub db: DbSettings,
    pub sqs: SqsSettings,
    pub s3: S3Settings,
}

impl Settings {
    pub fn load() -> anyhow::Result<Self> {
        let raw = config::Config::builder()
            .add_source(
                config::Environment::default()
                    .separator("__")
                    .try_parsing(true),
            )
            .build()?;
        Ok(raw.try_deserialize()?)
    }
}
