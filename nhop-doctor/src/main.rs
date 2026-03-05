mod scanner;
mod analyzer;
mod reporter;
mod fixer;

use clap::Parser;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "nhop-doctor")]
#[command(about = "NHOP Structural Doctor")]
struct Cli {
    #[arg(short, long, default_value = ".")]
    path: PathBuf,

    #[arg(long)]
    dry_run: bool,

    #[arg(long)]
    apply: bool,
}

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    println!("🧠 NHOP Doctor scanning project...\n");

    let metadata = cargo_metadata::MetadataCommand::new()
        .manifest_path(cli.path.join("Cargo.toml"))
        .exec()?;

    let issues = scanner::scan_project(&metadata)?;
    let fixes = analyzer::analyze_issues(&issues)?;

    reporter::print_report(&issues, &fixes, cli.dry_run);

    if cli.apply && !cli.dry_run {
        fixer::apply_fixes(&fixes)?;
    }

    Ok(())
}
