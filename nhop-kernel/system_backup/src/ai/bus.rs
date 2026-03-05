
// ai/bus.rs
//
// AI Message Bus — NHOP Sovereign AI Layer
//
// التدفق الصحيح:
//   CLI → Comms → Kernel → [AI Bus] → AI Engine → DB → Response
//
// AI لا يقرر العمل — الـ Kernel يأمر عبر Bus

use std::sync::Arc;
use tokio::sync::{mpsc, oneshot};

use crate::identity::KernelIdentity;
use crate::status::KernelStatus;
use super::engine::{AIEngine, AITask, AIResult};

// =====================================================
// Bus Request — رسالة من الـ Kernel إلى AI
// =====================================================

pub struct AIBusRequest {
    pub task:    AITask,
    pub reply:   oneshot::Sender<AIBusResponse>,  // قناة الرد
}

// =====================================================
// Bus Response — رد من AI إلى الـ Kernel
// =====================================================

pub enum AIBusResponse {
    Ok(AIResult),
    Err(String),
}

// =====================================================
// AI Bus Sender — الواجهة التي يستخدمها الـ Kernel
// =====================================================
//
// الـ Kernel يحتفظ بـ Sender فقط
// لا يتعامل مع AI مباشرة

#[derive(Clone)]
pub struct AIBusSender {
    tx: mpsc::Sender<AIBusRequest>,
}

impl AIBusSender {
    /// إرسال task والانتظار على الرد (async)
    pub async fn send_task(
        &self,
        task: AITask,
    ) -> Result<AIResult, String> {

        let (reply_tx, reply_rx) = oneshot::channel();

        self.tx
            .send(AIBusRequest { task, reply: reply_tx })
            .await
            .map_err(|_| "AI Bus is offline".to_string())?;

        match reply_rx.await {
            Ok(AIBusResponse::Ok(result)) => Ok(result),
            Ok(AIBusResponse::Err(e))     => Err(e),
            Err(_) => Err("AI Bus dropped response".to_string()),
        }
    }
}

// =====================================================
// AI Bus — تشغيل الـ Service
// =====================================================
//
// يُستدعى من main مرة واحدة فقط
// يُعيد Sender للـ Kernel

pub fn start_ai_bus(
    identity: Arc<KernelIdentity>,
    status:   Arc<KernelStatus>,
) -> AIBusSender {

    let (tx, mut rx) = mpsc::channel::<AIBusRequest>(32);

    // ── AI Worker Task ──────────────────────────────
    // يعمل كـ background service مستقل
    // يستمع للطلبات من الـ Kernel عبر channel

    tokio::spawn(async move {   // ← FIX #2: Handle محفوظ داخل spawn

        let mut engine = AIEngine::new(
            identity.clone(),
            status.clone(),
        );

        println!("🤖 Sovereign AI Engine Online");
        println!("🧠 Sovereign AI Layer Active");

        // ── Boot Verification ───────────────────────
        // الـ Kernel يُصدر أول طلب — ليس AI نفسه
        // FIX #3: AI لا يقرر Boot Task — Bus يستلمه من Kernel

        while let Some(request) = rx.recv().await {

            let response = match engine.execute(request.task).await {
                Ok(result) => AIBusResponse::Ok(result),
                Err(e)     => AIBusResponse::Err(e.to_string()),
            };

            // إرسال الرد — لو المستقبل انتهى نتجاهل
            let _ = request.reply.send(response);
        }

        // لو وصلنا هنا → Bus أُغلق (لا يجب أن يحدث)
        eprintln!("⚠️  AI Bus worker terminated unexpectedly");
    });

    AIBusSender { tx }
}
