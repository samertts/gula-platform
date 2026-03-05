use cargo_metadata::Metadata;
use std::fs;
use walkdir::WalkDir;

#[derive(Debug, Clone)]
pub enum Issue {
    DuplicateImport {
        file: String,
        import: String,
    },
}

pub fn scan_project(metadata: &Metadata) -> anyhow::Result<Vec<Issue>> {
    let mut issues = Vec::new();

    let src_dir = metadata.workspace_root.join("src");

    for entry in WalkDir::new(src_dir)
        .into_iter()
        .filter_map(|e| e.ok())
    {
        if entry.path().extension().and_then(|s| s.to_str()) == Some("rs") {
            let content = fs::read_to_string(entry.path())?;

            let mut seen = std::collections::HashSet::new();

            for line in content.lines() {
                if line.trim().starts_with("use crate::") {
                    if !seen.insert(line.trim().to_string()) {
                        issues.push(Issue::DuplicateImport {
                            file: entry.path().display().to_string(),
                            import: line.trim().into(),
                        });
                    }
                }
            }
        }
    }

    Ok(issues)
}
