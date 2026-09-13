const vscode = require('vscode');
const cp = require('child_process');
const path = require('path');

/**
 * Execute an AOS CLI command in the current workspace.
 * @param {string} commandArgs
 * @returns {Promise<string>}
 */
function runAosCommand(commandArgs) {
  return new Promise((resolve, reject) => {
    const folders = vscode.workspace.workspaceFolders;
    const cwd = folders && folders.length ? folders[0].uri.fsPath : process.cwd();

    cp.exec(`aos ${commandArgs}`, { cwd }, (err, stdout, stderr) => {
      if (err) {
        reject(stderr || stdout || err.message);
      } else {
        resolve(stdout.trim());
      }
    });
  });
}

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  // 1. Status Bar Item
  const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBar.text = '$(shield) AOS: Protected';
  statusBar.tooltip = 'Agent Operating Substrate: Active Guardrails Enforced (Click to open Control Plane)';
  statusBar.command = 'aos.openControlPlane';
  statusBar.show();
  context.subscriptions.push(statusBar);

  // 2. Command: Sync Harnesses
  const cmdSync = vscode.commands.registerCommand('aos.syncHarnesses', async () => {
    try {
      vscode.window.showInformationMessage('AOS: Synchronizing invariants to AI harnesses...');
      const out = await runAosCommand('sync');
      vscode.window.showInformationMessage(`AOS: Synchronized! ${out}`);
    } catch (err) {
      vscode.window.showErrorMessage(`AOS Sync failed: ${err}`);
    }
  });
  context.subscriptions.push(cmdSync);

  // 3. Command: Scan Codebase
  const cmdScan = vscode.commands.registerCommand('aos.scanCodebase', async () => {
    try {
      vscode.window.showInformationMessage('AOS: Scanning codebase conventions...');
      const out = await runAosCommand('ingest --dry-run');
      const action = await vscode.window.showInformationMessage(
        `AOS Scan: Found conventions. Apply tailored guardrails?`,
        'Activate Guardrails',
        'Open Control Plane'
      );
      if (action === 'Activate Guardrails') {
        const applyOut = await runAosCommand('ingest --promote');
        vscode.window.showInformationMessage(`AOS: Guardrails activated! ${applyOut}`);
      } else if (action === 'Open Control Plane') {
        vscode.commands.executeCommand('aos.openControlPlane');
      }
    } catch (err) {
      vscode.window.showErrorMessage(`AOS Ingestion Scan failed: ${err}`);
    }
  });
  context.subscriptions.push(cmdScan);

  // 4. Command: Inspect Current File Guardrails
  const cmdCheck = vscode.commands.registerCommand('aos.checkCurrentFile', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showWarningMessage('AOS: Open a file in editor to inspect its guardrails.');
      return;
    }
    const filePath = vscode.workspace.asRelativePath(editor.document.uri);
    try {
      const out = await runAosCommand(`rules check "${filePath}"`);
      vscode.window.showInformationMessage(`AOS Guardrails for ${filePath}: ${out}`);
    } catch (err) {
      vscode.window.showErrorMessage(`AOS check failed: ${err}`);
    }
  });
  context.subscriptions.push(cmdCheck);

  // 5. Command: Open Control Plane
  const cmdUI = vscode.commands.registerCommand('aos.openControlPlane', () => {
    vscode.env.openExternal(vscode.Uri.parse('http://127.0.0.1:8484'));
  });
  context.subscriptions.push(cmdUI);
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
