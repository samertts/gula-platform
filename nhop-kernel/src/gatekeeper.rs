use crate::constitution::Constitution;

pub struct Gatekeeper {
    constitution: Constitution,
}

impl Gatekeeper {
    pub fn new(constitution: Constitution) -> Self {
        Self { constitution }
    }

    pub fn validate_request(&self) -> Result<(), String> {

        // قانون 1: كل العمليات تحتاج Audit
        if !self.constitution.principles.require_audit_logging {
            return Err("Audit logging disabled — violation".into());
        }

        // قانون 2: منع الوصول المباشر للقاعدة
        if !self.constitution.principles.no_direct_db_access {
            return Err("Direct DB access allowed — violation".into());
        }

        // قانون 3: التوكن مطلوب
        if !self.constitution.principles.require_signed_tokens {
            return Err("Signed tokens not enforced".into());
        }

        Ok(())
    }
}
