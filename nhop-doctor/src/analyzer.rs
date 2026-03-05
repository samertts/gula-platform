use crate::scanner::Issue;

#[derive(Debug, Clone)]
pub struct Fix {
    pub description: String,
    pub file: String,
}

pub fn analyze_issues(issues: &[Issue]) -> anyhow::Result<Vec<Fix>> {
    let mut fixes = Vec::new();

    for issue in issues {
        match issue {
            Issue::DuplicateImport { file, import } => {
                fixes.push(Fix {
                    description: format!("Duplicate import detected: {}", import),
                    file: file.clone(),
                });
            }
        }
    }

    Ok(fixes)
}

