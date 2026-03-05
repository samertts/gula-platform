use crate::audit::Audit;
use crate::guardian::Guardian;

pub struct Kernel;

impl Kernel {
    pub fn initialize() {
        println!("⚙ Initializing Sovereign Kernel");

        Guardian::boot_check();
        Audit::log("Kernel initialized");
    }
}
