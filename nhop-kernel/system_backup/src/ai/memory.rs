use crate::ai::client::ChatMessage;

pub struct ConversationMemory {
    history: Vec<ChatMessage>,
    max_turns: usize,
}

impl ConversationMemory {
    pub fn new(max_turns: usize) -> Self {
        Self { history: vec![], max_turns }
    }

    pub fn add_user(&mut self, content: &str) {
        self.history.push(ChatMessage {
            role: "user".into(),
            content: content.to_string(),
        });
        self.trim();
    }

    pub fn add_assistant(&mut self, content: &str) {
        self.history.push(ChatMessage {
            role: "assistant".into(),
            content: content.to_string(),
        });
        self.trim();
    }

    pub fn get_history(&self) -> Vec<ChatMessage> {
        self.history.clone()
    }

    fn trim(&mut self) {
        // الحفاظ على آخر N محادثة لتجنب تجاوز context window
        let limit = self.max_turns * 2;
        if self.history.len() > limit {
            self.history = self.history[self.history.len() - limit..].to_vec();
        }
    }
}
