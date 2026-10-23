import { browser } from "wxt/browser";

export default defineContentScript({
  matches: ["*://github.com/*"],
  main() {
    console.log("ASEP Content Script Loaded");

    const checkRepo = () => {
      const url = window.location.href;
      if (url.includes("github.com/")) {
        const match = url.match(/github\.com\/([^\/]+\/[^\/]+)/);
        if (match && match[1]) {
          const repoPath = match[1];
          console.log("ASEP: Detected repository:", repoPath);

          browser.runtime.sendMessage({
            type: "REPO_DETECTED",
            url: `https://github.com/${repoPath}`,
          }).catch(err => {
            // Sidepanel might not be open, which is common
            console.debug("ASEP: Sidepanel not active, message suppressed");
          });
        }
      }
    };

    // Initial check
    checkRepo();

    // Watch for URL changes (GitHub uses Turbo/PJAX for navigation)
    let lastUrl = location.href;
    const observer = new MutationObserver(() => {
      if (location.href !== lastUrl) {
        lastUrl = location.href;
        checkRepo();
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
  },
});
