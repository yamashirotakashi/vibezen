"""
Traceability visualizer for generating visual representations of the traceability matrix.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

from vibezen.traceability.models import (
    TraceabilityMatrix,
    TraceLinkType,
    TraceabilityStatus,
)
from vibezen.traceability.analyzer import TraceabilityAnalyzer, CoverageReport


class TraceabilityVisualizer:
    """Generates visual representations of traceability data."""
    
    def __init__(self, matrix: TraceabilityMatrix):
        """Initialize visualizer with a traceability matrix."""
        self.matrix = matrix
        self.analyzer = TraceabilityAnalyzer(matrix)
    
    def generate_mermaid_diagram(self) -> str:
        """Generate a Mermaid diagram of the traceability relationships."""
        lines = ["graph TD"]
        
        # Add specification nodes
        for spec_id, spec in self.matrix.specifications.items():
            label = f"{spec.requirement_id}\\n{spec.name[:30]}..."
            style = self._get_node_style(spec.status, "spec")
            lines.append(f'    S{spec_id}["{label}"] {style}')
        
        # Add implementation nodes
        for impl_id, impl in self.matrix.implementations.items():
            label = f"{impl.name}\\n{impl.get_location()}"
            style = self._get_node_style(impl.status, "impl")
            lines.append(f'    I{impl_id}["{label}"] {style}')
        
        # Add test nodes
        for test_id, test in self.matrix.tests.items():
            label = f"{test.name}\\n{test.test_type}"
            style = self._get_node_style(test.status, "test")
            lines.append(f'    T{test_id}["{label}"] {style}')
        
        # Add links
        for link in self.matrix.links.values():
            source_prefix = self._get_node_prefix(link.source_id)
            target_prefix = self._get_node_prefix(link.target_id)
            
            if source_prefix and target_prefix:
                arrow_style = self._get_arrow_style(link.link_type)
                label = f"{link.link_type.value} ({link.confidence:.2f})"
                lines.append(f'    {source_prefix}{link.source_id} {arrow_style}|{label}| {target_prefix}{link.target_id}')
        
        # Add legend
        lines.extend([
            "",
            "    %% Legend",
            "    subgraph Legend",
            '        LS[Specification]:::spec',
            '        LI[Implementation]:::impl',
            '        LT[Test]:::test',
            "    end",
            "",
            "    %% Styles",
            "    classDef spec fill:#e1f5fe,stroke:#01579b,stroke-width:2px",
            "    classDef impl fill:#f3e5f5,stroke:#4a148c,stroke-width:2px", 
            "    classDef test fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px",
            "    classDef verified fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px",
            "    classDef failed fill:#ffcdd2,stroke:#c62828,stroke-width:3px",
            "    classDef notstarted fill:#f5f5f5,stroke:#616161,stroke-width:2px",
        ])
        
        return "\n".join(lines)
    
    def generate_coverage_heatmap(self) -> Dict[str, Any]:
        """Generate data for a coverage heatmap visualization."""
        report = self.analyzer.generate_coverage_report()
        
        # Create grid data
        spec_ids = list(self.matrix.specifications.keys())
        impl_ids = list(self.matrix.implementations.keys())
        test_ids = list(self.matrix.tests.keys())
        
        # Spec-Impl coverage matrix
        spec_impl_matrix = []
        for spec_id in spec_ids:
            row = []
            for impl_id in impl_ids:
                # Check if implementation implements specification
                implements = False
                for link in self.matrix.get_links_from(spec_id):
                    if link.target_id == impl_id and link.link_type == TraceLinkType.IMPLEMENTS:
                        implements = True
                        break
                row.append(1 if implements else 0)
            spec_impl_matrix.append(row)
        
        # Impl-Test coverage matrix
        impl_test_matrix = []
        for impl_id in impl_ids:
            row = []
            for test_id in test_ids:
                # Check if test tests implementation
                tests = False
                for link in self.matrix.get_links_from(test_id):
                    if link.target_id == impl_id and link.link_type == TraceLinkType.TESTS:
                        tests = True
                        break
                row.append(1 if tests else 0)
            impl_test_matrix.append(row)
        
        return {
            "spec_impl_coverage": {
                "matrix": spec_impl_matrix,
                "row_labels": [self.matrix.specifications[sid].requirement_id for sid in spec_ids],
                "col_labels": [self.matrix.implementations[iid].name for iid in impl_ids],
                "coverage_percentage": report.specification_coverage,
            },
            "impl_test_coverage": {
                "matrix": impl_test_matrix,
                "row_labels": [self.matrix.implementations[iid].name for iid in impl_ids],
                "col_labels": [self.matrix.tests[tid].name for tid in test_ids],
                "coverage_percentage": report.test_coverage,
            },
            "summary": {
                "total_specs": report.total_specifications,
                "implemented_specs": report.implemented_specifications,
                "total_impls": report.total_implementations,
                "tested_impls": report.tested_implementations,
                "total_tests": report.total_tests,
                "passing_tests": report.passing_tests,
            }
        }
    
    def generate_html_report(self, output_path: Path) -> None:
        """Generate an HTML report with interactive visualizations."""
        report = self.analyzer.generate_coverage_report()
        metrics = self.analyzer.get_traceability_metrics()
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>VIBEZEN Traceability Report</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }}
        .metric-label {{
            color: #666;
            margin-top: 5px;
        }}
        .issue-list {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        }}
        .issue-item {{
            margin: 5px 0;
            padding: 5px;
        }}
        .high-priority {{
            color: #d32f2f;
            font-weight: bold;
        }}
        .mermaid {{
            text-align: center;
            margin: 20px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>VIBEZEN Traceability Report</h1>
        
        <h2>Coverage Metrics</h2>
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{report.specification_coverage:.1f}%</div>
                <div class="metric-label">Specification Coverage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report.test_coverage:.1f}%</div>
                <div class="metric-label">Test Coverage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report.verification_coverage:.1f}%</div>
                <div class="metric-label">Verification Coverage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics['test_metrics']['pass_rate']:.1f}%</div>
                <div class="metric-label">Test Pass Rate</div>
            </div>
        </div>
        
        <h2>Issues Summary</h2>
        {self._generate_issues_html(report)}
        
        <h2>Traceability Relationships</h2>
        <div class="mermaid">
            {self.generate_mermaid_diagram()}
        </div>
        
        <h2>Coverage Heatmap</h2>
        <div id="heatmap"></div>
        
        <h2>Detailed Metrics</h2>
        {self._generate_metrics_table_html(metrics)}
        
    </div>
    
    <script>
        mermaid.initialize({{ startOnLoad: true }});
        
        // Generate heatmap
        var heatmapData = {json.dumps(self.generate_coverage_heatmap())};
        
        var specImplData = [{{
            z: heatmapData.spec_impl_coverage.matrix,
            x: heatmapData.spec_impl_coverage.col_labels,
            y: heatmapData.spec_impl_coverage.row_labels,
            type: 'heatmap',
            colorscale: 'Viridis',
            showscale: false
        }}];
        
        var layout = {{
            title: 'Specification-Implementation Coverage',
            xaxis: {{title: 'Implementations'}},
            yaxis: {{title: 'Specifications'}}
        }};
        
        Plotly.newPlot('heatmap', specImplData, layout);
    </script>
</body>
</html>
"""
        
        output_path.write_text(html_content, encoding='utf-8')
    
    def generate_plantuml_diagram(self) -> str:
        """Generate a PlantUML diagram of the traceability matrix."""
        lines = [
            "@startuml",
            "!theme plain",
            "skinparam componentStyle rectangle",
            "",
            "package \"Specifications\" {",
        ]
        
        # Add specifications
        for spec_id, spec in self.matrix.specifications.items():
            color = self._get_plantuml_color(spec.status)
            lines.append(f'  component "{spec.requirement_id}" as S{spec_id} {color}')
        
        lines.extend(["}", "", "package \"Implementations\" {"])
        
        # Add implementations
        for impl_id, impl in self.matrix.implementations.items():
            color = self._get_plantuml_color(impl.status)
            lines.append(f'  component "{impl.name}" as I{impl_id} {color}')
        
        lines.extend(["}", "", "package \"Tests\" {"])
        
        # Add tests
        for test_id, test in self.matrix.tests.items():
            color = self._get_plantuml_color(test.status)
            lines.append(f'  component "{test.name}" as T{test_id} {color}')
        
        lines.extend(["}", ""])
        
        # Add relationships
        for link in self.matrix.links.values():
            source_prefix = self._get_node_prefix(link.source_id)
            target_prefix = self._get_node_prefix(link.target_id)
            
            if source_prefix and target_prefix:
                arrow = self._get_plantuml_arrow(link.link_type)
                lines.append(f'{source_prefix}{link.source_id} {arrow} {target_prefix}{link.target_id} : {link.link_type.value}')
        
        lines.append("@enduml")
        return "\n".join(lines)
    
    def export_to_json(self, output_path: Path) -> None:
        """Export traceability data to JSON format."""
        data = {
            "specifications": {
                str(sid): {
                    "id": str(sid),
                    "requirement_id": spec.requirement_id,
                    "name": spec.name,
                    "description": spec.description,
                    "priority": spec.priority,
                    "status": spec.status.value,
                    "tags": list(spec.tags),
                }
                for sid, spec in self.matrix.specifications.items()
            },
            "implementations": {
                str(iid): {
                    "id": str(iid),
                    "name": impl.name,
                    "file_path": impl.file_path,
                    "location": impl.get_location(),
                    "complexity_score": impl.complexity_score,
                    "status": impl.status.value,
                    "tags": list(impl.tags),
                }
                for iid, impl in self.matrix.implementations.items()
            },
            "tests": {
                str(tid): {
                    "id": str(tid),
                    "name": test.name,
                    "test_type": test.test_type,
                    "test_file": test.test_file,
                    "last_result": test.last_result,
                    "status": test.status.value,
                    "tags": list(test.tags),
                }
                for tid, test in self.matrix.tests.items()
            },
            "links": [
                {
                    "source_id": str(link.source_id),
                    "target_id": str(link.target_id),
                    "link_type": link.link_type.value,
                    "confidence": link.confidence,
                    "evidence": link.evidence,
                }
                for link in self.matrix.links.values()
            ],
            "metrics": self.analyzer.get_traceability_metrics(),
        }
        
        output_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    def _get_node_prefix(self, node_id: UUID) -> Optional[str]:
        """Get the node prefix based on its type."""
        if node_id in self.matrix.specifications:
            return "S"
        elif node_id in self.matrix.implementations:
            return "I"
        elif node_id in self.matrix.tests:
            return "T"
        return None
    
    def _get_node_style(self, status: TraceabilityStatus, node_type: str) -> str:
        """Get Mermaid node style based on status."""
        if status == TraceabilityStatus.VERIFIED:
            return ":::verified"
        elif status == TraceabilityStatus.FAILED:
            return ":::failed"
        elif status == TraceabilityStatus.NOT_STARTED:
            return ":::notstarted"
        return f":::{node_type}"
    
    def _get_arrow_style(self, link_type: TraceLinkType) -> str:
        """Get Mermaid arrow style based on link type."""
        styles = {
            TraceLinkType.IMPLEMENTS: "-->",
            TraceLinkType.TESTS: "-.->",
            TraceLinkType.VERIFIES: "==>",
            TraceLinkType.DERIVED_FROM: "-->>",
            TraceLinkType.DEPENDS_ON: "-.->",
            TraceLinkType.CONFLICTS_WITH: "x--x",
            TraceLinkType.RELATED_TO: "---",
        }
        return styles.get(link_type, "---")
    
    def _get_plantuml_color(self, status: TraceabilityStatus) -> str:
        """Get PlantUML color based on status."""
        colors = {
            TraceabilityStatus.VERIFIED: "#C8E6C9",
            TraceabilityStatus.TESTED: "#A5D6A7", 
            TraceabilityStatus.IMPLEMENTED: "#B39DDB",
            TraceabilityStatus.IN_PROGRESS: "#FFE082",
            TraceabilityStatus.FAILED: "#EF9A9A",
            TraceabilityStatus.NOT_STARTED: "#E0E0E0",
            TraceabilityStatus.OBSOLETE: "#BCAAA4",
        }
        color = colors.get(status, "#E0E0E0")
        return f"<<color:{color}>>"
    
    def _get_plantuml_arrow(self, link_type: TraceLinkType) -> str:
        """Get PlantUML arrow style based on link type."""
        arrows = {
            TraceLinkType.IMPLEMENTS: "-->",
            TraceLinkType.TESTS: "..>",
            TraceLinkType.VERIFIES: "==>",
            TraceLinkType.DERIVED_FROM: "-->>",
            TraceLinkType.DEPENDS_ON: "..>",
            TraceLinkType.CONFLICTS_WITH: "<->",
            TraceLinkType.RELATED_TO: "--",
        }
        return arrows.get(link_type, "--")
    
    def _generate_issues_html(self, report: CoverageReport) -> str:
        """Generate HTML for issues section."""
        html = []
        
        if report.high_priority_unimplemented:
            html.append('<div class="issue-list">')
            html.append('<h3 class="high-priority">High Priority Unimplemented Specifications</h3>')
            for spec in report.high_priority_unimplemented:
                html.append(f'<div class="issue-item">• {spec.requirement_id}: {spec.name}</div>')
            html.append('</div>')
        
        if report.complex_untested:
            html.append('<div class="issue-list">')
            html.append('<h3>Complex Untested Implementations</h3>')
            for impl in report.complex_untested:
                html.append(f'<div class="issue-item">• {impl.name} (complexity: {impl.complexity_score:.1f})</div>')
            html.append('</div>')
        
        if report.failing_tests_list:
            html.append('<div class="issue-list">')
            html.append('<h3>Failing Tests</h3>')
            for test in report.failing_tests_list:
                html.append(f'<div class="issue-item">• {test.name} ({test.test_type})</div>')
            html.append('</div>')
        
        if report.orphan_tests:
            html.append('<div class="issue-list">')
            html.append('<h3>Orphan Tests</h3>')
            for test in report.orphan_tests:
                html.append(f'<div class="issue-item">• {test.name}</div>')
            html.append('</div>')
        
        return '\n'.join(html)
    
    def _generate_metrics_table_html(self, metrics: Dict[str, Any]) -> str:
        """Generate HTML table for detailed metrics."""
        html = ['<table>']
        html.append('<tr><th>Category</th><th>Metric</th><th>Value</th></tr>')
        
        for category, values in metrics.items():
            if isinstance(values, dict):
                for metric, value in values.items():
                    if isinstance(value, (int, float)):
                        html.append(f'<tr><td>{category}</td><td>{metric}</td><td>{value:.2f}</td></tr>')
                    else:
                        html.append(f'<tr><td>{category}</td><td>{metric}</td><td>{value}</td></tr>')
        
        html.append('</table>')
        return '\n'.join(html)