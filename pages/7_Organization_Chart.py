"""
Page 7: Organization Chart
Visual hierarchy of WP29, Groups, and Task Forces
"""
import streamlit as st
from supabase_client import SupabaseClient
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Organization Chart", page_icon="📊", layout="wide")

from auth_utils import require_auth
require_auth()

st.title("📊 Organization Chart")

# ============================================================================
# DATA & LOGIC
# ============================================================================

try:
    groups = SupabaseClient.get_all_groups()
    
    # 1. Build Hierarchy Tree from DB Data
    # ------------------------------------------------
    # Organize data by ID for easy access
    groups_by_id = {g['id']: g for g in groups}
    
    # Map parents to children
    children_map = {} 
    roots = []
    
    for g in groups:
        pid = g.get('parent_group_id')
        if pid:
            if pid not in children_map:
                children_map[pid] = []
            children_map[pid].append(g['id'])
        else:
            roots.append(g['id'])
            
    # Remove WP29 from roots list if it exists to treat it as THE root
    # If there are multiple roots (e.g. WP29 and some orphan), pull them under a meta-root or just assume WP29 is main
    potential_root = 'WP29'
    if potential_root in roots:
        # WP29 is our start node
        start_node = potential_root
    else:
        # Fallback if WP29 not found in DB or strange structure
        start_node = roots[0] if roots else None

    if not start_node:
        st.warning("No hierarchy found.")
        st.stop()
        
    # Sort children for consistent layout
    for k in children_map:
        children_map[k].sort()

    # 2. Layout Algorithm (Safe Recursion)
    # ------------------------------------------------
    node_coords = {} # id -> (x, y)
    width_cache = {}
    
    def calculate_subtree_width(node_id, visited=None):
        """Calculate width needed for a node based on children"""
        if visited is None: visited = set()
        if node_id in visited: return 1
        visited.add(node_id)
        
        if node_id in width_cache: return width_cache[node_id]
            
        children = children_map.get(node_id, [])
        if not children:
            width_cache[node_id] = 1
            return 1 
        
        width = 0
        for child in children:
            width += calculate_subtree_width(child, visited.copy())
            
        width_cache[node_id] = width
        return width
        
    def assign_coords(node_id, x_start, depth, visited=None):
        """Assign coordinates recursively"""
        if visited is None: visited = set()
        if node_id in visited: return
        visited.add(node_id)
        
        children = children_map.get(node_id, [])
        
        # Calculate my X position
        my_width = calculate_subtree_width(node_id) 
        my_x = x_start + (my_width / 2)
        node_coords[node_id] = (my_x, depth)
        
        # Assign children
        current_x = x_start
        for child in children:
            child_width = calculate_subtree_width(child)
            assign_coords(child, current_x, depth - 1, visited.copy())
            current_x += child_width

    # -- Calculate layout --
    assign_coords(start_node, 0, 0)
    
    # 3. Create Visualization Data
    # ------------------------------------------------
    x_nodes = []
    y_nodes = []
    text_nodes = []
    ids_nodes = []
    color_nodes = []
    
    edge_x = []
    edge_y = []
    
    import math
    if not node_coords:
        st.error("Could not calculate layout.")
        st.stop()

    max_depth = min(y for _, y in node_coords.values())
    min_x = min(x for x, _ in node_coords.values())
    max_x = max(x for x, _ in node_coords.values())
    
    for nid, (nx, ny) in node_coords.items():
        # Node info
        x_nodes.append(nx)
        y_nodes.append(ny)
        ids_nodes.append(nid)
        
        # Label and color
        if nid == 'WP29':
            text_nodes.append("<b>WP.29</b>")
            color_nodes.append('#667eea') # Purple
        elif nid in groups_by_id and not groups_by_id[nid].get('parent_group_id'):
             # Root level but not WP29? Or direct children of WP29?
             # Actually check relationship:
             pp = groups_by_id[nid].get('parent_group_id')
             if pp == 'WP29' or nid == start_node:
                 if nid != start_node:
                     color_nodes.append('#f093fb') # Pink (Groups)
                 else:
                     color_nodes.append('#667eea') # Root
                 text_nodes.append(f"<b>{nid}</b>")
        else:
            # TFs / Children
            text_nodes.append(nid.replace('TF ', 'TF<br>')) 
            color_nodes.append('#4facfe') # Blue
        
        # Ensure color is set if missed
        if len(color_nodes) < len(x_nodes):
            color_nodes.append('#4facfe')

        # Edges (connect to parent)
        # Find who is my parent from DB data directly
        parent = groups_by_id[nid].get('parent_group_id')
        
        if parent and parent in node_coords:
            px, py = node_coords[parent]
            mid_y = (py + ny) / 2
            edge_x.extend([px, px, nx, nx, None])
            edge_y.extend([py, mid_y, mid_y, ny, None])

    # 4. Draw with Plotly
    # ------------------------------------------------
    
    # Edges
    trace_edges = go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(color='#888', width=2),
        hoverinfo='none'
    )
    
    # Nodes
    trace_nodes = go.Scatter(
        x=x_nodes, y=y_nodes,
        mode='markers+text',
        text=text_nodes,
        textposition="middle center",
        marker=dict(
            symbol='square',
            size=60, 
            color=color_nodes,
            line=dict(color='white', width=1)
        ),
        hoverinfo='text',
        hovertext=[groups_by_id[Id].get('description', Id) for Id in ids_nodes],
        customdata=ids_nodes 
    )
    
    layout = go.Layout(
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[min_x-1, max_x+1]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[max_depth-0.5, 0.5]),
        height=600,
        margin=dict(l=20, r=20, t=20, b=20),
        clickmode='event+select',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    fig = go.Figure(data=[trace_edges, trace_nodes], layout=layout)
    
    # 5. Render & Handle Click
    # ------------------------------------------------
    
    st.markdown("### 🏛️ Interactive Hierarchy")
    st.info("👆 Click on a box to view its documents")
    
    selection = st.plotly_chart(fig, use_container_width=True, on_select="rerun")
    
    # 6. Navigation Logic
    if selection and selection.selection and selection.selection['points']:
        point = selection.selection['points'][0]
        selected_id = point['customdata']
        
        # Navigate for ANY selection
        st.session_state['filter_group'] = selected_id if selected_id != 'WP29' else 'All'
        st.switch_page("pages/4_Search_Session.py")

except Exception as e:
    st.error(f"Error building hierarchy: {e}")
    import traceback
    st.code(traceback.format_exc())
