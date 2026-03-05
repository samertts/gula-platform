use std::sync::Arc;

use crate::identity::KernelIdentity;
use crate::status::KernelStatus;
use crate::comms::engine::CommsEngine;

#[derive(Clone)]
pub struct KernelContext {
    pub identity: Arc<KernelIdentity>,
    pub status: Arc<KernelStatus>,
    pub comms: Arc<CommsEngine>,
}

impl KernelContext {
    pub fn new(
        identity: Arc<KernelIdentity>,
        status: Arc<KernelStatus>,
        comms: Arc<CommsEngine>,
    ) -> Self {
        Self {
            identity,
            status,
            comms,
        }
    }
}
