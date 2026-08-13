from pathlib import Path

ROOT = Path('/home/ubuntu/gula-platform')
REPLACEMENTS = {
    'actions/cache@v4': 'actions/cache@0057852bfaa89a56745cba8c7296529d2fc39830',
    'actions/checkout@v4': 'actions/checkout@11d5960a326750d5838078e36cf38b85af677262',
    'actions/dependency-review-action@v4': 'actions/dependency-review-action@2031cfc080254a8a887f58cffee85186f0e49e48',
    'actions/download-artifact@v4': 'actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093',
    'actions/github-script@v7': 'actions/github-script@f28e40c7f34bde8b3046d885e986cb6290c5673b',
    'actions/setup-java@v4': 'actions/setup-java@cf277c60eb25467037889841efdb72551f06f6c3',
    'actions/setup-node@v4': 'actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020',
    'actions/setup-python@v5': 'actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065',
    'actions/upload-artifact@v4': 'actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02',
    'anchore/scan-action@v5': 'anchore/scan-action@869c549e657a088dc0441b08ce4fc0ecdac2bb65',
    'appleboy/telegram-action@1.1.0': 'appleboy/telegram-action@221e6b684967abe813051ee4a37dd61770a83ad3',
    'azure/setup-kubectl@v4': 'azure/setup-kubectl@776406bce94f63e41d621b960d78ee25c8b76ede',
    'docker/login-action@v3': 'docker/login-action@c94ce9fb468520275223c153574b00df6fe4bcc9',
    'github/codeql-action/init@v4': 'github/codeql-action/init@ff2f1c621b7f889edc0d3c761ac2e6a3f8cdb0dd',
    'github/codeql-action/analyze@v4': 'github/codeql-action/analyze@ff2f1c621b7f889edc0d3c761ac2e6a3f8cdb0dd',
    'github/codeql-action/init@v3.28.0': 'github/codeql-action/init@ff2f1c621b7f889edc0d3c761ac2e6a3f8cdb0dd',
    'github/codeql-action/analyze@v3.28.0': 'github/codeql-action/analyze@ff2f1c621b7f889edc0d3c761ac2e6a3f8cdb0dd',
    'github/codeql-action/upload-sarif@v3.28.0': 'github/codeql-action/upload-sarif@ff2f1c621b7f889edc0d3c761ac2e6a3f8cdb0dd',
    'gitleaks/gitleaks-action@v2': 'gitleaks/gitleaks-action@ff98106e4c7b2bc287b24eaf42907196329070c7',
    'gradle/actions/setup-gradle@v4': 'gradle/actions/setup-gradle@748248ddd2a24f49513d8f472f81c3a07d4d50e1',
    'gradle/actions/dependency-submission@v4': 'gradle/actions/dependency-submission@748248ddd2a24f49513d8f472f81c3a07d4d50e1',
    'orhun/git-cliff-action@v2': 'orhun/git-cliff-action@b7913b664658dd091d9971658cb02a19047baa79',
    'ossf/scorecard-action@v2.4.0': 'ossf/scorecard-action@62b2cac7ed8198b15735ed49ab1e5cf35480ba46',
    'reactivecircus/android-emulator-runner@v2': 'reactivecircus/android-emulator-runner@a421e43855164a8197daf9d8d40fe71c6996bb0d',
    'slackapi/slack-github-action@v2': 'slackapi/slack-github-action@91efab103c0de0a537f72a35f6b8cda0ee76bf0a',
    'softprops/action-gh-release@v2': 'softprops/action-gh-release@3bb12739c298aeb8a4eeaf626c5b8d85266b0e65',
    'subosito/flutter-action@v3': 'subosito/flutter-action@1a449444c387b1966244ae4d4f8c696479add0b2',
    'subosito/flutter-action@v2': 'subosito/flutter-action@1a449444c387b1966244ae4d4f8c696479add0b2',
    'treosh/lighthouse-ci-action@v12': 'treosh/lighthouse-ci-action@3e7e23fb74242897f95c0ba9cabad3d0227b9b18',
}

changed = []
for path in sorted(list((ROOT / '.github' / 'workflows').glob('*.yml')) + list((ROOT / '.github' / 'actions').glob('*/action.yml'))):
    text = path.read_text()
    original = text
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    if text != original:
        path.write_text(text)
        changed.append(str(path.relative_to(ROOT)))
print('\n'.join(changed))
