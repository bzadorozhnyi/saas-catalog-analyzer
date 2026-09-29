use aws_sdk_s3::primitives::ByteStream;

use crate::enums::content_type_enum::ContentType;

pub struct S3Service {
    client: aws_sdk_s3::Client,
    bucket_name: String,
}

impl S3Service {
    #[must_use]
    pub fn new(client: aws_sdk_s3::Client, bucket_name: String) -> Self {
        Self {
            client,
            bucket_name,
        }
    }

    pub async fn upload(
        &self,
        key: &str,
        bytes: Vec<u8>,
        content_type: ContentType,
    ) -> Result<(), aws_sdk_s3::Error> {
        self.client
            .put_object()
            .bucket(&self.bucket_name)
            .key(key)
            .body(ByteStream::from(bytes))
            .content_type(content_type.as_str())
            .send()
            .await?;
        Ok(())
    }
}
