"""
VIBEZENコマンドラインツール - 品質検出率レポート

「動くだけコード」の検出率を表示し、
品質改善のための情報を提供します。
"""

import click
import asyncio
from pathlib import Path
from typing import Optional

from vibezen.core.guard import VIBEZENGuard
from vibezen.metrics.quality_detector import get_quality_detector
from vibezen.monitoring.metrics import get_metrics_collector


@click.group()
def quality():
    """品質検出率管理コマンド"""
    pass


@quality.command()
@click.option('--export', '-e', type=click.Path(), help='レポートをファイルに出力')
def report(export: Optional[str]):
    """現在の検出率レポートを表示"""
    detector = get_quality_detector()
    metrics = get_metrics_collector()
    
    # レポートを生成
    detection_report = detector.get_detection_report()
    metrics_report = metrics.get_user_friendly_report()
    
    # コンソールに表示
    click.echo(detection_report)
    click.echo("\n" + "=" * 40 + "\n")
    click.echo(metrics_report)
    
    # ファイルに出力
    if export:
        export_path = Path(export)
        with open(export_path, 'w', encoding='utf-8') as f:
            f.write(detection_report)
            f.write("\n\n")
            f.write(metrics_report)
        click.echo(f"\n✅ レポートを保存しました: {export_path}")


@quality.command()
@click.argument('code_file', type=click.Path(exists=True))
@click.option('--spec', '-s', type=click.Path(exists=True), help='仕様ファイル（JSON/YAML）')
def check(code_file: str, spec: Optional[str]):
    """指定されたコードファイルの品質をチェック"""
    async def _check():
        guard = VIBEZENGuard()
        
        # コードを読み込み
        with open(code_file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 仕様を読み込み（あれば）
        spec_data = {}
        if spec:
            import json
            import yaml
            
            with open(spec, 'r', encoding='utf-8') as f:
                if spec.endswith('.json'):
                    spec_data = json.load(f)
                elif spec.endswith(('.yaml', '.yml')):
                    spec_data = yaml.safe_load(f)
        
        # 品質チェックを実行
        result = await guard.validate_implementation(spec_data, code)
        
        # 結果を表示
        click.echo(f"\n📊 品質チェック結果: {code_file}")
        click.echo("=" * 60)
        
        if result["violation_count"] == 0:
            click.echo("✅ 品質問題は検出されませんでした！")
        else:
            click.echo(f"⚠️  {result['violation_count']}件の問題が検出されました:")
            
            # 重要度別に表示
            if result["critical_count"] > 0:
                click.echo(f"  🚨 致命的: {result['critical_count']}件")
            if result["high_count"] > 0:
                click.echo(f"  ❌ 高: {result['high_count']}件")
            
            # 違反の詳細
            click.echo("\n📋 検出された問題:")
            for i, violation in enumerate(result["violations"][:10], 1):
                severity_emoji = {
                    "critical": "🚨",
                    "high": "❌",
                    "medium": "🟡",
                    "low": "🟢"
                }
                emoji = severity_emoji.get(violation.severity.value, "•")
                click.echo(f"  {i}. {emoji} {violation.description}")
                click.echo(f"     → {violation.suggested_action}")
            
            if len(result["violations"]) > 10:
                click.echo(f"\n  ... 他{len(result['violations']) - 10}件")
        
        # 検出率レポートを表示
        if "quality_report" in result:
            click.echo("\n" + result["quality_report"])
        
        # 推奨事項
        if result["recommendations"]:
            click.echo("\n💡 推奨事項:")
            for rec in result["recommendations"]:
                click.echo(f"  • {rec}")
    
    asyncio.run(_check())


@quality.command()
@click.option('--pattern', '-p', help='特定のパターンのみ表示')
def patterns(pattern: Optional[str]):
    """検出可能なパターンの一覧を表示"""
    detector = get_quality_detector()
    
    click.echo("🎯 VIBEZEN品質検出パターン")
    click.echo("=" * 40)
    
    for pattern_id, p in detector.patterns.items():
        if pattern and pattern not in pattern_id:
            continue
        
        # パターン情報
        click.echo(f"\n📌 {p.name} ({pattern_id})")
        click.echo(f"   説明: {p.description}")
        click.echo(f"   重要度: {p.severity}")
        
        # 検出精度
        if p.true_positives + p.false_positives > 0:
            click.echo(f"   精度: {p.precision:.1%}")
            click.echo(f"   再現率: {p.recall:.1%}")
            click.echo(f"   F1スコア: {p.f1_score:.1%}")
        else:
            click.echo("   精度: データなし")


@quality.command()
@click.argument('pattern_id')
@click.option('--correct/--incorrect', default=True, help='検出が正しかったかどうか')
@click.option('--comment', '-c', help='コメント')
def feedback(pattern_id: str, correct: bool, comment: Optional[str]):
    """検出結果へのフィードバックを記録"""
    detector = get_quality_detector()
    
    # パターンが存在するか確認
    if pattern_id not in detector.patterns:
        click.echo(f"❌ パターン '{pattern_id}' が見つかりません")
        click.echo("利用可能なパターン:")
        for pid in detector.patterns.keys():
            click.echo(f"  • {pid}")
        return
    
    # フィードバックを記録（簡易版）
    pattern = detector.patterns[pattern_id]
    if correct:
        pattern.true_positives += 1
        click.echo(f"✅ 正しい検出として記録しました")
    else:
        pattern.false_positives += 1
        click.echo(f"❌ 誤検出として記録しました")
    
    if comment:
        click.echo(f"💬 コメント: {comment}")
    
    # 更新後の精度を表示
    click.echo(f"\n📊 {pattern.name}の更新後の精度:")
    click.echo(f"  精度: {pattern.precision:.1%}")
    click.echo(f"  再現率: {pattern.recall:.1%}")
    click.echo(f"  F1スコア: {pattern.f1_score:.1%}")


@quality.command()
@click.argument('output_file', type=click.Path())
def export(output_file: str):
    """検出メトリクスをエクスポート"""
    detector = get_quality_detector()
    
    output_path = Path(output_file)
    detector.export_metrics(output_path)
    
    click.echo(f"✅ メトリクスをエクスポートしました: {output_path}")
    
    # サマリーを表示
    rates = detector._calculate_overall_detection_rate()
    overall = rates["overall"]
    click.echo(f"\n📊 エクスポート時の全体精度:")
    click.echo(f"  精度: {overall['precision']:.1%}")
    click.echo(f"  再現率: {overall['recall']:.1%}")
    click.echo(f"  F1スコア: {overall['f1_score']:.1%}")
    click.echo(f"  総検出数: {overall['total_detections']}件")


def main():
    """メインエントリーポイント"""
    quality()


if __name__ == "__main__":
    main()