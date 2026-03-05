//
// Sovereign AI Engine — NHOP Kernel Service
// AI ليس مستقلاً — يعمل تحت سلطة الـ Kernel

use std::sync::Arc;

use crate::identity::KernelIdentity;
use crate::status::KernelStatus;

use super::client::{AnthropicClient, ChatMessage};
use super::memory::ConversationMemory;
use super::policy::AIPolicy;
use super::tasks::lab_analysis::analyze_lab_result;

// =====================================================
// AI Task — الأوامر التي يستقبلها AI من الـ Kernel
// =====================================================

pub enum AITask {
    LabAnalysis(String),
    EpiWatch(String),
    DecisionSupport(String),
    SystemDiagnostics(String),
    GeneralAssistant(String),
}

// =====================================================
// AI Task Result — يُعاد لـ Kernel أو DB
// =====================================================

pub struct AIResult {
    pub task_id: String,
    pub output: String,
    pub status: AIResultStatus,
}

pub enum AIResultStatus {
    Success,
    Degraded,   // استجاب لكن بجودة منخفضة
    Failed,
}

// =====================================================
// AI Engine — يستلم Kernel Context عند الإنشاء
// AI لا يعمل خارج سلطة الـ Kernel
// =====================================================

pub struct AIEngine {
    client:   AnthropicClient,
    memory:   ConversationMemory,
    identity: Arc<KernelIdentity>,   // ← FIX #1
    status:   Arc<KernelStatus>,     // ← FIX #1
}

impl AIEngine {
    /// Constructor — يستلم Kernel Context إلزامياً
    pub fn new(
        identity: Arc<KernelIdentity>,
        status:   Arc<KernelStatus>,
    ) -> Self {
        Self {
            client:   AnthropicClient::new(),
            memory:   ConversationMemory::new(20),
            identity,
            status,
        }
    }

    /// تنفيذ Task — مطلوب من الـ Kernel
    pub async fn execute(
        &mut self,
        task: AITask,
    ) -> Result<AIResult, reqwest::Error> {

        let task_id = format!(
            "{}-{}",
            self.identity.kernel_id,
            uuid_now()
        );

        let output = match task {

            AITask::LabAnalysis(data) => {
                analyze_lab_result(
                    &self.client,
                    &mut self.memory,
                    &data,
                ).await?
            }

            AITask::EpiWatch(data) => {
                let system = AIPolicy::nhop_system_prompt(
                    "Epidemiological Intelligence — detect outbreak \
                     patterns, geographic spread, early warning signals"
                );
                self.run_with_memory(&system, &data).await?
            }

            AITask::SystemDiagnostics(data) => {
                // AI يعرف هوية النظام الذي يفحصه
                let context = format!(
                    "[Kernel: {}]\n{}",
                    self.identity.kernel_id,
                    data
                );
                let system = AIPolicy::nhop_system_prompt(
                    "System Security & Operations Analyst — \
                     analyze kernel health, detect anomalies, \
                     enhance system security"
                );
                self.run_with_memory(&system, &context).await?
            }

            AITask::DecisionSupport(data) => {
                let system = AIPolicy::nhop_system_prompt(
                    "Clinical Decision Support — evidence-based \
                     guidance, risk alerts, protocol recommendations"
                );
                self.run_with_memory(&system, &data).await?
            }

            AITask::GeneralAssistant(q) => {
                let system = AIPolicy::nhop_system_prompt(
                    "General NHOP Assistant — clinical, \
                     administrative, and operational support"
                );
                self.run_with_memory(&system, &q).await?
            }
        };

        Ok(AIResult {
            task_id,
            output,
            status: AIResultStatus::Success,
        })
    }

    /// Helper داخلي — تشغيل مع memory
    async fn run_with_memory(
        &mut self,
        system: &str,
        input: &str,
    ) -> Result<String, reqwest::Error> {
        self.memory.add_user(input);
        let response = self.client
            .send(system, self.memory.get_history())
            .await?;
        let final_response = format!(
            "{}{}",
            response,
            AIPolicy::medical_disclaimer()
        );
        self.memory.add_assistant(&final_response);
        Ok(final_response)
    }
}

/// UUID بسيط من timestamp (بدون dependency إضافية)
fn uuid_now() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}
