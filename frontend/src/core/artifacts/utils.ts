import { getBackendBaseURL } from "../config";
import { isStaticWebsiteOnly } from "../static-mode";
import type { AgentThread } from "../threads";

const USER_DATA_ARTIFACT_PREFIX = "/mnt/user-data";
const PRESENTABLE_ARTIFACT_PREFIX = "/mnt/user-data/outputs/";

export function normalizeArtifactFilepath(filepath: unknown) {
  if (typeof filepath !== "string") {
    return null;
  }
  const trimmed = filepath.trim();
  if (!trimmed) {
    return null;
  }

  const normalized = trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
  if (
    normalized !== USER_DATA_ARTIFACT_PREFIX &&
    !normalized.startsWith(`${USER_DATA_ARTIFACT_PREFIX}/`)
  ) {
    return null;
  }

  return normalized;
}

export function isPresentableArtifactFilepath(filepath: string) {
  return normalizeArtifactFilepath(filepath)?.startsWith(
    PRESENTABLE_ARTIFACT_PREFIX,
  );
}

function artifactFilepathForURL(filepath: string) {
  const normalized = normalizeArtifactFilepath(filepath);
  if (!normalized) {
    return null;
  }
  return normalized.split("/").map(encodeURIComponent).join("/");
}

export function urlOfArtifact({
  filepath,
  threadId,
  download = false,
  isMock = false,
}: {
  filepath: string;
  threadId: string;
  download?: boolean;
  isMock?: boolean;
}) {
  if (isStaticWebsiteOnly()) {
    return staticDemoArtifactURL({ filepath, threadId, download });
  }
  const encodedFilepath = artifactFilepathForURL(filepath);
  if (!encodedFilepath) {
    return "about:blank";
  }
  if (isMock) {
    return `${getBackendBaseURL()}/mock/api/threads/${threadId}/artifacts${encodedFilepath}${download ? "?download=true" : ""}`;
  }
  return `${getBackendBaseURL()}/api/threads/${threadId}/artifacts${encodedFilepath}${download ? "?download=true" : ""}`;
}

export function extractArtifactsFromThread(thread: AgentThread) {
  return thread.values.artifacts ?? [];
}

export function resolveArtifactURL(absolutePath: string, threadId: string) {
  if (isStaticWebsiteOnly()) {
    return staticDemoArtifactURL({ filepath: absolutePath, threadId });
  }
  const encodedFilepath = artifactFilepathForURL(absolutePath);
  if (!encodedFilepath) {
    return "about:blank";
  }
  return `${getBackendBaseURL()}/api/threads/${threadId}/artifacts${encodedFilepath}`;
}

function staticDemoArtifactURL({
  filepath,
  threadId,
  download = false,
}: {
  filepath: string;
  threadId: string;
  download?: boolean;
}) {
  const normalized = normalizeArtifactFilepath(filepath);
  if (!normalized) {
    return "about:blank";
  }
  const demoPath = normalized.replace(/^\/mnt\//, "/");
  return `${getBackendBaseURL()}/demo/threads/${threadId}${demoPath}${download ? "?download=true" : ""}`;
}
