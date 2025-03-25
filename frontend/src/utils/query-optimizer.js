// utils/query-optimizer.js

export class CypherQueryOptimizer {
    // 优化查询语句
    static optimizeQuery(query) {
      let optimized = query;
      
      // 1. 添加索引提示
      optimized = this.addIndexHints(optimized);
      
      // 2. 限制结果集大小
      optimized = this.addLimitIfMissing(optimized);
      
      // 3. 重写低效模式
      optimized = this.rewriteIneffectivePatterns(optimized);
      
      return optimized;
    }
    
    // 添加索引提示
    static addIndexHints(query) {
      // 为name属性添加索引提示
      if (/WHERE\s+\w+\.name\s*=\s*/i.test(query)) {
        return query.replace(
          /MATCH\s+\((\w+):(\w+)\)/i,
          'MATCH ($1:$2) USING INDEX $1:$2(name)'
        );
      }
      
      // 为id属性添加索引提示
      if (/WHERE\s+\w+\.id\s*=\s*/i.test(query)) {
        return query.replace(
          /MATCH\s+\((\w+):(\w+)\)/i,
          'MATCH ($1:$2) USING INDEX $1:$2(id)'
        );
      }
      
      return query;
    }
    
    // 如果缺少LIMIT子句，添加默认限制
    static addLimitIfMissing(query) {
      if (!/\bLIMIT\s+\d+\b/i.test(query)) {
        // 检查是否以RETURN结尾
        if (/RETURN.+?$/i.test(query)) {
          return `${query} LIMIT 100`;
        }
      }
      
      return query;
    }
    
    // 重写低效的查询模式
    static rewriteIneffectivePatterns(query) {
      // 重写无限深度模式为有限深度
      return query.replace(
        /\([\w:]+\)-\[\w*\*\]-\([\w:]+\)/g,
        match => `${match.slice(0, -1)}*1..3)`
      );
    }
  }