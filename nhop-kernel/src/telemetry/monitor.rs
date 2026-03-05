use std::sync::Arc;
use tokio::time::{sleep, Duration};

use crate::status::KernelStatus;

pub struct SovereignMonitor;

impl SovereignMonitor {
    pub fn start(status: Arc<KernelStatus>) {
        tokio::spawn(async move {
            println!("📡 Sovereign Monitoring Activated");

            loop {
                Self::print_health(&status);
                sleep(Duration::from_secs(15)).await;
            }
        });
    }

    fn print_health(status: &KernelStatus) {
        println!();
        println!("================ SYSTEM TELEMETRY ================");
        println!("Kernel ID      : {}", status.kernel_id);
        println!("Guardian       : {}", if status.guardian_online { "ONLINE" } else { "OFFLINE" });
        println!("Constitution   : {}", if status.constitution_loaded { "LOADED" } else { "MISSING" });
        println!("Database       : {}", if status.db_connected { "CONNECTED" } else { "DISCONNECTED" });
        println!("==================================================");
        println!();
    }
}
