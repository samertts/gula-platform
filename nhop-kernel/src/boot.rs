use crate::constitution::load_constitution;
use crate::db;

pub async fn start() {
    println!("Booting NHOP Sovereign Kernel...");

    let constitution =
        load_constitution("core/constitution/constitution.json")
            .expect("Failed to load constitution");

    println!("✅ Constitution Loaded");
    println!("System: {}", constitution.system);
    println!("Version: {}", constitution.version);

    db::connect_db().await;

    println!("Kernel startup allowed.");
}
