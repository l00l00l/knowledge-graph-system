# app/services/inference_engine.py

from typing import Dict, Any, List, Optional, Union, Tuple
import json
from fastapi import HTTPException

from app.db.neo4j_enhanced import Neo4jEnhanced
from app.core.logger import logger

class Rule:
    """推理规则定义"""
    
    def __init__(self, name: str, pattern: str, inference: str, confidence: float = 1.0):
        self.name = name
        self.pattern = pattern  # Cypher模式匹配
        self.inference = inference  # 推理结果
        self.confidence = confidence  # 规则置信度
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "name": self.name,
            "pattern": self.pattern,
            "inference": self.inference,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """从字典创建规则"""
        return cls(
            name=data.get("name", ""),
            pattern=data.get("pattern", ""),
            inference=data.get("inference", ""),
            confidence=data.get("confidence", 1.0)
        )


class InferenceEngine:
    """推理引擎，基于规则执行知识推理"""
    
    def __init__(self, db: Neo4jEnhanced):
        self.db = db
        self.rules = []  # 规则集
    
    async def load_rules(self, rules_file: str = None) -> None:
        """从文件加载规则"""
        if rules_file:
            try:
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                    
                self.rules = [Rule.from_dict(rule) for rule in rules_data]
                logger.info(f"Loaded {len(self.rules)} rules from {rules_file}")
            except Exception as e:
                logger.error(f"Failed to load rules from {rules_file}: {e}")
                # 加载默认规则
                self._load_default_rules()
        else:
            # 加载默认规则
            self._load_default_rules()
    
    def _load_default_rules(self) -> None:
        """加载默认推理规则"""
        self.rules = [
            # 传递性规则：如果A是B的一种，B是C的一种，则A是C的一种
            Rule(
                name="transitive_is_a",
                pattern="MATCH (a)-[:IS_A]->(b)-[:IS_A]->(c) WHERE NOT (a)-[:IS_A]->(c)",
                inference="CREATE (a)-[:IS_A {inferred: true, rule: 'transitive_is_a'}]->(c)"
            ),
            
            # 部分-整体规则：如果A是B的一部分，B是C的一部分，则A是C的一部分
            Rule(
                name="transitive_part_of",
                pattern="MATCH (a)-[:PART_OF]->(b)-[:PART_OF]->(c) WHERE NOT (a)-[:PART_OF]->(c)",
                inference="CREATE (a)-[:PART_OF {inferred: true, rule: 'transitive_part_of'}]->(c)"
            ),
            
            # 属性继承规则：如果A是B的一种，B有属性P，则A有属性P
            Rule(
                name="property_inheritance",
                pattern="""
                MATCH (a)-[:IS_A]->(b)
                MATCH (b)-[:HAS_PROPERTY]->(p)
                WHERE NOT EXISTS {
                    MATCH (a)-[:HAS_PROPERTY]->(p)
                }
                """,
                inference="CREATE (a)-[:HAS_PROPERTY {inferred: true, rule: 'property_inheritance'}]->(p)"
            ),
            
            # 关系转移规则：如果A与B有关系R，B与C有关系R，且R是可传递的，则A与C有关系R
            Rule(
                name="relationship_transfer",
                pattern="""
                MATCH (a)-[r1:RELATED_TO]->(b)-[r2:RELATED_TO]->(c) 
                WHERE r1.type = r2.type AND r1.transitive = true
                AND NOT EXISTS {
                    MATCH (a)-[r:RELATED_TO]->(c) WHERE r.type = r1.type
                }
                """,
                inference="""
                CREATE (a)-[:RELATED_TO {
                    type: r1.type, 
                    inferred: true, 
                    rule: 'relationship_transfer'
                }]->(c)
                """
            )
        ]
        
        logger.info(f"Loaded {len(self.rules)} default rules")
    
    async def add_rule(self, rule: Rule) -> None:
        """添加新规则"""
        self.rules.append(rule)
    
    async def remove_rule(self, rule_name: str) -> bool:
        """删除规则"""
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.name != rule_name]
        return len(self.rules) < initial_count
    
    async def apply_rule(self, rule: Rule) -> Dict[str, Any]:
        """应用单个规则进行推理"""
        try:
            # 构建完整查询
            full_query = f"{rule.pattern}\n{rule.inference}\nRETURN count(*) as inferences"
            
            # 执行推理
            result = await self.db.execute_write_query(full_query)
            
            # 处理结果
            if result and result[0]:
                inferences_count = result[0]
                return {
                    "rule_name": rule.name,
                    "inferences_created": inferences_count,
                    "status": "success"
                }
            
            return {
                "rule_name": rule.name,
                "inferences_created": 0,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Failed to apply rule {rule.name}: {e}")
            return {
                "rule_name": rule.name,
                "status": "error",
                "error": str(e)
            }
    
    async def apply_all_rules(self) -> Dict[str, Any]:
        """应用所有规则进行推理"""
        results = []
        total_inferences = 0
        
        for rule in self.rules:
            result = await self.apply_rule(rule)
            results.append(result)
            
            if result["status"] == "success":
                total_inferences += result.get("inferences_created", 0)
        
        return {
            "total_rules_applied": len(self.rules),
            "total_inferences_created": total_inferences,
            "rule_results": results
        }
    
    async def apply_rules_to_query(self, cypher_query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """在查询执行前应用推理规则增强结果"""
        # 首先执行推理
        inference_result = await self.apply_all_rules()
        
        # 执行原始查询
        query_result = await self.db.execute_read_query(cypher_query, params)
        
        return {
            "inference_applied": inference_result["total_inferences_created"] > 0,
            "inference_count": inference_result["total_inferences_created"],
            "query_result": query_result
        }