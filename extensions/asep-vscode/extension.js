const vscode = require('vscode');
const axios = require('axios');

/**
 * This extension connects the VS Code editor to the ASEP Intelligence Backend.
 * It provides real-time engineering intelligence directly in the gutter.
 */
function activate(context) {
    console.log('ASEP Intelligence is now active!');

    const diagnosticCollection = vscode.languages.createDiagnosticCollection('asep');
    let deepDivePanel = undefined;

    async function updateDiagnostics(document) {
        const config = vscode.workspace.getConfiguration('asep');
        const backendUrl = config.get('backendUrl');
        const filePath = document.fileName;

        try {
            const response = await axios.get(`${backendUrl}/repositories/current/analyze?path=${encodeURIComponent(filePath)}`);
            const findings = response.data.findings || [];

            const diagnostics = findings.map(f => {
                const range = new vscode.Range(f.line - 1, f.column - 1, f.line - 1, f.column + 10);
                const severity = {
                    'Error': vscode.DiagnosticSeverity.Error,
                    'Warning': vscode.DiagnosticSeverity.Warning,
                    'Information': vscode.DiagnosticSeverity.Information,
                }[f.severity] || vscode.DiagnosticSeverity.Information;

                return new vscode.Diagnostic(range, f.message, severity);
            });

            diagnosticCollection.set(document.uri, diagnostics);
        } catch (error) {
            console.error(`ASEP Diagnostics Error: ${error.message}`);
        }
    }

    async function showDeepDive(findingId) {
        const config = vscode.workspace.getConfiguration('asep');
        const backendUrl = config.get('backendUrl');

        try {
            const response = await axios.get(`${backendUrl}/repositories/current/analyze/finding?id=${findingId}`);
            const data = response.data;

            if (deepDivePanel) {
                deepDivePanel.webview.html = getWebviewContent(data);
                deepDivePanel.reveal(vscode.ViewColumn.Two);
            } else {
                deepDivePanel = vscode.window.createWebviewPanel(
                    'asepDeepDive',
                    'ASEP Deep Dive Analysis',
                    vscode.ViewColumn.Two,
                    { enableScripts: true }
                );
                deepDivePanel.webview.html = getWebviewContent(data);
                deepDivePanel.onDidDispose(() => { deepDivePanel = undefined; });
            }
        } catch (error) {
            vscode.window.showErrorMessage(`ASEP Deep Dive Error: ${error.message}`);
        }
    }

    function getWebviewContent(data) {
        return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: var(--vscode-font-family, sans-serif);
                    color: var(--vscode-editor-foreground);
                    background-color: var(--vscode-editor-background);
                    padding: 20px;
                    line-height: 1.6;
                }
                .header { border-bottom: 1px solid var(--vscode-panel-border); margin-bottom: 20px; padding-bottom: 10px; }
                .section { margin-bottom: 20px; }
                .label { font-weight: bold; color: var(--vscode-descriptionForeground); display: block; margin-bottom: 5px; }
                .content { background: var(--vscode-editor-inactiveSelectionBackground); padding: 10px; border-radius: 4px; }
                .fix-block {
                    font-family: monospace;
                    background: var(--vscode-editor-background);
                    border: 1px solid var(--vscode-panel-border);
                    padding: 10px;
                    white-space: pre-wrap;
                    display: block;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Deep Dive Analysis</h1>
            </div>
            <div class="section">
                <span class="label">Reasoning</span>
                <div class="content">${data.reasoning}</div>
            </div>
            <div class="section">
                <span class="label">Impact</span>
                <div class="content">${data.impact}</div>
            </div>
            <div class="section">
                <span class="label">Suggested Fix</span>
                <div class="fix-block">${data.suggestedFix}</div>
            </div>
        </body>
        </html>`;
    }

    // CodeLens Provider
    class DeepDiveCodeLensProvider {
        async provideCodeLenses(document) {
            const config = vscode.workspace.getConfiguration('asep');
            const backendUrl = config.get('backendUrl');

            try {
                const response = await axios.get(`${backendUrl}/repositories/current/analyze?path=${encodeURIComponent(document.fileName)}`);
                const findings = response.data.findings || [];

                const lenses = [];
                findings.forEach(f => {
                    const range = new vscode.Range(f.line - 1, 0, f.line - 1, 0);
                    lenses.push(new vscode.CodeLens([
                        {
                            title: "🔍 Deep Dive Analysis",
                            command: "asep.deepDive",
                            arguments: [f.id]
                        }
                    ], range));
                });
                return lenses;
            } catch (e) {
                return [];
            }
        }
    }

    context.subscriptions.push(
        vscode.languages.registerCodeLensProvider({ language: 'javascript', scheme: 'file' }, new DeepDiveCodeLensProvider()),
        vscode.languages.registerCodeLensProvider({ language: 'typescript', scheme: 'file' }, new DeepDiveCodeLensProvider()),
        vscode.languages.registerCodeLensProvider({ language: 'python', scheme: 'file' }, new DeepDiveCodeLensProvider()),
        vscode.workspace.onDidOpenTextDocument(doc => updateDiagnostics(doc)),
        vscode.workspace.onDidSaveTextDocument(doc => updateDiagnostics(doc))
    );

    // Register the manual analysis command
    let disposable = vscode.commands.registerCommand('asep.analyzeFile', async function () {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('Open a file to analyze it with ASEP');
            return;
        }

        const document = editor.document;
        await updateDiagnostics(document);
        vscode.window.showInformationMessage('ASEP: Analysis updated in the editor gutter.');
    });

    let deepDiveDisposable = vscode.commands.registerCommand('asep.deepDive', async function (findingId) {
        await showDeepDive(findingId);
    });

    context.subscriptions.push(disposable, deepDiveDisposable, diagnosticCollection);
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};