#!/usr/bin/env python3
"""
VIBEZEN CLI - 品質保証システムのコマンドラインインターフェース

非技術者でも使いやすい品質チェックツール
"""

import click
from vibezen.cli.quality_report import quality


@click.group()
def cli():
    """
    VIBEZEN - AI開発の品質保証システム
    
    「動くだけコード」を検出し、品質を自動的に改善します。
    """
    pass


# サブコマンドを追加
cli.add_command(quality)


@cli.command()
def version():
    """バージョン情報を表示"""
    click.echo("VIBEZEN v0.1.0")
    click.echo("AI-powered Quality Assurance System")


@cli.command()
@click.argument('code_file', type=click.Path(exists=True))
def quick(code_file: str):
    """コードファイルの簡易品質チェック"""
    import asyncio
    from vibezen.core.guard import VIBEZENGuard
    
    async def _quick_check():
        guard = VIBEZENGuard()
        
        with open(code_file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        result = await guard.validate_implementation({}, code)
        
        # シンプルな結果表示
        if result["violation_count"] == 0:
            click.echo("✅ 品質チェック: 合格")
        else:
            click.echo(f"⚠️  品質チェック: {result['violation_count']}件の問題")
            
            # 最も重要な問題を1つだけ表示
            if result["violations"]:
                v = result["violations"][0]
                click.echo(f"\n最も重要な問題: {v.description}")
                click.echo(f"対策: {v.suggested_action}")
    
    asyncio.run(_quick_check())


if __name__ == "__main__":
    cli()