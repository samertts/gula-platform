use uuid::Uuid;
use rand::rngs::OsRng;
use ed25519_dalek::{SigningKey, VerifyingKey};

/// ======================================
/// Kernel Identity
/// ======================================
pub struct KernelIdentity {
    pub kernel_id: Uuid,
    pub signing_key: SigningKey,
    pub verifying_key: VerifyingKey,
}

impl KernelIdentity {
    pub fn new() -> Self {
        let mut csprng = OsRng;

        let signing_key = SigningKey::generate(&mut csprng);
        let verifying_key = signing_key.verifying_key();

        Self {
            kernel_id: Uuid::new_v4(),
            signing_key,
            verifying_key,
        }
    }
}
