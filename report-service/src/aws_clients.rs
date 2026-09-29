use aws_config::Region;
use aws_sdk_sqs::config::Credentials;

pub async fn build_sqs_client(
    region: &str,
    endpoint_url: Option<&str>,
    access_key_id: Option<&str>,
    secret_access_key: Option<&str>,
) -> aws_sdk_sqs::Client {
    let config = build_aws_config(region, endpoint_url, access_key_id, secret_access_key).await;
    aws_sdk_sqs::Client::new(&config)
}

pub async fn build_s3_client(
    region: &str,
    endpoint_url: Option<&str>,
    access_key_id: Option<&str>,
    secret_access_key: Option<&str>,
) -> aws_sdk_s3::Client {
    let config = build_aws_config(region, endpoint_url, access_key_id, secret_access_key).await;
    // LocalStack's S3 emulator only accepts path-style requests
    // (http://localhost:4566/<bucket>/<key>), not virtual-hosted-style.
    let s3_config = aws_sdk_s3::config::Builder::from(&config)
        .force_path_style(endpoint_url.is_some())
        .build();
    aws_sdk_s3::Client::from_conf(s3_config)
}

async fn build_aws_config(
    region: &str,
    endpoint_url: Option<&str>,
    access_key_id: Option<&str>,
    secret_access_key: Option<&str>,
) -> aws_config::SdkConfig {
    let mut loader = aws_config::defaults(aws_config::BehaviorVersion::latest())
        .region(Region::new(region.to_string()));
    if let Some(endpoint_url) = endpoint_url {
        let access_key = access_key_id.unwrap_or("test");
        let secret_key = secret_access_key.unwrap_or("test");
        loader = loader
            .endpoint_url(endpoint_url)
            .credentials_provider(Credentials::new(
                access_key, secret_key, None, None, "static",
            ));
    }
    loader.load().await
}
