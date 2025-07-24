"""
VIBEZEN設定ファイル検証システム

設定ファイルの妥当性を検証し、
非技術者にも分かりやすいエラーメッセージを提供します。
"""

import yaml
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from pydantic import BaseModel, Field, validator
import re

from vibezen.core.error_handling import ConfigurationError
from vibezen.utils.logger import get_logger

logger = get_logger(__name__)

# 設定値の定数
MAX_MONITORING_INTERVAL = 300  # 監視間隔の最大値（秒）
MIN_CONFIDENCE_THRESHOLD = 0.0
MAX_CONFIDENCE_THRESHOLD = 1.0


class ThinkingConfig(BaseModel):
    """思考設定"""
    min_steps: Dict[str, int] = Field(
        default={"spec_understanding": 5, "implementation_choice": 4},
        description="最小思考ステップ数"
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="確信度閾値"
    )
    
    @validator("min_steps")
    def validate_min_steps(cls, v):
        for key, value in v.items():
            if value < 1:
                raise ValueError(f"min_steps.{key}は1以上である必要があります")
            if value > 20:
                raise ValueError(f"min_steps.{key}は20以下である必要があります")
        return v


class DefenseConfig(BaseModel):
    """防御設定"""
    pre_validation: Dict[str, bool] = Field(
        default={"enabled": True, "use_o3_search": True},
        description="事前検証設定"
    )
    runtime_monitoring: Dict[str, bool] = Field(
        default={"enabled": True, "real_time": True},
        description="実行時監視設定"
    )


class TriggersConfig(BaseModel):
    """トリガー設定"""
    hardcode_detection: Dict[str, bool] = Field(
        default={"enabled": True},
        description="ハードコード検出"
    )
    complexity_threshold: int = Field(
        default=10,
        ge=1,
        le=50,
        description="複雑度閾値"
    )
    spec_violation_detection: Dict[str, bool] = Field(
        default={"enabled": True},
        description="仕様違反検出"
    )


class IntegrationsConfig(BaseModel):
    """統合設定"""
    mis: Dict[str, bool] = Field(
        default={"enabled": True},
        description="MIS統合"
    )
    zen_mcp: Dict[str, Any] = Field(
        default={
            "enabled": True,
            "deterministic": {"enabled": True}
        },
        description="zen-MCP統合"
    )
    
    @validator("zen_mcp")
    def validate_zen_mcp(cls, v):
        if v.get("enabled") and not v.get("deterministic", {}).get("enabled"):
            logger.warning("zen-MCPが有効ですが決定論的シードが無効です。再現性が低下する可能性があります")
        return v


class MonitoringConfig(BaseModel):
    """監視設定"""
    enabled: bool = Field(default=True, description="監視有効化")
    interval_seconds: int = Field(
        default=10,
        ge=1,
        le=MAX_MONITORING_INTERVAL,
        description="監視間隔（秒）"
    )
    alert_channels: List[str] = Field(
        default=["console"],
        description="アラート通知チャネル"
    )
    
    @validator("alert_channels")
    def validate_channels(cls, v):
        valid_channels = {"console", "file", "webhook"}
        for channel in v:
            if channel not in valid_channels:
                raise ValueError(f"無効なアラートチャネル: {channel}. 有効な値: {valid_channels}")
        return v


class QualityConfig(BaseModel):
    """品質設定"""
    auto_rollback: Dict[str, Any] = Field(
        default={
            "enabled": True,
            "threshold": 60,
            "max_attempts": 3
        },
        description="自動手戻り設定"
    )
    reporting: Dict[str, Any] = Field(
        default={
            "format": "user_friendly",
            "include_technical_details": False
        },
        description="レポート設定"
    )
    
    @validator("auto_rollback")
    def validate_auto_rollback(cls, v):
        threshold = v.get("threshold", 60)
        if not 0 <= threshold <= 100:
            raise ValueError("auto_rollback.thresholdは0-100の範囲である必要があります")
        
        max_attempts = v.get("max_attempts", 3)
        if not 1 <= max_attempts <= 10:
            raise ValueError("auto_rollback.max_attemptsは1-10の範囲である必要があります")
        
        return v


class VIBEZENConfig(BaseModel):
    """VIBEZEN設定全体"""
    thinking: ThinkingConfig = Field(default_factory=ThinkingConfig)
    defense: DefenseConfig = Field(default_factory=DefenseConfig)
    triggers: TriggersConfig = Field(default_factory=TriggersConfig)
    integrations: IntegrationsConfig = Field(default_factory=IntegrationsConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)
    
    class Config:
        extra = "allow"  # 追加フィールドを許可


class ConfigValidator:
    """設定ファイル検証器"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def _check_file_exists(self, config_path: Path):
        """ファイルの存在確認"""
        if not config_path.exists():
            raise ConfigurationError(
                "vibezen.yaml",
                f"設定ファイルが見つかりません: {config_path}"
            )
    
    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix == '.yaml' or config_path.suffix == '.yml':
                    return yaml.safe_load(f)
                elif config_path.suffix == '.json':
                    return json.load(f)
                else:
                    raise ConfigurationError(
                        "vibezen.yaml",
                        f"サポートされていないファイル形式: {config_path.suffix}"
                    )
        except Exception as e:
            raise ConfigurationError(
                "vibezen.yaml",
                f"設定ファイルの読み込みに失敗しました: {e}"
            )
    
    def _extract_vibezen_config(self, raw_config: Dict[str, Any]) -> Dict[str, Any]:
        """vibezenセクションを抽出"""
        if "vibezen" not in raw_config:
            self.warnings.append("'vibezen'キーが見つかりません。デフォルト設定を使用します")
            return {}
        return raw_config["vibezen"]
    
    def _validate_config_structure(self, raw_config: Any) -> None:
        """設定の基本構造を検証"""
        if not raw_config:
            logger.warning("設定ファイルが空です。デフォルト設定を使用します")
            return
        
        if not isinstance(raw_config, dict):
            raise ConfigurationError(
                "vibezen.yaml",
                "設定ファイルのルートは辞書形式である必要があります"
            )
    
    def _create_config_object(self, vibezen_config: Dict[str, Any]) -> VIBEZENConfig:
        """設定オブジェクトを作成"""
        try:
            return VIBEZENConfig(**vibezen_config)
        except Exception as e:
            # エラーメッセージを分かりやすく変換
            error_msg = self._convert_validation_error(str(e))
            raise ConfigurationError(
                "vibezen.yaml",
                f"設定値が不正です: {error_msg}"
            )
    
    def validate_file(self, config_path: Union[str, Path]) -> VIBEZENConfig:
        """
        設定ファイルを検証
        
        Args:
            config_path: 設定ファイルパス
            
        Returns:
            検証済み設定オブジェクト
            
        Raises:
            ConfigurationError: 検証エラー
        """
        config_path = Path(config_path)
        
        # ファイル存在確認
        self._check_file_exists(config_path)
        
        # ファイル読み込み
        raw_config = self._load_config_file(config_path)
        
        # 空ファイルチェック
        if not raw_config:
            logger.warning("設定ファイルが空です。デフォルト設定を使用します")
            return VIBEZENConfig()
        
        # 基本構造チェック
        self._validate_config_structure(raw_config)
        
        # vibezen キーの抽出
        vibezen_config = self._extract_vibezen_config(raw_config)
        
        # Pydanticで検証して設定オブジェクト作成
        config = self._create_config_object(vibezen_config)
        
        # 追加の検証
        self._validate_consistency(config)
        
        # 警告を表示
        if self.warnings:
            for warning in self.warnings:
                logger.warning(warning)
        
        return config
    
    def _convert_validation_error(self, error_msg: str) -> str:
        """Pydanticのエラーメッセージを分かりやすく変換"""
        # よくあるエラーパターンを変換
        conversions = {
            "ensure this value is greater than or equal to": "以上である必要があります",
            "ensure this value is less than or equal to": "以下である必要があります",
            "field required": "必須項目です",
            "value is not a valid": "有効な値ではありません",
            "type_error": "型が正しくありません"
        }
        
        result = error_msg
        for eng, jpn in conversions.items():
            result = result.replace(eng, jpn)
        
        return result
    
    def _validate_consistency(self, config: VIBEZENConfig):
        """設定の一貫性を検証"""
        # 自動手戻りが有効なのに閾値が高すぎる
        if (config.quality.auto_rollback["enabled"] and 
            config.quality.auto_rollback["threshold"] >= 90):
            self.warnings.append(
                "自動手戻りの閾値が90以上です。ほとんど発動しない可能性があります"
            )
        
        # 監視が無効なのにアラートチャネルが設定されている
        if (not config.monitoring.enabled and 
            len(config.monitoring.alert_channels) > 0):
            self.warnings.append(
                "監視が無効ですが、アラートチャネルが設定されています"
            )
        
        # MIS統合が無効なのにTODO/KG機能を使おうとしている
        if not config.integrations.mis["enabled"]:
            self.warnings.append(
                "MIS統合が無効です。TODO管理とKnowledge Graph機能が使用できません"
            )
    
    def _create_thinking_config(self) -> Dict[str, Any]:
        """思考エンジンのデフォルト設定を作成"""
        return {
            "min_steps": {
                "spec_understanding": 5,
                "implementation_choice": 4
            },
            "confidence_threshold": 0.7
        }
    
    def _create_defense_config(self) -> Dict[str, Any]:
        """防御システムのデフォルト設定を作成"""
        return {
            "pre_validation": {
                "enabled": True,
                "use_o3_search": True
            },
            "runtime_monitoring": {
                "enabled": True,
                "real_time": True
            }
        }
    
    def _create_triggers_config(self) -> Dict[str, Any]:
        """トリガーのデフォルト設定を作成"""
        return {
            "hardcode_detection": {
                "enabled": True
            },
            "complexity_threshold": 10,
            "spec_violation_detection": {
                "enabled": True
            }
        }
    
    def _create_integrations_config(self) -> Dict[str, Any]:
        """統合のデフォルト設定を作成"""
        return {
            "mis": {
                "enabled": True
            },
            "zen_mcp": {
                "enabled": True,
                "deterministic": {
                    "enabled": True
                }
            }
        }
    
    def _create_monitoring_config(self) -> Dict[str, Any]:
        """監視のデフォルト設定を作成"""
        return {
            "enabled": True,
            "interval_seconds": 10,
            "alert_channels": ["console"]
        }
    
    def _create_quality_config(self) -> Dict[str, Any]:
        """品質のデフォルト設定を作成"""
        return {
            "auto_rollback": {
                "enabled": True,
                "threshold": 60,
                "max_attempts": 3
            },
            "reporting": {
                "format": "user_friendly",
                "include_technical_details": False
            }
        }
    
    def _create_default_config_dict(self) -> Dict[str, Any]:
        """デフォルト設定の辞書を作成"""
        return {
            "vibezen": {
                "thinking": self._create_thinking_config(),
                "defense": self._create_defense_config(),
                "triggers": self._create_triggers_config(),
                "integrations": self._create_integrations_config(),
                "monitoring": self._create_monitoring_config(),
                "quality": self._create_quality_config()
            }
        }
    
    def _generate_yaml_template(self) -> str:
        """YAMLテンプレートを生成"""
        return """# VIBEZEN設定ファイル
# このファイルでVIBEZENの動作をカスタマイズできます

vibezen:
  # 思考エンジン設定
  thinking:
    # AIが考える最小ステップ数
    min_steps:
      spec_understanding: 5      # 仕様理解フェーズ
      implementation_choice: 4   # 実装選択フェーズ
    confidence_threshold: 0.7    # 確信度の閾値（0.0-1.0）
  
  # 防御システム設定
  defense:
    pre_validation:
      enabled: true             # 事前検証を有効化
      use_o3_search: true       # o3-searchを使用
    runtime_monitoring:
      enabled: true             # 実行時監視を有効化
      real_time: true           # リアルタイム監視
  
  # トリガー設定
  triggers:
    hardcode_detection:
      enabled: true             # ハードコード検出を有効化
    complexity_threshold: 10    # 複雑度の閾値
    spec_violation_detection:
      enabled: true             # 仕様違反検出を有効化
  
  # 外部システム統合
  integrations:
    mis:
      enabled: true             # MIS統合を有効化
    zen_mcp:
      enabled: true             # zen-MCP統合を有効化
      deterministic:
        enabled: true           # 決定論的シードを有効化（再現性）
  
  # 監視設定
  monitoring:
    enabled: true               # 監視を有効化
    interval_seconds: 10        # 監視間隔（秒）
    alert_channels:             # アラート通知先
      - console                 # コンソール出力
  
  # 品質設定
  quality:
    auto_rollback:
      enabled: true             # 自動手戻りを有効化
      threshold: 60             # 品質スコア閾値（0-100）
      max_attempts: 3           # 最大試行回数
    reporting:
      format: user_friendly     # レポート形式
      include_technical_details: false  # 技術詳細を含めるか
"""
    
    def generate_default_config(self, output_path: Union[str, Path]):
        """デフォルト設定ファイルを生成"""
        output_path = Path(output_path)
        
        # デフォルト設定の辞書を作成（将来の検証用）
        default_config = self._create_default_config_dict()
        
        # YAMLテンプレートを生成
        yaml_content = self._generate_yaml_template()
        
        # ファイルに出力
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        logger.info(f"デフォルト設定ファイルを生成しました: {output_path}")
    
    def validate_runtime_update(
        self,
        current_config: VIBEZENConfig,
        updates: Dict[str, Any]
    ) -> VIBEZENConfig:
        """
        実行時の設定更新を検証
        
        Args:
            current_config: 現在の設定
            updates: 更新内容
            
        Returns:
            更新後の設定
        """
        # 現在の設定を辞書に変換
        current_dict = current_config.dict()
        
        # 更新を適用
        updated_dict = self._deep_update(current_dict, updates)
        
        # 検証
        try:
            return VIBEZENConfig(**updated_dict)
        except Exception as e:
            error_msg = self._convert_validation_error(str(e))
            raise ConfigurationError(
                "runtime_update",
                f"設定更新が無効です: {error_msg}"
            )
    
    def _deep_update(self, base: Dict, updates: Dict) -> Dict:
        """辞書を再帰的に更新"""
        result = base.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_update(result[key], value)
            else:
                result[key] = value
        
        return result


# 便利関数
def load_config(config_path: Union[str, Path] = "vibezen.yaml") -> VIBEZENConfig:
    """設定ファイルを読み込み"""
    validator = ConfigValidator()
    return validator.validate_file(config_path)


def generate_default_config(output_path: Union[str, Path] = "vibezen.yaml"):
    """デフォルト設定ファイルを生成"""
    validator = ConfigValidator()
    validator.generate_default_config(output_path)