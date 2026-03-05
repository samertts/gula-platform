use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

//
// ============================================================
// ROOT CONSTITUTION
// ============================================================
//

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Constitution {
    pub system: SystemConfig,
    pub guardian: GuardianConfig,
    pub security: SecurityConfig,
    pub network: NetworkConfig,
    pub runtime: RuntimeConfig,
}

//
// ============================================================
// SYSTEM
// ============================================================
//

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SystemConfig {
    pub name: String,
    pub version: String,
}

//
// ============================================================
// GUARDIAN
// ============================================================
//

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct GuardianConfig {
    pub enabled: bool,
    pub max_repair_actions_per_hour: u32,
    pub watchdog_interval_seconds: u64,
}

//
// ============================================================
// SECURITY
// ============================================================
//

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SecurityConfig {
    pub allow_self_modification: bool,
    pub audit_required: bool,
    pub require_signed_messages: bool,
}

//
// ============================================================
// NETWORK
// ============================================================
//

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct NetworkConfig {
    pub internal_comms_enabled: bool,
    pub max_peers: u32,
}

//
// ============================================================
// RUNTIME
// ============================================================
//

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RuntimeConfig {
    pub log_level: String,
    pub cli_enabled: bool,
}

//
// ============================================================
// LOADER
// ============================================================
//

pub fn load_constitution<P: AsRef<Path>>(
    path: P,
) -> Result<Constitution, Box<dyn std::error::Error>> {
    let content = fs::read_to_string(&path)?;

    let constitution: Constitution =
        serde_json::from_str(&content)
            .map_err(|e| format!("Invalid constitution JSON format: {}", e))?;

    validate_constitution(&constitution)?;

    Ok(constitution)
}

//
// ============================================================
// VALIDATION LAYER
// ============================================================
//

fn validate_constitution(
    constitution: &Constitution,
) -> Result<(), Box<dyn std::error::Error>> {

    if constitution.system.name.trim().is_empty() {
        return Err("System name cannot be empty".into());
    }

    if constitution.network.max_peers == 0 {
        return Err("max_peers must be > 0".into());
    }

    if constitution.guardian.watchdog_interval_seconds < 5 {
        return Err("watchdog interval too low".into());
    }

    Ok(())
}
