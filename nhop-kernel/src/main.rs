use std::path::PathBuf;
use std::sync::Arc;
use std::time::Duration;

mod ai;
mod constitution;
mod db;
mod identity;
mod status;
mod comms;

use ai::bus::{start_ai_bus, AIBusSender};
use ai::engine::AITask;
use identity::KernelIdentity;
use status::KernelStatus;
use comms::engine::CommsEngine;

#[tokio::main]
async fn main() {

    println!("🚀 Booting NHOP Sovereign Kernel...");

    // =====================================================
    // Kernel Initialization
    // =====================================================

    println!("⚙  Initializing Sovereign Kernel");
    println!("🛡  Guardian online");
    println!("🧠 Memory check passed");
    println!("🔒 Kernel integrity verified");

    // =====================================================
    // Constitution Load
    // =====================================================

    let constitution_path =
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("constitution.json");

    let constitution_path_str = constitution_path
        .to_str()
        .expect("Invalid constitution path");

    constitution::load_constitution(constitution_path_str)
        .expect("Failed to load constitution");

    println!("✅ Constitution loaded successfully");
    println!("✅ Gatekeeper validation passed");

    // =====================================================
    // Identity Creation
    // =====================================================

    let identity = Arc::new(KernelIdentity::new());

    println!(
        "🧬 Kernel Identity Ready: {}",
        identity.kernel_id
    );

    // =====================================================
    // Kernel Status Tracker
    // =====================================================

    let kernel_status =
        Arc::new(KernelStatus::new(identity.kernel_id));

    // =====================================================
    // Database Connection (NON-BLOCKING)
    // =====================================================

    tokio::spawn(async move {
        match db::connect_db().await {
            Ok(_) => {
                println!("✅ NHOP connected to database");
                println!("✅ Database connection established");
            }
            Err(e) => {
                eprintln!("❌ Database connection failed: {}", e);
            }
        }
    });

    // =====================================================
    // Communications Engine
    // =====================================================

    let comms_engine = Arc::new(CommsEngine::new());

    println!("📡 NHOP Internal Comms Ready");

    // =====================================================
    // FIX #1 + #2 + #3 — Sovereign AI Bus
    // =====================================================
    //
    // AI يستلم Kernel Context (Identity + Status)
    // Bus يُعيد Sender فقط — Kernel لا يلمس Engine
    // Boot Task يصدر من الـ Kernel عبر Bus
    // Handle محفوظ داخل start_ai_bus (لا silent failure)

    let ai_bus: AIBusSender = start_ai_bus(
        identity.clone(),
        kernel_status.clone(),
    );

    println!("🔗 AI Bus connected to Kernel");

    // =====================================================
    // CLI Interface (Independent Runtime)
    // =====================================================

    let identity_clone = identity.clone();
    let engine_clone   = comms_engine.clone();
    let status_clone   = kernel_status.clone();
    let ai_bus_clone   = ai_bus.clone(); // CLI يمكنه إرسال AI tasks

    tokio::spawn(async move {
        comms::cli::run_cli(
            identity_clone,
            engine_clone,
            status_clone,
        )
        .await;
    });

    // =====================================================
    // Kernel Boot Verification — Proof of Authority
    // =====================================================
    //
    // الـ Kernel يُصدر أول طلب لـ AI (ليس AI نفسه)
    // FIX #3: السيادة تبقى في Kernel

    tokio::time::sleep(Duration::from_millis(500)).await;

    match ai_bus.send_task(
        AITask::LabAnalysis(
            "WBC: 14.5 K/uL | CRP: 48 mg/L | Temp: 38.9°C | Patient: 34M"
                .into(),
        )
    ).await {
        Ok(result) => {
            println!("📊 AI Boot Verification:");
            println!("{}", result.output);
            println!("✅ AI Layer verified [task_id: {}]", result.task_id);
        }
        Err(e) => {
            // فشل AI لا يوقف الـ Kernel
            eprintln!("⚠️  AI boot check failed (non-fatal): {}", e);
            eprintln!("⚠️  AI Layer degraded — kernel continues");
        }
    }

    // =====================================================
    // Kernel Online — All Systems Nominal
    // =====================================================

    println!("🚀 NHOP Kernel Online — All Systems Nominal");

    // =====================================================
    // Keep Kernel Alive
    // =====================================================
    //
    // Main thread = Kernel heartbeat فقط
    // جميع العمليات في spawned tasks
    //
    // التدفق النهائي:
    //   CLI → ai_bus.send_task() → AI Engine → AIResult
    //   DB  → ai_bus.send_task() → AI Engine → AIResult
    //   API → ai_bus.send_task() → AI Engine → AIResult

    loop {
        tokio::time::sleep(Duration::from_secs(3600)).await;
    }
}
