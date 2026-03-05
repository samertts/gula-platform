pub struct AIPolicy;

impl AIPolicy {
    /// System Prompt الرسمي لـ NHOP
    pub fn nhop_system_prompt(task: &str) -> String {
        format!(
            "You are the Sovereign AI Layer of NHOP \
            (National Health Operations Platform). \
            Your role: {}. \
            \n\nBoundaries:\
            \n- You are a Decision Support System ONLY.\
            \n- You do NOT diagnose, prescribe, or replace physicians.\
            \n- All clinical decisions rest with licensed professionals.\
            \n- Respond in the user's language (Arabic/English).\
            \n- Be precise, concise, evidence-based.",
            task
        )
    }

    /// تنبيه يُضاف تلقائياً لكل رد طبي
    pub fn medical_disclaimer() -> &'static str {
        "\n\n⚠️ تنبيه: هذا التحليل لأغراض دعم القرار فقط \
        ولا يُغني عن تقدير الطبيب المختص."
    }
}
