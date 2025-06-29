#!/usr/bin/env python3
"""
OpenManus前端界面快速测试
"""

import subprocess
import time
from pathlib import Path

import requests


def check_frontend_files():
    """检查前端关键文件"""
    print("🔍 === 检查前端文件 ===")

    frontend_path = Path("app/web")
    key_files = [
        "package.json",
        "src/App.tsx",
        "src/main.tsx",
        "src/pages/RequirementsPage.tsx",
        "src/pages/ArchitecturePage.tsx",
        "src/components/ThinkActReflectPanel.tsx",
    ]

    all_exist = True
    for file in key_files:
        file_path = frontend_path / file
        if file_path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            all_exist = False

    return all_exist


def test_backend_health():
    """测试后端健康状态"""
    print("\n🔗 === 测试后端状态 ===")

    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ 后端响应: HTTP {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ 后端连接失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 OpenManus前端快速检查")
    print("=" * 40)

    # 检查前端文件
    frontend_ok = check_frontend_files()

    # 检查后端状态
    backend_ok = test_backend_health()

    print(f"\n📊 === 检查结果 ===")
    print(f"前端文件: {'✅ 完整' if frontend_ok else '❌ 缺失'}")
    print(f"后端服务: {'✅ 运行' if backend_ok else '❌ 停止'}")

    if frontend_ok and backend_ok:
        print("\n🎉 系统基本组件正常！")
        print("💡 建议运行: ./start_openmanus.sh 启动完整服务")
    else:
        print("\n⚠️ 发现问题，请检查配置")


if __name__ == "__main__":
    main()
