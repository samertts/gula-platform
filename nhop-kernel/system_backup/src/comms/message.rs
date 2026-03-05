use serde::{Serialize, Deserialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

use ed25519_dalek::{
    Signature,
    SigningKey,
    VerifyingKey,
    Signer,
    Verifier,
};

/// ======================================================
/// Recipient Type
/// ======================================================
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum Recipient {
    User(Uuid),
    Channel(String),
    Broadcast,
}

/// ======================================================
/// Message Structure
/// ======================================================
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommsMessage {
    pub msg_id: Uuid,
    pub sender_id: Uuid,
    pub recipient: Recipient,
    pub content: Vec<u8>,
    pub timestamp: DateTime<Utc>,
    pub signature: Option<Vec<u8>>,
}

impl CommsMessage {

    /// --------------------------------------------------
    /// Create new message
    /// --------------------------------------------------
    pub fn new(
        sender_id: Uuid,
        recipient: Recipient,
        content: Vec<u8>,
    ) -> Self {
        Self {
            msg_id: Uuid::new_v4(),
            sender_id,
            recipient,
            content,
            timestamp: Utc::now(),
            signature: None,
        }
    }

    /// --------------------------------------------------
    /// Internal payload serialization
    /// (data that is actually signed)
    /// --------------------------------------------------
    fn payload_bytes(&self) -> Vec<u8> {
        bincode::serialize(&(
            self.msg_id,
            self.sender_id,
            &self.recipient,
            &self.content,
            self.timestamp,
        ))
        .expect("Payload serialization failed")
    }

    /// --------------------------------------------------
    /// Sign message
    /// --------------------------------------------------
    pub fn sign(&mut self, signing_key: &SigningKey) {
        let payload = self.payload_bytes();

        let signature: Signature = signing_key.sign(&payload);

        self.signature = Some(signature.to_bytes().to_vec());
    }

    /// --------------------------------------------------
    /// Verify signature
    /// --------------------------------------------------
    pub fn verify(&self, verifying_key: &VerifyingKey) -> bool {

        let sig_bytes = match &self.signature {
            Some(s) => s,
            None => return false,
        };

        // Vec<u8> → [u8;64]
        let sig_array: [u8; 64] = match sig_bytes.clone().try_into() {
            Ok(arr) => arr,
            Err(_) => return false,
        };

        let signature = Signature::from_bytes(&sig_array);

        verifying_key
            .verify(&self.payload_bytes(), &signature)
            .is_ok()
    }
}
