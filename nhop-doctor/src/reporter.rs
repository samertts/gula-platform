use colored::*;
use crate::scanner::Issue;
use crate::analyzer::Fix;

pub fn print_report(issues: &[Issue], fixes: &[Fix], dry_run: bool) {
    println!("{}", "🔍 NHOP Doctor Report".bold());

    if issues.is_empty() {
        println!("{}", "✅ No structural problems found".green());
        return;
    }

    println!("\nProblems:");

    for issue in issues {
        println!("{:?}", issue);
    }

    println!("\nSuggested fixes:");

    for fix in fixes {
        println!("🛠 {}", fix.description.cyan());
    }

    if dry_run {
        println!("\n⚠ Dry run mode — no changes applied".yellow());
    }
}
