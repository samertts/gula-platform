use colored::*;

/// ===============================
/// Issue Types (from scanner)
/// ===============================
#[derive(Debug, Clone)]
pub enum Issue {
    UnusedImport {
        file: String,
        line: usize,
        import: String,
    },

    DuplicateModule {
        module: String,
        locations: Vec<String>,
    },

    MissingModule {
        parent: String,
        child: String,
    },

    TypeMismatch {
        file: String,
        line: usize,
        expected: String,
        found: String,
    },
}

/// ===============================
/// Fix Suggestions (from analyzer)
/// ===============================
#[derive(Debug, Clone)]
pub struct Fix {
    pub description: String,
    pub file: String,
    pub line: Option<usize>,
    pub replacement: Option<String>,
}

/// ===============================
/// Report Printer
/// ===============================
pub fn print_report(
    issues: &[Issue],
    fixes: &[Fix],
    dry_run: bool,
) {
    println!();
    println!("{}", "🔍 NHOP Doctor — Structural Report"
        .bold()
        .underline()
        .cyan());

    // ---------------------------------
    // Issues
    // ---------------------------------
    if issues.is_empty() {
        println!("{}", "✅ No structural issues detected".green());
    } else {
        println!("\n{}", "Detected Issues:".bold());

        for issue in issues {
            match issue {
                Issue::UnusedImport { file, line, import } => {
                    println!(
                        "{} {}:{} → unused import: {}",
                        "[UNUSED]".yellow(),
                        file,
                        line,
                        import
                    );
                }

                Issue::DuplicateModule { module, locations } => {
                    println!(
                        "{} module '{}' duplicated at {:?}",
                        "[DUPLICATE]".red(),
                        module,
                        locations
                    );
                }

                Issue::MissingModule { parent, child } => {
                    println!(
                        "{} '{}' missing submodule '{}'",
                        "[MISSING]".red(),
                        parent,
                        child
                    );
                }

                Issue::TypeMismatch {
                    file,
                    line,
                    expected,
                    found,
                } => {
                    println!(
                        "{} {}:{} expected '{}' but found '{}'",
                        "[TYPE]".red(),
                        file,
                        line,
                        expected,
                        found
                    );
                }
            }
        }
    }

    // ---------------------------------
    // Fix Suggestions
    // ---------------------------------
    println!();
    println!("{}", "🔧 Suggested Fixes".bold().underline());

    if fixes.is_empty() {
        println!("{}", "No automatic fixes available.".yellow());
    } else {
        for fix in fixes {
            if fix.replacement.is_some() {
                println!(
                    "{} {} ({}:{})",
                    "[AUTO]".green(),
                    fix.description,
                    fix.file,
                    fix.line.unwrap_or(0)
                );
            } else {
                println!(
                    "{} {}",
                    "[MANUAL]".yellow(),
                    fix.description
                );
            }
        }
    }

    // ---------------------------------
    // Dry Run Notice
    // ---------------------------------
    println!();

    if dry_run {
        println!(
            "{}",
            "⚠ Dry run mode — no changes applied"
                .yellow()
                .bold()
        );
    } else {
        println!(
            "{}",
            "💡 Run with --apply to execute automatic fixes"
                .cyan()
        );
    }

    println!();
}
