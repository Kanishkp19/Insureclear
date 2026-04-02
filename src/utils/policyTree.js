export function createPolicyTree(raw) {
  const root = raw?.result?.[0];
  if (!root) return null;
  return normalizeNode(root, []);
}

function normalizeNode(node, parentPath) {
  const path = [...parentPath, node.node_id];
  const children = Array.isArray(node.nodes)
    ? node.nodes.map((child) => normalizeNode(child, path))
    : [];

  return {
    id: node.node_id,
    title: node.title || "Untitled node",
    pageIndex: node.page_index ?? null,
    summary: node.summary || node.prefix_summary || node.text || "",
    text: node.text || node.summary || node.prefix_summary || "",
    children,
    path,
  };
}

export function flattenPolicyTree(root) {
  if (!root) return [];
  const items = [];

  function walk(node) {
    items.push(node);
    node.children.forEach(walk);
  }

  walk(root);
  return items;
}

export function buildExpandedState(root, depth = 2) {
  const expanded = new Set();
  if (!root) return expanded;

  function walk(node, level) {
    if (level < depth && node.children.length > 0) {
      expanded.add(node.id);
      node.children.forEach((child) => walk(child, level + 1));
    }
  }

  walk(root, 0);
  return expanded;
}

export function cleanPolicyText(value) {
  if (!value) return "No summary available for this node.";

  return value
    .replace(/!\[[^\]]*\]\([^)]+\)/g, "")
    .replace(/^#+\s*/gm, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/&gt;/g, ">")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}
