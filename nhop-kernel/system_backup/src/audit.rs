use chrono::Utc;

pub struct Audit;

impl Audit {
    pub fn log(action: &str) {
        let time = Utc::now();
        println!("[AUDIT {}] {}", time, action);
    }
}
