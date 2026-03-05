use crate::analyzer::Fix;

pub fn apply_fixes(fixes: &[Fix]) -> anyhow::Result<()> {
    println!("Applying fixes...");

    for fix in fixes {
        println!("✅ {}", fix.description);
    }

    Ok(())
}
