use reqwest::Client;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Clone)]
pub struct ChatMessage {
    pub role: String,
    pub content: String,
}

#[derive(Serialize)]
struct AnthropicRequest {
    model: String,
    max_tokens: u32,
    system: String,
    messages: Vec<ChatMessage>,
}

#[derive(Deserialize)]
pub struct ContentBlock {
    pub text: String,
}

#[derive(Deserialize)]
pub struct AnthropicResponse {
    pub content: Vec<ContentBlock>,
}

pub struct AnthropicClient {
    api_key: String,
    model: String,
    http: Client,
}

impl AnthropicClient {
    pub fn new() -> Self {
        dotenvy::dotenv().ok();
        Self {
            api_key: std::env::var("ANTHROPIC_API_KEY")
                .expect("ANTHROPIC_API_KEY missing"),
            model: std::env::var("ANTHROPIC_MODEL")
                .unwrap_or("claude-sonnet-4-6".into()),
            http: Client::new(),
        }
    }

    pub async fn send(
        &self,
        system: &str,
        messages: Vec<ChatMessage>,
    ) -> Result<String, reqwest::Error> {
        let body = AnthropicRequest {
            model: self.model.clone(),
            max_tokens: 2048,
            system: system.to_string(),
            messages,
        };

        let res = self.http
            .post("https://api.anthropic.com/v1/messages")
            .header("x-api-key", &self.api_key)
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .json(&body)
            .send()
            .await?
            .json::<AnthropicResponse>()
            .await?;

        Ok(res.content[0].text.clone())
    }
}
