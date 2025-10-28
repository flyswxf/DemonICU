from io import BytesIO
from typing import Dict, List, Tuple
from pathlib import Path

import json

import matplotlib
matplotlib.use("Agg")  # headless backend
import matplotlib.pyplot as plt
import networkx as nx

from .. import constants as C


def _hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    hex_color = hex_color.strip().lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c * 2 for c in hex_color])
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b)


def _darken(rgb: Tuple[float, float, float], factor: float) -> Tuple[float, float, float]:
    # factor in [0,1], 1 -> darkest
    k = max(0.0, min(1.0, factor))
    return (rgb[0] * (1 - k), rgb[1] * (1 - k), rgb[2] * (1 - k))


def _read_graph(path: Path) -> Tuple[List[Dict], List[Tuple[str, str]]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    nodes = data.get("nodes", [])
    edges_raw = data.get("edges", [])
    edges: List[Tuple[str, str]] = []
    for e in edges_raw:
        if isinstance(e, (list, tuple)) and len(e) == 2:
            edges.append((str(e[0]), str(e[1])))
        elif isinstance(e, dict):
            a = e.get("from")
            b = e.get("to")
            if a is not None and b is not None:
                edges.append((str(a), str(b)))
    return nodes, edges


def generate_graph_image(
    bg_color: str = "#0b1220",
    accent: str = "#49b2ff",
    width: int = 960,
    height: int = 540,
) -> BytesIO:
    """Read graph JSON and render a PNG aligned with frontend theme.

    - Node size determined by degree (min 300, max 1200)
    - Node color darkens with size (larger -> darker)
    - Background matches app theme
    """
    nodes, edges = _read_graph(C.GRAPH_JSON_PATH)

    G = nx.Graph()
    importance_map: Dict[str, int] = {}
    for n in nodes:
        nid = str(n.get("id"))
        name = n.get("name") or nid
        imp = n.get("importance", 1)
        try:
            imp = int(imp)
        except Exception:
            imp = 1
        if imp < 1:
            imp = 1
        importance_map[nid] = imp
        G.add_node(nid, label=name)
    for a, b in edges:
        if a in G.nodes and b in G.nodes:
            G.add_edge(a, b)

    # layout
    pos = nx.spring_layout(G, seed=42)

    # Node size and color driven by importance from JSON
    if importance_map:
        min_imp = min(importance_map.values())
        max_imp = max(importance_map.values())
    else:
        min_imp = 1
        max_imp = 1
    def size_for(n: str) -> float:
        imp = importance_map.get(n, 1)
        if max_imp == min_imp:
            return 600.0
        # scale 300-1200 by importance
        return 300.0 + (imp - min_imp) * (1200.0 - 300.0) / (max_imp - min_imp)

    # colors from accent, darker if larger
    accent_rgb = _hex_to_rgb(accent)
    node_sizes = [size_for(n) for n in G.nodes]
    size_min = min(node_sizes) if node_sizes else 300.0
    size_max = max(node_sizes) if node_sizes else 1200.0
    node_colors = []
    for n, s in zip(G.nodes, node_sizes):
        # normalize importance to [0,1]
        imp = importance_map.get(n, 1)
        if max_imp == min_imp:
            k = 0.3
        else:
            k = (imp - min_imp) / (max_imp - min_imp)
        # slightly more contrast: larger importance -> darker
        k = 0.25 + 0.6 * k
        node_colors.append(_darken(accent_rgb, k))

    # figure
    dpi = 100
    fig_w = width / dpi
    fig_h = height / dpi
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    ax.set_facecolor(bg_color)
    fig.patch.set_facecolor(bg_color)
    ax.axis("off")

    # draw edges (semi-transparent accent)
    edge_color = (*accent_rgb, 0.35)
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_color, width=2.0)

    # draw nodes
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_sizes, node_color=node_colors)

    # labels
    labels = {n: G.nodes[n].get("label", n) for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=10, font_color="#e7efff")

    buf = BytesIO()
    plt.tight_layout(pad=0.5)
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf