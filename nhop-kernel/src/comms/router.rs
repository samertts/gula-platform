use sqlx::PgPool;
use uuid::Uuid;

pub async fn send_message(
    pool: &PgPool,
    sender: Uuid,
    receiver: Uuid,
    body: String,
) -> Result<(), sqlx::Error> {

    sqlx::query(
        r#"
        INSERT INTO messages (sender_id, receiver_id, body)
        VALUES ($1, $2, $3)
        "#
    )
    .bind(sender)
    .bind(receiver)
    .bind(body)
    .execute(pool)
    .await?;

    Ok(())
}
