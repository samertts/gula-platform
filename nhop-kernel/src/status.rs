use uuid::Uuid;
use std::sync::{Arc, Mutex};

#[derive(Debug)]
pub struct KernelStatus {
    pub kernel_id: Uuid,
    pub guardian_online: bool,
    pub constitution_loaded: bool,
    pub db_connected: bool,
}

impl KernelStatus {
    pub fn new(kernel_id: Uuid) -> Self {
        Self {
            kernel_id,
            guardian_online: true,
            constitution_loaded: true,
            db_connected: false,
        }
    }

    pub fn set_db_connected(&mut self, value: bool) {
        self.db_connected = value;
    }
}

//
// ✅ THIS IS THE MISSING FUNCTION
//
pub fn print_status(status: &Arc<KernelStatus>) {
    println!("==============================");
    println!("NHOP Sovereign Kernel Status");
    println!("==============================");

    println!("Kernel ID: {}", status.kernel_id);

    println!(
        "Guardian: {}",
        if status.guardian_online {
            "ONLINE"
        } else {
            "OFFLINE"
        }
    );

    println!(
        "Constitution: {}",
        if status.constitution_loaded {
            "LOADED"
        } else {
            "NOT LOADED"
        }
    );

    println!(
        "Database: {}",
        if status.db_connected {
            "CONNECTED"
        } else {
            "DISCONNECTED"
        }
    );

    println!("==============================");
}
