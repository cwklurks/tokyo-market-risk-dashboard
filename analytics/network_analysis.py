"""
Network Analysis Engine for Tokyo Market Risk Dashboard
Provides graph-based analysis of interconnected risks
"""

import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple, Optional
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

class NetworkAnalysisEngine:
    """
    Advanced network analysis for systemic risk detection
    """
    
    def __init__(self):
        self.risk_network = nx.Graph()
        self.entity_types = {
            'market': {'color': '#4ECDC4', 'size': 30},
            'earthquake': {'color': '#FF6B6B', 'size': 25},
            'sector': {'color': '#45B7D1', 'size': 20},
            'currency': {'color': '#96CEB4', 'size': 20},
            'external': {'color': '#DDA0DD', 'size': 15}
        }
        
    def build_risk_network(self, market_data: Dict, earthquake_data: List, 
                          correlation_matrix: pd.DataFrame) -> nx.Graph:
        """Build comprehensive risk network graph"""
        
        # Clear existing network
        self.risk_network.clear()
        
        # Add market nodes
        for market, data in market_data.items():
            if data:
                self.risk_network.add_node(
                    market,
                    node_type='market',
                    volatility=data.get('volatility', 0.2),
                    price=data.get('current_price', 0),
                    change_pct=data.get('change_percent', 0)
                )
        
        # Add earthquake risk nodes
        if earthquake_data:
            for i, eq in enumerate(earthquake_data[:5]):  # Top 5 recent earthquakes
                magnitude = eq.get('magnitude', 0)
                location = eq.get('location', 'Unknown')
                # Create meaningful node name based on magnitude and location
                if magnitude >= 6.0:
                    node_id = f"Major Quake M{magnitude:.1f}"
                elif magnitude >= 5.0:
                    node_id = f"Strong Quake M{magnitude:.1f}"
                else:
                    node_id = f"Moderate Quake M{magnitude:.1f}"
                
                # If location is available, add it to the name
                if location and location != 'Unknown':
                    # Shorten location name for display
                    short_location = location.split(',')[0] if ',' in location else location
                    if len(short_location) > 15:
                        short_location = short_location[:15] + '...'
                    node_id = f"{node_id} ({short_location})"
                
                self.risk_network.add_node(
                    node_id,
                    node_type='earthquake',
                    magnitude=magnitude,
                    distance=eq.get('distance_from_tokyo', 100),
                    time=eq.get('time', ''),
                    location=location
                )
                
                # Connect earthquakes to affected markets
                if eq.get('magnitude', 0) > 5.0:
                    # Strong earthquakes affect all markets
                    for market in market_data.keys():
                        weight = 1.0 / (1.0 + eq.get('distance_from_tokyo', 100) / 100)
                        self.risk_network.add_edge(node_id, market, weight=weight)
        
        # Add sector nodes
        sectors = ['real_estate', 'insurance', 'utilities', 'construction', 'tourism']
        for sector in sectors:
            self.risk_network.add_node(
                sector,
                node_type='sector',
                risk_exposure=np.random.uniform(0.3, 0.8)  # Simulated
            )
            
            # Connect sectors to markets
            if 'nikkei' in market_data:
                weight = np.random.uniform(0.4, 0.7)
                self.risk_network.add_edge(sector, 'nikkei', weight=weight)
        
        # Add currency nodes
        currencies = ['usd', 'eur', 'cny']
        for currency in currencies:
            self.risk_network.add_node(
                currency,
                node_type='currency',
                correlation=np.random.uniform(-0.5, 0.5)  # Simulated
            )
            
            # Connect to JPY
            if 'jpy_usd' in market_data:
                weight = abs(np.random.uniform(-0.6, 0.6))
                self.risk_network.add_edge(currency, 'jpy_usd', weight=weight)
        
        # Add correlations from matrix
        if not correlation_matrix.empty:
            for i in range(len(correlation_matrix)):
                for j in range(i+1, len(correlation_matrix)):
                    source = correlation_matrix.index[i]
                    target = correlation_matrix.columns[j]
                    corr = correlation_matrix.iloc[i, j]
                    if abs(corr) > 0.3:  # Only significant correlations
                        self.risk_network.add_edge(source, target, weight=abs(corr))
        
        return self.risk_network
    
    def detect_risk_clusters(self) -> List[List[str]]:
        """Detect clusters of interconnected risks"""
        
        # Find communities in the network
        communities = list(nx.community.greedy_modularity_communities(self.risk_network))
        
        # Analyze each cluster
        risk_clusters = []
        for community in communities:
            cluster = list(community)
            
            # Calculate cluster risk score
            risk_score = 0
            for node in cluster:
                node_data = self.risk_network.nodes[node]
                if node_data.get('node_type') == 'earthquake':
                    risk_score += node_data.get('magnitude', 0) / 10
                elif node_data.get('node_type') == 'market':
                    risk_score += node_data.get('volatility', 0)
                elif node_data.get('node_type') == 'sector':
                    risk_score += node_data.get('risk_exposure', 0)
            
            if risk_score > 0.5:  # Significant risk cluster
                risk_clusters.append({
                    'nodes': cluster,
                    'risk_score': risk_score,
                    'size': len(cluster)
                })
        
        return risk_clusters
    
    def calculate_systemic_risk_score(self) -> Dict:
        """Calculate overall systemic risk based on network topology"""
        
        # Network metrics
        density = nx.density(self.risk_network)
        
        # Average clustering coefficient
        avg_clustering = nx.average_clustering(self.risk_network)
        
        # Centrality measures
        degree_centrality = nx.degree_centrality(self.risk_network)
        betweenness_centrality = nx.betweenness_centrality(self.risk_network)
        
        # Find most critical nodes
        critical_nodes = sorted(
            degree_centrality.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # Calculate systemic risk score
        systemic_score = (
            density * 0.3 +  # Network interconnectedness
            avg_clustering * 0.3 +  # Local clustering
            max(degree_centrality.values()) * 0.4  # Most connected node
        )
        
        return {
            'systemic_risk_score': systemic_score,
            'network_density': density,
            'avg_clustering': avg_clustering,
            'critical_nodes': critical_nodes,
            'risk_level': self._get_risk_level(systemic_score)
        }
    
    def find_contagion_paths(self, source_node: str, impact_threshold: float = 0.3) -> List[List[str]]:
        """Find potential contagion paths from a source of risk"""
        
        if source_node not in self.risk_network:
            return []
        
        # Use BFS to find paths weighted by edge strength
        contagion_paths = []
        
        # Get all simple paths up to length 4
        for target in self.risk_network.nodes():
            if target != source_node:
                try:
                    paths = list(nx.all_simple_paths(
                        self.risk_network, 
                        source_node, 
                        target, 
                        cutoff=4
                    ))
                    
                    for path in paths:
                        # Calculate path impact
                        path_impact = 1.0
                        for i in range(len(path) - 1):
                            edge_data = self.risk_network.get_edge_data(path[i], path[i+1])
                            path_impact *= edge_data.get('weight', 0.5)
                        
                        if path_impact >= impact_threshold:
                            contagion_paths.append({
                                'path': path,
                                'impact': path_impact,
                                'length': len(path)
                            })
                except nx.NetworkXNoPath:
                    continue
        
        # Sort by impact
        contagion_paths.sort(key=lambda x: x['impact'], reverse=True)
        
        return contagion_paths[:10]  # Top 10 paths
    
    def generate_network_visualization(self) -> go.Figure:
        """Generate interactive network visualization using Plotly"""
        
        # Calculate layout
        pos = nx.spring_layout(self.risk_network, k=2, iterations=50)
        
        # Create edge traces
        edge_traces = []
        for edge in self.risk_network.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            weight = edge[2].get('weight', 0.5)
            
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(
                    width=weight * 3,
                    color='rgba(125,125,125,0.5)'
                ),
                hoverinfo='none'
            )
            edge_traces.append(edge_trace)
        
        # Create node traces by type
        node_traces = []
        for node_type, style in self.entity_types.items():
            node_list = [node for node, data in self.risk_network.nodes(data=True) 
                        if data.get('node_type') == node_type]
            
            if not node_list:
                continue
                
            x_nodes = []
            y_nodes = []
            hover_text = []
            
            for node in node_list:
                x, y = pos[node]
                x_nodes.append(x)
                y_nodes.append(y)
                
                # Create hover text
                node_data = self.risk_network.nodes[node]
                if node_type == 'earthquake':
                    location = node_data.get('location', 'Unknown')
                    magnitude = node_data.get('magnitude', 0)
                    distance = node_data.get('distance', 0)
                    time = node_data.get('time', '')
                    text = f"<b>Earthquake Event</b><br>Magnitude: M{magnitude:.1f}<br>Location: {location}<br>Distance from Tokyo: {distance:.0f}km<br>Time: {time}"
                elif node_type == 'market':
                    volatility = node_data.get('volatility', 0)
                    change_pct = node_data.get('change_pct', 0)
                    price = node_data.get('price', 0)
                    text = f"<b>{node.upper()} Market</b><br>Current Price: {price:.2f}<br>Volatility: {volatility:.2%}<br>Change: {change_pct:+.2f}%"
                elif node_type == 'sector':
                    risk_exposure = node_data.get('risk_exposure', 0)
                    text = f"<b>{node.replace('_', ' ').title()} Sector</b><br>Risk Exposure: {risk_exposure:.1%}"
                elif node_type == 'currency':
                    correlation = node_data.get('correlation', 0)
                    text = f"<b>{node.upper()} Currency</b><br>JPY Correlation: {correlation:+.2f}"
                else:
                    text = f"<b>{node.replace('_', ' ').title()}</b><br>Type: {node_type.title()}"
                
                hover_text.append(text)
            
            node_trace = go.Scatter(
                x=x_nodes,
                y=y_nodes,
                mode='markers+text',
                marker=dict(
                    size=style['size'],
                    color=style['color'],
                    line=dict(width=2, color='white')
                ),
                text=[node for node in node_list],
                textposition="top center",
                hovertext=hover_text,
                hoverinfo='text',
                name=node_type.capitalize()
            )
            node_traces.append(node_trace)
        
        # Create figure
        fig = go.Figure(data=edge_traces + node_traces)
        
        fig.update_layout(
            title="Risk Network Topology",
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20, l=20, r=20, t=60),
            xaxis=dict(
                showgrid=False, 
                zeroline=False, 
                showticklabels=False,
                scaleanchor="y",
                scaleratio=1
            ),
            yaxis=dict(
                showgrid=False, 
                zeroline=False, 
                showticklabels=False
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=600,
            autosize=True,
            dragmode='zoom'
        )
        
        return fig
    
    def _get_risk_level(self, score: float) -> str:
        """Convert risk score to risk level"""
        if score >= 0.7:
            return 'CRITICAL'
        elif score >= 0.5:
            return 'HIGH'
        elif score >= 0.3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def detect_anomalies(self) -> List[Dict]:
        """Detect anomalous patterns in the risk network"""
        
        anomalies = []
        
        # Check for unusual degree centrality
        degree_centrality = nx.degree_centrality(self.risk_network)
        mean_centrality = np.mean(list(degree_centrality.values()))
        std_centrality = np.std(list(degree_centrality.values()))
        
        for node, centrality in degree_centrality.items():
            if centrality > mean_centrality + 2 * std_centrality:
                anomalies.append({
                    'type': 'high_centrality',
                    'node': node,
                    'severity': 'HIGH',
                    'description': f'{node} has unusually high connectivity',
                    'metric': centrality
                })
        
        # Check for isolated clusters
        components = list(nx.connected_components(self.risk_network))
        if len(components) > 1:
            for comp in components[1:]:  # Skip the main component
                anomalies.append({
                    'type': 'isolated_cluster',
                    'nodes': list(comp),
                    'severity': 'MEDIUM',
                    'description': f'Isolated risk cluster detected with {len(comp)} nodes',
                    'metric': len(comp)
                })
        
        return anomalies 