

use tokio_postgres::{NoTls, Error};
use dotenvy::dotenv;
use std::env;

pub async fn connect_db() -> Result<(), Error> {
    dotenv().ok();

    let conn_str = format!(
        "host={} user={} password={} dbname={} port={}",
        env::var("DB_HOST").unwrap(),
        env::var("DB_USER").unwrap(),
        env::var("DB_PASSWORD").unwrap(),
        env::var("DB_NAME").unwrap(),
        env::var("DB_PORT").unwrap(),
    );

    let (_client, connection) =
        tokio_postgres::connect(&conn_str, NoTls).await?;

    tokio::spawn(async move {
        if let Err(e) = connection.await {
            eprintln!("DB connection error: {}", e);
        }
    });

    println!("✅ NHOP connected to database");

    Ok(())
}

