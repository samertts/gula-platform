

use std::sync::Arc;
use rustyline::DefaultEditor;
use uuid::Uuid;

use crate::identity::KernelIdentity;
use crate::status;
use crate::status::KernelStatus;

use crate::comms::{
    engine::CommsEngine,
    message::{CommsMessage, Recipient},
};

pub async fn run_cli(
    identity: Arc<KernelIdentity>,
    engine: Arc<CommsEngine>,
    kernel_status: Arc<KernelStatus>,
) {
    let mut rl = DefaultEditor::new().unwrap();

    println!("NHOP Internal Comms Ready");
    println!("Commands:");
    println!("/send <uuid> <message>");
    println!("/inbox");
    println!("/status");
    println!("/exit");

    loop {
        let line = rl.readline(">> ");

        let line = match line {
            Ok(l) => l.trim().to_string(),
            Err(_) => continue,
        };

        // ==========================
        // EXIT
        // ==========================
        if line == "/exit" {
            println!("Shutting down CLI...");
            break;
        }

        // ==========================
        // STATUS
        // ==========================
        if line == "/status" {
            status::print_status(&kernel_status);
            continue;
        }

        // ==========================
        // SEND MESSAGE
        // ==========================
        if line.starts_with("/send ") {
            let args: Vec<&str> = line[6..].splitn(2, ' ').collect();

            if args.len() < 2 {
                println!("Usage: /send <uuid> <message>");
                continue;
            }

            let target_uuid = match Uuid::parse_str(args[0]) {
                Ok(v) => v,
                Err(_) => {
                    println!("Invalid UUID");
                    continue;
                }
            };

            let recipient = Recipient::User(target_uuid);

            let mut msg = CommsMessage::new(
                identity.kernel_id,
                recipient,
                args[1].as_bytes().to_vec(),
            );

            // sign message
            msg.sign(&identity.signing_key);

            // send
            engine.send_message(msg).await;

            println!("Message sent.");
            continue;
        }

        // ==========================
        // INBOX
        // ==========================
        if line == "/inbox" {
            let msgs = engine.receive(identity.kernel_id).await;

            if msgs.is_empty() {
                println!("Inbox empty");
                continue;
            }

            for m in msgs {
                println!(
                    "[{}] {}",
                    m.sender_id,
                    String::from_utf8_lossy(&m.content)
                );
            }

            continue;
        }

        // ==========================
        // UNKNOWN COMMAND
        // ==========================
        println!("Unknown command");
    }

    println!("CLI terminated.");
}
