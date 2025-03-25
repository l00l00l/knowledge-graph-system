# app/services/web_archiver.py

from playwright.async_api import async_playwright
import warcio
from warcio.capture_http import capture_http
from io import BytesIO
from datetime import datetime
import uuid
import aiofiles
import hashlib
from urllib.parse import urlparse

class WebArchiver:
    """网页抓取与归档服务"""
    
    def __init__(self, archives_dir: str):
        self.archives_dir = archives_dir
    
    async def capture_and_archive(self, url: str) -> dict:
        """抓取网页并创建WARC归档"""
        result = {
            "url": url,
            "timestamp": datetime.utcnow().isoformat(),
            "archive_id": str(uuid.uuid4()),
            "content_hash": "",
            "warc_path": "",
            "content": "",
            "metadata": {}
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(
                user_agent="Mozilla/5.0 Knowledge Graph System Web Archiver"
            )
            
            # 启用请求拦截，以便捕获所有HTTP交互
            page = await context.new_page()
            
            # 收集网络请求数据
            requests_data = []
            responses_data = []
            
            page.on("request", lambda request: requests_data.append({
                "url": request.url,
                "method": request.method,
                "headers": request.headers,
                "post_data": request.post_data
            }))
            
            page.on("response", lambda response: responses_data.append({
                "url": response.url,
                "status": response.status,
                "headers": response.headers,
            }))
            
            # 访问页面，等待网络空闲
            try:
                response = await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # 提取基本信息
                title = await page.title()
                html_content = await page.content()
                text_content = await page.evaluate("document.body.innerText")
                
                # 计算内容哈希
                content_hash = hashlib.sha256(html_content.encode('utf-8')).hexdigest()
                result["content_hash"] = f"sha256:{content_hash}"
                result["content"] = text_content
                
                # 提取元数据
                metadata = {
                    "title": title,
                    "final_url": page.url,  # 处理重定向
                    "domain": urlparse(page.url).netloc,
                    "status_code": response.status,
                    "content_type": response.headers.get("content-type", ""),
                    "headers": dict(response.headers),
                    "links": await page.evaluate("""() => {
                        return Array.from(document.querySelectorAll('a[href]'))
                            .map(a => a.href);
                    }"""),
                    "images": await page.evaluate("""() => {
                        return Array.from(document.querySelectorAll('img[src]'))
                            .map(img => img.src);
                    }"""),
                }
                result["metadata"] = metadata
                
                # 生成WARC文件
                domain = urlparse(url).netloc
                warc_path = f"{self.archives_dir}/{result['archive_id']}_{domain}.warc.gz"
                result["warc_path"] = warc_path
                
                # 使用warcio创建WARC记录
                with open(warc_path, 'wb') as f:
                    writer = warcio.WARCWriter(f, gzip=True)
                    
                    # 添加WARCINFO记录
                    record = writer.create_warcinfo_record(
                        filename=warc_path,
                        info={
                            'software': 'Knowledge Graph System Web Archiver',
                            'format': 'WARC File Format 1.1',
                            'datetime': result["timestamp"]
                        }
                    )
                    writer.write_record(record)
                    
                    # 添加请求记录
                    for req_data in requests_data:
                        if req_data["url"] == url:  # 只保存主请求
                            req_record = writer.create_request_record(
                                uri=req_data["url"],
                                record_id=str(uuid.uuid4()),
                                content_type="application/http; msgtype=request",
                                headers=req_data["headers"]
                            )
                            writer.write_record(req_record)
                    
                    # 添加响应记录
                    resp_record = writer.create_response_record(
                        uri=url,
                        record_id=str(uuid.uuid4()),
                        content_type="application/http; msgtype=response",
                        headers=metadata["headers"],
                        payload=BytesIO(html_content.encode("utf-8"))
                    )
                    writer.write_record(resp_record)
                
                # 截图保存
                screenshot_path = f"{self.archives_dir}/{result['archive_id']}_screenshot.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                
                return result
                
            except Exception as e:
                result["error"] = str(e)
                return result
            
            finally:
                await browser.close()