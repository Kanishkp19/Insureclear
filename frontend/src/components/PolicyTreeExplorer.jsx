import React, { useMemo, useState } from "react";
import {
  buildExpandedState,
  cleanPolicyText,
  createPolicyTree,
  flattenPolicyTree,
} from "../utils/policyTree";

function TreeNode({ node, level, expanded, onToggle, onSelect, selectedId }) {
  const hasChildren = node.children.length > 0;
  const isExpanded = expanded.has(node.id);
  const isSelected = selectedId === node.id;
  const visibleChildren = hasChildren && isExpanded ? node.children : [];

  return (
    <li className={`tree-branch level-${level}`}>
      <div className={`tree-visual-node ${isSelected ? "selected" : ""}`}>
        <button
          className="tree-node-button"
          type="button"
          onClick={() => onSelect(node.id)}
        >
          <span className="tree-node-circle">{node.id}</span>
          <span className="tree-node-title-wrap">
            <span className="tree-node-title">{node.title}</span>
            {node.pageIndex ? <span className="tree-node-page">Page {node.pageIndex}</span> : null}
          </span>
        </button>

        {hasChildren ? (
          <button className="tree-toggle" type="button" onClick={() => onToggle(node.id)}>
            {isExpanded ? "Collapse" : "Expand"}
          </button>
        ) : null}
      </div>

      {visibleChildren.length > 0 ? (
        <ul className="tree-children-chart">
          {visibleChildren.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              expanded={expanded}
              onToggle={onToggle}
              onSelect={onSelect}
              selectedId={selectedId}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export default function PolicyTreeExplorer({ documentData }) {
  const treeRoot = useMemo(() => createPolicyTree(documentData), [documentData]);
  const allNodes = useMemo(() => flattenPolicyTree(treeRoot), [treeRoot]);
  const [expanded, setExpanded] = useState(() => buildExpandedState(treeRoot, 2));
  const [selectedId, setSelectedId] = useState(treeRoot?.id ?? null);

  const selectedNode = useMemo(
    () => allNodes.find((node) => node.id === selectedId) ?? treeRoot,
    [allNodes, selectedId, treeRoot]
  );

  function handleToggle(nodeId) {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  }

  function handleSelect(nodeId) {
    const node = allNodes.find((item) => item.id === nodeId);
    if (!node) return;

    setSelectedId(nodeId);
    setExpanded((current) => {
      const next = new Set(current);
      node.path.slice(0, -1).forEach((id) => next.add(id));
      return next;
    });
  }

  if (!treeRoot) return null;

  return (
    <section className="page-section tree-page" id="policy-tree">
      <section className="tree-stage">
        <div className="section-head tree-head">
          <div>
            <span className="eyebrow muted">Policy tree</span>
            <h2>Click through the document structure and read the summary for each node.</h2>
          </div>
          <p>
            This tree is generated from your vectorless policy document JSON. Every node opens a
            clause summary or section description from the source file.
          </p>
        </div>

        <div className="tree-layout">
          <div className="tree-panel">
            <div className="tree-panel-header">
              <strong>Document structure</strong>
              <span>{allNodes.length} nodes • click any node</span>
            </div>

            <div className="tree-canvas">
              <ul className="tree-root-chart">
                <TreeNode
                  node={treeRoot}
                  level={0}
                  expanded={expanded}
                  onToggle={handleToggle}
                  onSelect={handleSelect}
                  selectedId={selectedId}
                />
              </ul>
            </div>
          </div>

          <aside className="tree-summary-panel">
            <div className="tree-summary-header">
              <span className="summary-chip">Selected node</span>
              <h3>{selectedNode?.title}</h3>
              <div className="tree-summary-meta">
                <span>Node ID: {selectedNode?.id}</span>
                {selectedNode?.pageIndex ? <span>Page: {selectedNode.pageIndex}</span> : null}
              </div>
            </div>

            <div className="tree-summary-body">
              <pre>{cleanPolicyText(selectedNode?.summary || selectedNode?.text)}</pre>
            </div>
          </aside>
        </div>
      </section>
    </section>
  );
}
