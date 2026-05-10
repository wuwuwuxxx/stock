#!/usr/bin/env python3
"""
企业微信 Webhook 消息推送 Demo

使用说明:
1. 直接在命令行运行: python webhook_demo.py
2. 作为模块导入使用: from webhook_demo import send_text, send_markdown, send_image

支持的消息类型:
- 文本消息 (text)
- Markdown 消息 (markdown)
- 图文消息 (news)
- 图片消息 (image) - 需要 base64 编码
- 文件消息 (file) - 需要先上传文件
"""

import requests
import json
import base64
import hashlib
from typing import Optional, List, Dict

# ==================== 配置区域 ====================

# 企业微信 Webhook URL（从用户提供的）
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=bb5d55cf-6294-4a21-b2b4-72eda7686d94"

# ==================== 基础发送函数 ====================

def _send_message(data: Dict) -> Dict:
    """
    基础发送函数
    
    Args:
        data: 消息体字典
        
    Returns:
        API 返回的 JSON 数据
    """
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            headers=headers,
            data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("errcode") == 0:
            print(f"✅ 消息发送成功")
        else:
            print(f"❌ 发送失败: {result.get('errmsg')}")
            
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
        return {"errcode": -1, "errmsg": str(e)}


# ==================== 文本消息 ====================

def send_text(
    content: str,
    mentioned_list: Optional[List[str]] = None,
    mentioned_mobile_list: Optional[List[str]] = None
) -> Dict:
    """
    发送文本消息
    
    Args:
        content: 消息内容，最长不超过2048个字节
        mentioned_list: @用户列表，如 ["wangqing", "@all"] 表示 @所有人
        mentioned_mobile_list: @手机号列表，如 ["13800001111", "@all"]
        
    Returns:
        API 返回结果
        
    Example:
        >>> send_text("Hello World")
        >>> send_text("@张三 请查看", mentioned_list=["zhangsan"])
        >>> send_text("@所有人 开会啦", mentioned_list=["@all"])
    """
    data = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    
    if mentioned_list:
        data["text"]["mentioned_list"] = mentioned_list
    if mentioned_mobile_list:
        data["text"]["mentioned_mobile_list"] = mentioned_mobile_list
        
    return _send_message(data)


# ==================== Markdown 消息 ====================

def send_markdown(content: str) -> Dict:
    """
    发送 Markdown 消息
    
    Args:
        content: Markdown 格式的消息内容
        
    Returns:
        API 返回结果
        
    Example:
        >>> send_markdown("## 标题\\n**加粗文字**\\n- 列表项1\\n- 列表项2")
        >>> send_markdown("<font color='info'>蓝色文字</font>")
        >>> send_markdown("<font color='warning'>橙色文字</font>")
        >>> send_markdown("<font color='comment'>灰色文字</font>")
    """
    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }
    return _send_message(data)


# ==================== 图文消息 ====================

def send_news(
    title: str,
    description: str,
    url: str,
    picurl: Optional[str] = None
) -> Dict:
    """
    发送图文消息
    
    Args:
        title: 标题，不超过128个字节
        description: 描述，不超过512个字节
        url: 点击后跳转的链接
        picurl: 图片 URL，留空则不显示图片
        
    Returns:
        API 返回结果
        
    Example:
        >>> send_news(
        ...     title="今日股票推荐",
        ...     description="发现一只潜力股，点击查看详情...",
        ...     url="https://example.com/stock/000001",
        ...     picurl="https://example.com/cover.jpg"
        ... )
    """
    article = {
        "title": title,
        "description": description,
        "url": url
    }
    
    if picurl:
        article["picurl"] = picurl
        
    data = {
        "msgtype": "news",
        "news": {
            "articles": [article]
        }
    }
    return _send_message(data)


# ==================== 图片消息 ====================

def send_image(image_path: str) -> Dict:
    """
    发送图片消息
    
    Args:
        image_path: 本地图片路径
        
    Returns:
        API 返回结果
        
    Example:
        >>> send_image("/path/to/chart.png")
    """
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
            
        # 计算 base64
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        # 计算 md5
        md5 = hashlib.md5(image_data).hexdigest()
        
        data = {
            "msgtype": "image",
            "image": {
                "base64": base64_data,
                "md5": md5
            }
        }
        return _send_message(data)
        
    except FileNotFoundError:
        print(f"❌ 文件未找到: {image_path}")
        return {"errcode": -1, "errmsg": f"File not found: {image_path}"}
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return {"errcode": -1, "errmsg": str(e)}


# ==================== 文件消息 ====================

def upload_file(file_path: str) -> Optional[str]:
    """
    上传文件到企业微信，获取 media_id
    
    Args:
        file_path: 本地文件路径
        
    Returns:
        media_id 或 None
    """
    try:
        upload_url = WEBHOOK_URL.replace("send", "upload_media") + "&type=file"
        
        with open(file_path, "rb") as f:
            filename = file_path.split("/")[-1].split("\\")[-1]
            files = {"media": (filename, f, "application/octet-stream")}
            response = requests.post(upload_url, files=files, timeout=30)
            
        result = response.json()
        if result.get("errcode") == 0:
            print(f"✅ 文件上传成功: {filename}")
            return result.get("media_id")
        else:
            print(f"❌ 上传失败: {result.get('errmsg')}")
            return None
            
    except FileNotFoundError:
        print(f"❌ 文件未找到: {file_path}")
        return None
    except Exception as e:
        print(f"❌ 上传异常: {e}")
        return None


def send_file(media_id: str) -> Dict:
    """
    发送文件消息（需要先上传文件获取 media_id）
    
    Args:
        media_id: 文件上传后返回的 media_id
        
    Returns:
        API 返回结果
        
    Example:
        >>> media_id = upload_file("/path/to/report.pdf")
        >>> if media_id:
        >>>     send_file(media_id)
    """
    data = {
        "msgtype": "file",
        "file": {
            "media_id": media_id
        }
    }
    return _send_message(data)


# ==================== 快捷模板消息 ====================

def send_stock_alert(
    stock_code: str,
    company_name: str,
    price: float,
    change_percent: float,
    reason: str = ""
) -> Dict:
    """
    发送股票推荐消息（使用 Markdown 格式）
    
    Args:
        stock_code: 股票代码
        company_name: 公司名称
        price: 当前价格
        change_percent: 涨跌幅
        reason: 推荐理由
        
    Returns:
        API 返回结果
    """
    # 根据涨跌显示不同颜色
    color = "warning" if change_percent > 0 else "info"
    sign = "+" if change_percent > 0 else ""
    
    content = f"""## 📈 股票推荐

**{company_name}** ({stock_code})

**当前价格:** <font color='{color}'>{price:.2f}</font>
**涨跌幅:** <font color='{color}'>{sign}{change_percent:.2f}%</font>

**推荐理由:**
{reason or '技术面突破，值得关注'}

> 💡 回复股票代码查看详细分析
"""
    return send_markdown(content)


def send_daily_report(
    date: str,
    market_summary: str,
    selected_stocks: List[Dict]
) -> Dict:
    """
    发送每日股票筛选报告
    
    Args:
        date: 日期
        market_summary: 市场概况
        selected_stocks: 筛选出的股票列表，每项为 dict 包含 code, name, price, change
        
    Returns:
        API 返回结果
    """
    stock_list = "\n".join([
        f"- **{s['name']}** ({s['code']}): {s['price']:.2f} ({s['change']:+.2f}%)"
        for s in selected_stocks[:10]  # 最多显示10只
    ])
    
    content = f"""## 📊 每日股票筛选报告 ({date})

### 市场概况
{market_summary}

### 今日精选 ({len(selected_stocks)} 只)
{stock_list}

---
💡 回复股票代码获取 AI 深度分析
"""
    return send_markdown(content)


# ==================== 主程序 ====================

def main():
    """
    演示所有消息类型的发送
    """
    print("=" * 50)
    print("企业微信 Webhook 消息推送 Demo")
    print("=" * 50)
    
    # 1. 发送普通文本消息
    print("\n[1/5] 发送文本消息...")
    send_text(
        content="Hello World! 这是一条来自 Python 的测试消息 🎉",
        mentioned_list=["@all"]  # @所有人，可以改为具体用户名如 ["zhangsan"]
    )
    
    # 2. 发送 Markdown 消息
    print("\n[2/5] 发送 Markdown 消息...")
    send_markdown("""## Markdown 测试消息

这是 **加粗** 文字，这是 *斜体* 文字

### 支持的颜色标签
- <font color='info'>蓝色 info - 常用于提示</font>
- <font color='warning'>橙色 warning - 常用于警告</font>
- <font color='comment'>灰色 comment - 常用于注释</font>

### 列表示例
1. 第一步
2. 第二步
3. 第三步

> 这是一段引用文字
""")
    
    # 3. 发送股票推荐消息
    print("\n[3/5] 发送股票推荐消息...")
    send_stock_alert(
        stock_code="000001",
        company_name="平安银行",
        price=12.50,
        change_percent=3.25,
        reason="1. 突破前期高点\\n2. 成交量放大\\n3. 主力资金流入"
    )
    
    # 4. 发送图文消息
    print("\n[4/5] 发送图文消息...")
    send_news(
        title="🚀 发现潜力股：宁德时代",
        description="新能源汽车龙头，Q3业绩超预期，机构密集调研，技术面呈现多头排列...",
        url="https://quote.eastmoney.com/concept/sz300750.html",
        picurl="https://pic.rmb.bdstatic.com/bjh/news/5f58140e3d20001ca103f0c7c8b24a51.jpeg"
    )
    
    # 5. 发送每日报告示例
    print("\n[5/5] 发送每日筛选报告...")
    send_daily_report(
        date="2026-03-22",
        market_summary="今日大盘震荡上行，沪指收涨 0.8%，成交量较前日放大 15%。",
        selected_stocks=[
            {"code": "000001", "name": "平安银行", "price": 12.50, "change": 3.25},
            {"code": "300750", "name": "宁德时代", "price": 185.20, "change": 2.18},
            {"code": "600519", "name": "贵州茅台", "price": 1680.00, "change": 1.05},
            {"code": "000858", "name": "五粮液", "price": 145.30, "change": -0.85},
            {"code": "002594", "name": "比亚迪", "price": 268.50, "change": 4.12},
        ]
    )
    
    print("\n" + "=" * 50)
    print("所有消息发送完成！请查看企业微信群消息。")
    print("=" * 50)
    
    print("""
使用建议:
1. 直接运行此文件可发送测试消息
2. 导入模块使用特定功能:
   
   from webhook_demo import send_text, send_markdown, send_stock_alert
   
   send_text("自定义消息内容")
   send_markdown("## 自定义 Markdown")
   send_stock_alert("000001", "平安银行", 12.5, 3.25)
    
3. 修改代码中的 WEBHOOK_URL 可切换到其他群机器人
    """)


if __name__ == "__main__":
    main()
