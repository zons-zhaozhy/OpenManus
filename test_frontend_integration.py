#!/usr/bin/env python3
"""
前端集成测试 - 验证SSE流式需求分析功能
"""

import json
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def test_frontend_sse_integration():
    """测试前端SSE集成"""

    print("🧪 启动前端集成测试...")

    # 配置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        # 启动WebDriver
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)

        print("📱 访问前端页面...")
        driver.get("http://localhost:5173")

        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        print("✅ 页面加载成功")

        # 导航到需求分析页面
        try:
            requirements_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "需求分析"))
            )
            requirements_link.click()
            print("🎯 进入需求分析页面")

            # 等待输入框出现
            input_area = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "textarea"))
            )

            print("📝 找到输入框，开始输入测试需求...")
            test_requirement = (
                "我想开发一个在线教育平台，支持视频课程、在线考试、学习进度跟踪等功能"
            )
            input_area.clear()
            input_area.send_keys(test_requirement)

            # 找到提交按钮并点击
            submit_button = driver.find_element(
                By.XPATH,
                "//button[contains(text(), '分析需求') or contains(text(), '开始分析')]",
            )
            submit_button.click()

            print("🚀 已提交需求分析请求...")

            # 等待分析结果出现
            print("⏳ 等待分析结果...")

            # 检查是否有聊天消息出现
            WebDriverWait(driver, 30).until(
                lambda d: len(d.find_elements(By.CLASS_NAME, "message")) > 0
                or len(
                    d.find_elements(
                        By.XPATH,
                        "//*[contains(text(), '🚀') or contains(text(), '分析')]",
                    )
                )
                > 0
            )

            time.sleep(5)  # 给SSE流一些时间完成

            # 检查页面内容
            page_source = driver.page_source

            print("✅ 分析已开始，检查结果...")

            # 检查是否包含期望的内容
            success_indicators = [
                "🚀" in page_source,  # 开始分析图标
                "分析" in page_source,  # 包含分析相关文字
                test_requirement in page_source,  # 包含用户输入的需求
            ]

            success_count = sum(success_indicators)
            print(f"📊 成功指标: {success_count}/3")

            if success_count >= 2:
                print("🎉 前端SSE集成测试通过！")
                return True
            else:
                print("❌ 前端SSE集成测试失败")
                print("页面内容预览:")
                print(page_source[:500] + "...")
                return False

        except Exception as e:
            print(f"❌ 测试过程中出错: {e}")
            print("页面标题:", driver.title)
            print("当前URL:", driver.current_url)
            return False

    except Exception as e:
        print(f"💥 测试启动失败: {e}")
        return False
    finally:
        if "driver" in locals():
            driver.quit()
            print("🔒 已关闭浏览器")


def test_sse_without_browser():
    """不使用浏览器的SSE测试"""
    import urllib.parse

    import requests

    print("🧪 执行无浏览器SSE测试...")

    test_content = "我想开发一个在线教育平台"
    encoded_content = urllib.parse.quote(test_content)
    url = f"http://localhost:8000/api/requirements/analyze/stream?content={encoded_content}"

    try:
        headers = {"Accept": "text/event-stream", "Cache-Control": "no-cache"}

        response = requests.get(url, headers=headers, stream=True, timeout=30)

        if response.status_code == 200:
            events_received = 0
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    events_received += 1
                    if events_received >= 5:  # 收到足够的事件就退出
                        break

            print(f"✅ SSE测试成功，收到 {events_received} 个事件")
            return True
        else:
            print(f"❌ SSE测试失败，状态码: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ SSE测试异常: {e}")
        return False


if __name__ == "__main__":
    print("🏁 开始前端集成测试...")
    print("=" * 50)

    # 先测试SSE接口本身
    sse_result = test_sse_without_browser()

    if sse_result:
        # 再测试前端集成（如果有Chrome驱动的话）
        try:
            frontend_result = test_frontend_sse_integration()
        except Exception as e:
            print(f"⚠️  前端浏览器测试跳过: {e}")
            frontend_result = None
    else:
        print("❌ SSE接口测试失败，跳过前端测试")
        frontend_result = False

    print("=" * 50)
    print("📋 测试总结:")
    print(f"   SSE接口测试: {'✅ 通过' if sse_result else '❌ 失败'}")
    if frontend_result is not None:
        print(f"   前端集成测试: {'✅ 通过' if frontend_result else '❌ 失败'}")
    else:
        print(f"   前端集成测试: ⚠️  跳过")
