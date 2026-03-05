memory::ConversationMemory, policy::AIPolicy};

pub async fn analyze_lab_result(
    client: &AnthropicClient,
    memory: &mut ConversationMemory,
    lab_data: &str,
) -> Result<String, reqwest::Error> {
    let system = AIPolicy::nhop_system_prompt(
        "Laboratory AI Assistant — interpret lab results, \
        detect anomalies, suggest follow-up tests, \
        flag potential errors"
    );

    memory.add_user(lab_data);

    let response = client
        .send(&system, memory.get_history())
        .await?;

    let final_response = format!(
        "{}{}",
        response,
        AIPolicy::medical_disclaimer()
    );

    memory.add_assistant(&final_response);
    Ok(final_response)
}

use crate::ai::{
    client::AnthropicClient,
    memory::ConversationMemory,
    policy::AIPolicy,
    tasks::lab_analysis::analyze_lab_result,
};

pub enum AITask {
    LabAnalysis(String),
    EpiWatch(String),
    DecisionSupport(String),
    SystemDiagnostics(String),
    GeneralAssistant(String),
}

pub struct AIEngine {
    client: AnthropicClient,
    memory: ConversationMemory,
}

impl AIEngine {
    pub fn new() -> Self {
        Self {
            client: AnthropicClient::new(),
            memory: ConversationMemory::new(20),
        }
    }

    pub async fn execute(&mut self, task: AITask) -> Result<String, reqwest::Error> {
        match task {
            AITask::LabAnalysis(data) =>
                analyze_lab_result(&self.client, &mut self.memory, &data).await,

            AITask::EpiWatch(data) => {
                let system = AIPolicy::nhop_system_prompt(
                    "Epidemiological Intelligence — detect outbreak patterns, \
                    geographic spread, early warning signals"
                );
                self.memory.add_user(&data);
                let res = self.client.send(&system, self.memory.get_history()).await?;
                self.memory.add_assistant(&res);
                Ok(res)
            }

            AITask::SystemDiagnostics(data) => {
                let system = AIPolicy::nhop_system_prompt(
                    "System Security & Operations Analyst — analyze system health, \
                    detect anomalies, support kernel operations, enhance security"
                );
                self.memory.add_user(&data);
                let res = self.client.send(&system, self.memory.get_history()).await?;
                self.memory.add_assistant(&res);
                Ok(res)
            }

            _ => {
                // General fallback
                let system = AIPolicy::nhop_system_prompt("General NHOP Assistant");
                if let AITask::GeneralAssistant(q) = task {
                    self.memory.add_user(&q);
                    let res = self.client.send(&system, self.memory.get_history()).await?;
                    self.memory.add_assistant(&res);
                    Ok(res)
                } else { Ok("Unknown task".into()) }
            }
        }
    }
}
