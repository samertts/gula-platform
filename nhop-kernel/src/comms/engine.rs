use std::collections::{HashMap, VecDeque};
use tokio::sync::Mutex;
use uuid::Uuid;

use crate::comms::message::{CommsMessage, Recipient};

/// =====================================
/// Communications Engine
/// =====================================
pub struct CommsEngine {
    /// inbox per USER only
    inboxes: Mutex<HashMap<Uuid, VecDeque<CommsMessage>>>,
}

impl CommsEngine {

    /// Create new engine
    pub fn new() -> Self {
        Self {
            inboxes: Mutex::new(HashMap::new()),
        }
    }

    /// =====================================
    /// Send Message
    /// =====================================
    pub async fn send_message(&self, msg: CommsMessage) {

        let mut inboxes = self.inboxes.lock().await;

        match &msg.recipient {

            // ---------- Direct user message ----------
            Recipient::User(user_id) => {
                inboxes
                    .entry(*user_id)
                    .or_insert_with(VecDeque::new)
                    .push_back(msg);
            }

            // ---------- Channel (future feature) ----------
            Recipient::Channel(_channel) => {
                // placeholder — channels not implemented yet
                println!("Channel messaging not implemented yet");
            }

            // ---------- Broadcast ----------
            Recipient::Broadcast => {
                for queue in inboxes.values_mut() {
                    queue.push_back(msg.clone());
                }
            }
        }
    }

    /// =====================================
    /// Receive Messages
    /// =====================================
    pub async fn receive(&self, user: Uuid) -> Vec<CommsMessage> {

        let mut inboxes = self.inboxes.lock().await;

        if let Some(queue) = inboxes.get_mut(&user) {
            queue.drain(..).collect()
        } else {
            vec![]
        }
    }
}
