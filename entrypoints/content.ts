export default defineContentScript({
  matches: ['*://github.com/*'],
  main() {
    const url = window.location.href;
    if (url.includes('github.com/')) {
      // Extract the repo part: github.com/user/repo
      const match = url.match(/github\.com\/([^\/]+\/[^\/\?#]+)/);
      if (match) {
        const repoUrl = `https://github.com/${match[1]}`;
        console.log('ASEP: Detected repo URL:', repoUrl);

        // Send to the extension
        browser.runtime.sendMessage({
          type: 'REPO_DETECTED',
          url: repoUrl
        });
      }
    }
  },
});
