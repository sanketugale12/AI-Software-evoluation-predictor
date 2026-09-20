const vscode = require('vscode');
const axios = require('axios');

/**
 * This extension connects the VS Code editor to the ASEP Intelligence Backend.
 * It provides real-time engineering intelligence directly in the gutter.
 */
function activate(context) {
    console.log('ASEP Intelligence is now active!');

    // Register the manual analysis command
    let disposable = vscode.commands.registerCommand('asep.analyzeFile', async function () {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('Open a file to analyze it with ASEP');
            return;
        }

        const filePath = editor.document.fileName;
        const config = vscode.workspace.getConfiguration('asep');
        const backendUrl = config.get('backendUrl');

        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "ASEP: Analyzing file...",
            cancellationToken: undefined
        }, async (progress) => {
            try {
                // ponytail: Simple GET request. In V2, we'll use a more robust AnalysisJob flow.
                const response = await axios.get(`${backendUrl}/repositories/current/analyze?path=${encodeURIComponent(filePath)}`);

                vscode.window.showInformationMessage(`ASEP Analysis Complete: ${response.data.summary || 'No critical risks found.'}`);
            } catch (error) {
                vscode.window.showErrorMessage(`ASEP Backend Error: ${error.message}`);
            }
        });
    });

    context.subscriptions.push(disposable);
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};
