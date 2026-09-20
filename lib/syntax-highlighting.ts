// Syntax highlighting utilities using Shiki

import { getHighlighter, type Highlighter } from "shiki";

let highlighterInstance: Highlighter | null = null;

/**
 * Get or create the Shiki highlighter instance
 */
async function getHighlighterInstance(): Promise<Highlighter> {
  if (!highlighterInstance) {
    highlighterInstance = await getHighlighter({
      themes: ["github-dark", "github-light"],
      langs: [
        "python",
        "javascript",
        "typescript",
        "jsx",
        "tsx",
        "java",
        "c",
        "cpp",
        "csharp",
        "go",
        "rust",
        "ruby",
        "php",
        "swift",
        "kotlin",
        "scala",
        "bash",
        "sql",
        "html",
        "css",
        "scss",
        "json",
        "yaml",
        "toml",
        "xml",
        "markdown",
        "dockerfile",
        "gitignore",
        "protobuf",
        "graphql",
        "vue",
        "svelte",
        "hcl",
        "makefile",
        "cmake",
        "ini",
        "text",
      ],
    });
  }
  return highlighterInstance;
}

/**
 * Map our language names to Shiki language IDs
 */
function mapLanguageToShiki(language: string): string {
  const langMap: Record<string, string> = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "jsx": "jsx",
    "tsx": "tsx",
    "java": "java",
    "c": "c",
    "cpp": "cpp",
    "csharp": "csharp",
    "go": "go",
    "rust": "rust",
    "ruby": "ruby",
    "php": "php",
    "swift": "swift",
    "kotlin": "kotlin",
    "scala": "scala",
    "bash": "bash",
    "sql": "sql",
    "html": "html",
    "css": "css",
    "scss": "scss",
    "json": "json",
    "yaml": "yaml",
    "toml": "toml",
    "xml": "xml",
    "markdown": "markdown",
    "dockerfile": "dockerfile",
    "gitignore": "gitignore",
    "protobuf": "protobuf",
    "graphql": "graphql",
    "vue": "vue",
    "svelte": "svelte",
    "hcl": "hcl",
    "makefile": "makefile",
    "cmake": "cmake",
    "ini": "ini",
    "text": "text",
  };

  return langMap[language] || "text";
}

/**
 * Highlight code with Shiki
 */
export async function highlightCode(
  code: string,
  language: string,
  theme: "github-dark" | "github-light" = "github-dark"
): Promise<string> {
  const highlighter = await getHighlighterInstance();
  const shikiLang = mapLanguageToShiki(language);

  return highlighter.codeToHtml(code, {
    lang: shikiLang,
    theme,
  });
}

/**
 * Highlight code and return tokens for custom rendering
 */
export async function highlightCodeToTokens(
  code: string,
  language: string,
  theme: "github-dark" | "github-light" = "github-dark"
) {
  const highlighter = await getHighlighterInstance();
  const shikiLang = mapLanguageToShiki(language);

  return highlighter.codeToThemedTokens(code, shikiLang, theme);
}

/**
 * Get language from filename (alias for detectLanguage)
 */
export function getLanguageFromFilename(filename: string): string {
  return detectLanguage(filename) || "text";
}

/**
 * Detect language from file path (re-exported from file-detection for convenience)
 */
function detectLanguage(path: string): string | null {
  const filename = path.split("/").pop() || "";

  const FILENAME_TO_LANGUAGE: Record<string, string> = {
    "Dockerfile": "dockerfile",
    "Makefile": "makefile",
    "makefile": "makefile",
    "CMakeLists.txt": "cmake",
    "Vagrantfile": "ruby",
    "Gemfile": "ruby",
    "Rakefile": "ruby",
    "Guardfile": "ruby",
    "Capfile": "ruby",
    "Podfile": "ruby",
    "Fastfile": "ruby",
    "Appfile": "ruby",
    "Berksfile": "ruby",
    "Thorfile": "ruby",
    "Procfile": "yaml",
    ".gitignore": "gitignore",
    ".gitattributes": "gitignore",
    ".dockerignore": "dockerfile",
    ".editorconfig": "ini",
    ".eslintrc": "json",
    ".prettierrc": "json",
    ".babelrc": "json",
    ".stylelintrc": "json",
    ".remarkrc": "json",
    ".lintstagedrc": "json",
    ".huskyrc": "json",
    ".npmrc": "ini",
    ".yarnrc": "yaml",
    "LICENSE": "text",
    "LICENSE.txt": "text",
    "LICENSE.md": "markdown",
    "README": "markdown",
    "README.txt": "text",
    "README.md": "markdown",
    "CHANGELOG": "markdown",
    "CHANGELOG.md": "markdown",
    "CONTRIBUTING": "markdown",
    "CONTRIBUTING.md": "markdown",
    "AUTHORS": "text",
    "CONTRIBUTORS": "text",
  };

  if (FILENAME_TO_LANGUAGE[filename]) {
    return FILENAME_TO_LANGUAGE[filename];
  }

  const EXTENSION_TO_LANGUAGE: Record<string, string> = {
    ".py": "python",
    ".pyi": "python",
    ".pyx": "python",
    ".pxd": "python",
    ".pxi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".rake": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".fish": "fish",
    ".sql": "sql",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "scss",
    ".less": "less",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".md": "markdown",
    ".markdown": "markdown",
    ".rst": "rst",
    "Dockerfile": "dockerfile",
    ".dockerignore": "dockerfile",
    ".gitignore": "gitignore",
    ".gitattributes": "gitignore",
    ".proto": "protobuf",
    ".graphql": "graphql",
    ".gql": "graphql",
    ".vue": "vue",
    ".svelte": "svelte",
    ".tf": "hcl",
    ".tfvars": "hcl",
  };

  for (const [ext, lang] of Object.entries(EXTENSION_TO_LANGUAGE)) {
    if (filename.endsWith(ext)) {
      return lang;
    }
  }

  return null;
}